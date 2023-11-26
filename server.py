from multiprocessing import Queue, Pipe, Value, Process, cpu_count
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
import multiprocessing

class DualLock:
    async def __init__(self):
        self.__async_lock = asyncio.Lock()
        self.__multiprocessing_lock = multiprocessing.Lock()

    async def __enter__(self):
        self.__async_lock.__enter__()
        self.__multiprocessing_lock.__enter__()

    async def __exit__(self, type, value, traceback):
        self.__async_lock.__exit__(self, type, value, traceback)
        self.__multiprocessing_lock.__exit__(self, type, value, traceback)

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

    def __init__(self, workers_num: int = cpu_count()):
        if not (isinstance(workers_num, int) and workers_num < 1):
            raise ValueError('workers_num be more than 0')
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

    @staticmethod
    async def __handle_client(
        conn: socket, 
        queue: multiprocessing.Queue, 
        lock: multiprocessing.Lock,
    ):
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

    async def start(self):
        """
        Запускает сервер принимать входящие подключения.
        """
        self.server_socket = socket(AF_INET, SOCK_STREAM)
        self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen()

        self.requests_queue = Queue()
        self.queue_lock = DualLock()
        for _ in range(self.workers_num):
            self.CPUWorker(
                self.queue_lock,
                self.request_queue,
            )

        try:
            loop = asyncio.get_event_loop()

            while True:
                conn, _ = await loop.sock_accept(self.server_socket)
                loop.create_task(
                    Server.__handle_client(
                        conn, 
                        self.requests_queue, 
                        self.queue_lock
                    )
                )

        except (KeyboardInterrupt, OSError):
            pass
        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(f'Unexpected exception while running: {exc}')
        finally:
            self.stop()


if __name__ == '__main__':
    server = Server()
    asyncio.run(server.start())
