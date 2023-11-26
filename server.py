from multiprocessing import Process, cpu_count, Lock, Queue
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
from threading import Thread
import asyncio


def router(request: bytes) -> bytes:
    return request


class TreadWorker(Thread):
    """
    Воркер, в своём потоке запускает маршрутизатор.
    """
    def __init__(self, conn, request):
        super().__init__()
        self.conn = conn
        self.request = request

    def run(self):
        res = b''
        try:
            res = router(self.request)  # bytes
        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(exc)
        finally:
            self.conn.send(res)
            self.conn.close()


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
                data = self.request_queue.get()
                if data is None:
                    break
                (conn, request) = data
                TreadWorker(
                    conn,
                    request,
                ).start()

        except (timeout, error):
            pass


class Server:
    """
    TCP сервер, возвращающий ниаболее часто встречаемые слова в url запросах.
    """

    def __init__(self, host = 'localhost', port=8080, workers_num: int = cpu_count()):
        if not isinstance(workers_num, int) or workers_num < 1:
            raise ValueError('workers_num be more than 0')
        self.host = host
        self.port = port
        self.workers_num = workers_num

    def stop(self):
        """
        Останавливает сервер.
        """
        if self.server_socket:
            for _ in range(self.workers_num):
                self.requests_queue.put(None)
            try:
                self.server_socket.shutdown(SHUT_RDWR)
                self.server_socket.close()
                self.server_socket.detach()
            except OSError:
                pass
            except Exception as exc:  # pylint: disable=broad-exception-caught
                print(f'Unexpected exception while stopping: {exc}')

    @staticmethod
    def __handle_client(
        conn: socket, 
        queue: Queue,
        lock
    ):
        request = b''
        while True:
            data = conn.recv(1024)
            request += data
            break

        if not request:
            conn.close()
            return

        queue.put((
            conn, request
        ))

    def start(self):
        """
        Запускает сервер принимать входящие подключения.
        """
        self.server_socket = socket(AF_INET, SOCK_STREAM)
        self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()

        self.requests_queue = Queue()
        lock = Lock()
        for _ in range(self.workers_num):
            CPUWorker(
                self.requests_queue,
            ).start()

        try:
            while True:
                conn, _ = self.server_socket.accept()

                Server.__handle_client(
                    conn, 
                    self.requests_queue,
                    lock,
                )

        except (KeyboardInterrupt, OSError):
            pass
        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(f'Unexpected exception while running: {exc}')
        finally:
            self.stop()


if __name__ == '__main__':
    server = Server(workers_num=1)
    asyncio.run(server.start())
