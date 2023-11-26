from multiprocessing import Queue, Pipe, Value, Process, cpu_count, Lock
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


def router(request: bytes) -> bytes:
    pass


class Server:
    """
    TCP сервер, возвращающий ниаболее часто встречаемые слова в url запросах.
    """

    class CPUWorker(Process):
        """
        Воркер для каждого нового TCP соединения.
        """
        def __init__(self, global_request_queue):
            super().__init__()
            self.request_queue = global_request_queue

        def run(self):
            try:
                while True:
                    for (conn, request) in iter(self.request_queue.get, None):
                        res = router(request)
                        conn.send(res)
                        conn.close()

            except (timeout, error):
                pass


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
        queue: Queue,
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
