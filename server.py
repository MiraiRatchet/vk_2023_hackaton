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

from typing import Callable

import json




class request:
    def __init__(self, params: list[str], method: str):
        self.params = params
        self.method = method

    def get_argument(self, param: str) -> str:
        return self.params[param]

    def get_method(self) -> str:
        return self.method


class TreadWorker(Thread):
    """
    Воркер, в своём потоке запускает маршрутизатор.
    """
    def __init__(self, conn, request, server):
        super().__init__()
        self.conn = conn
        self.request = request
        self.server = server

    def run(self):
        res = b''
        try:
            res = self.server.handle_reqv(self.request)  # bytes
        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(exc)
        finally:
            self.conn.send(res)
            self.conn.close()


class CPUWorker(Process):
    """
    Воркер для каждого нового TCP соединения.
    """
    def __init__(self, global_request_queue, server):
        super().__init__()
        self.request_queue = global_request_queue
        self.server = server

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
                    self.server,
                ).start()

        except (timeout, error):
            pass

class Server:
    """
    TCP сервер, возвращающий ниаболее часто встречаемые слова в url запросах.
    """

    urls_paths: dict[tuple[str, frozenset[str]],
                     dict[str, Callable[[bytes], bytes]]] = {}

    def handle_reqv(self, data_bytes_: bytes) -> bytes:
        data_bytes = data_bytes_.decode("utf-8")
        try:
            data = {}
            paths = data_bytes.split()
            data['url'] = paths[1]
            data['method'] = paths[0]
            #data['token'] = paths[paths.index("Postman-Token:")]
            # print(data)

            path, _, parametrs = data['url'].rpartition('?')

            parametrs = dict(parametr.split('=')
                             for parametr in parametrs.split('&'))

            method = str(data['method'])
            # print(method, 123213213213213213)
            reqv = request(parametrs, method)

        except Exception as e:
            # print(e, 1)
            return bytes(json.dumps({
                "content": "Bad Request",
                "status": 400,
            }), "utf-8")
        try:
            unique_path = (path, frozenset(parametrs))
            if (unique_path in self.urls_paths and
                    method in self.urls_paths[unique_path]):
                response_content = self.urls_paths[unique_path][method](reqv)
                #print(response_content)
            else:
                response_content = self.urls_paths[(
                    path, frozenset({}))][method](reqv)
        except Exception as e:
            return bytes(json.dumps({
                "content": "Not Found",
                "status": 404,
            }), "utf-8")

        response_status = 200
        response = {
            "content": response_content,
            "status": response_status,
        }

        res = json.dumps(response).encode()

        print(res)
        return res

    def route(self, url: str, methods: list[str]):
        path = url
        if '>' in path:
            path, _, parametrs = path.rpartition('/')
            parametrs = frozenset(parametrs[1:-1].split('><'))
            if parametrs == {""}:
                parametrs = frozenset()
        else:
            path = path.removesuffix('/')
            parametrs = frozenset()

        """проверка аргументов methods"""
        """проверка <><><>"""
        """пример: (path, ?<name><abc><username>)"""
        def wrapper(func):
            """проверка на наличие нужных параметров у функции"""
            def inner(reqv: dict[str, str]):
                kwargs = {
                    parametr: reqv.get_argument(parametr)
                    for parametr in parametrs
                }

                response_html: str = func(reqv, **kwargs)

                return response_html

            unique_path = (path, frozenset(parametrs))
            for method in methods:
                if unique_path not in self.urls_paths:
                    self.urls_paths[unique_path] = {}
                self.urls_paths[unique_path][method] = inner

        return wrapper

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
        message_len = 1024
        request = b''
        while True:
            data = conn.recv(message_len)
            request += data
            
            if not data or len(data) < message_len:
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
        print(f'Server running on {self.host}:{self.port}')

        self.requests_queue = Queue()
        lock = Lock()
        for _ in range(self.workers_num):
            CPUWorker(
                self.requests_queue,
                self,
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

    from template import get_template
    @server.route(url='/req/<username><cat>', methods=["POST", "GET"])
    def test(reqv, username, cat):
        items = [{'name': "pizza", 'description': "good"}, {"name": "durt", "description": "bad"}]
        print(f'Got {username=}, {cat=}')
        return get_template('test.html', items=items)#f'rqv {username=}'

    asyncio.run(server.start())
