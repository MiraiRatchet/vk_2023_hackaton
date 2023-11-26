from multiprocessing import Queue, Lock, Pipe, Value, Process, cpu_count
from collections import Counter
from socket import (
    socket,
    AF_INET,
    SOCK_STREAM,
    timeout,
    error,
    SOL_SOCKET,
    SO_REUSEADDR,
    SHUT_RDWR,
)
from settings import HOST, PORT
import asyncio

async def handle_client(conn, queue, lock):
    loop = asyncio.get_event_loop()

    request = b''
    while True:
        data = await loop.sock_recv(conn, 1024)
        request += data
        if not data or len(data) < 1024:
            break
        
    if not request:
        conn.close()
        return
    
    with lock:
        queue.put((
            conn, request
        ))

class Server:
    """
    TCP сервер, возвращающий ниаболее часто встречаемые слова в url запросах.
    """


    class CPUWorker(Process):
        """
        Воркер для каждого нового TCP соединения.
        """
        def __init__(self, queue_lock, global_request_queue):
            super().__init__()
            self.queue_lock = queue_lock
            self.request_queue = global_request_queue

        def run(self):
            try:
                while True:
                    recieved_data = b''
                    while True:
                        data = self.conn.recv(1024)
                        recieved_data = recieved_data + data
                        if not data or len(data) < 1024:
                            break

                    if not recieved_data:
                        raise error
                    
                    url = recieved_data.decode('utf-8')
                    pipe_client, pipe_worker = Pipe()
                    
                    with self.queue_lock:
                        self.request_queue.put((url, pipe_worker))
                    
                    res = pipe_client.recv()
                    pipe_client.close()
                    self.conn.send(res.encode('utf-8'))
            
            except (timeout, error):
                pass
            finally:
                self.conn.close()

    def __init__(self, workers_num, top_num):
        if not isinstance(workers_num, int) or not\
                isinstance(top_num, int) or workers_num < 1 or top_num < 1:
            raise ValueError('workers_num and top_num must be more than 0')
        self.workers_num = workers_num

    def stop(self):
        """
        Останавливает сервер.
        """
        if self.server_socket:
            for _ in range(self.workers_num):
                self.request_queue.put(None)
            try:
                self.server_socket.shutdown(SHUT_RDWR)
                self.server_socket.close()
                self.server_socket.detach()
            except OSError:
                pass
            except Exception as exc:  # pylint: disable=broad-exception-caught
                print(f'Unexpected exception while stopping: {exc}')

    async def start(self):
        """
        Запускает сервер принимать входящие подключения.
        """
        self.server_socket = socket(AF_INET, SOCK_STREAM)
        self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen()

        requests_queue = Queue()
        queue_lock = Lock()
        for _ in range(self.workers_num):
            self.CPUWorker(
            )

        try:
            loop = asyncio.get_event_loop()

            while True:
                conn, _ = await loop.sock_accept(self.server_socket)
                #conn.settimeout(10)
                loop.create_task(handle_client(conn, requests_queue, queue_lock))

        except (KeyboardInterrupt, OSError):
            pass
        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(f'Unexpected exception while running: {exc}')
        finally:
            self.stop()


if __name__ == '__main__':
    args = args_parse().parse_args()
    server = Server(args.workers_num, args.top_num)
    server.start()
