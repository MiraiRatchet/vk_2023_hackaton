"""
Сервер по поиску ниаболее часто встречаемых слов в url запросе.
"""
from threading import Thread
from multiprocessing import Queue, Lock, Pipe, Value
import argparse
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
from json import dumps
import requests
from bs4 import BeautifulSoup
from settings import HOST, PORT


class Server:
    """
    TCP сервер, возвращающий ниаболее часто встречаемые слова в url запросах.
    """
    class UrlParserWorker(Thread):
        """
        Воркер, который возвращает топ самых встречаемых слов в документе
        из запроса по входящему url.
        """
        def __init__(self, queue, top_num, total_count):
            super().__init__()
            self.queue = queue
            self.top_num = top_num
            self.total_count = total_count

        def run(self):
            for (url, pipe_write) in iter(self.queue.get, None):
                res = 'error occured'
                try:
                    response = requests.get(url, timeout=3)
                    response.raise_for_status()

                    words_counter = Counter()
                    page_data = BeautifulSoup(response.text, 'html.parser')
                    words_counter.update(page_data.get_text().split())
                    res = dumps(
                        dict(words_counter.most_common(self.top_num)),
                        ensure_ascii=False,
                    )
                except requests.HTTPError as exc:
                    print(exc)
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    print(exc)
                finally:
                    pipe_write.send(f'{url}: {res}')
                    with self.total_count.get_lock():
                        self.total_count.value += 1
                        print(f'Proceeded {self.total_count.value}')
                    pipe_write.close()

    class ClientWorker(Thread):
        """
        Воркер для каждого нового TCP соединения.
        """
        def __init__(self, conn, queue_lock, request_queue):
            super().__init__()
            self.conn = conn
            self.queue_lock = queue_lock
            self.request_queue = request_queue

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
        self.top_num = top_num
        self.server_socket = None
        self.request_queue = Queue()

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

    def start(self):
        """
        Запускает сервер принимать входящие подключения.
        """
        self.server_socket = socket(AF_INET, SOCK_STREAM)
        self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen()

        total_count = Value('i', 0)

        queue_lock = Lock()
        for _ in range(self.workers_num):
            self.UrlParserWorker(
                self.request_queue,
                self.top_num,
                total_count,
            ).start()

        try:
            while True:
                conn, _ = self.server_socket.accept()
                conn.settimeout(10)
                self.ClientWorker(conn, queue_lock, self.request_queue).start()
        except (KeyboardInterrupt, OSError):
            pass
        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(f'Unexpected exception while running: {exc}')
        finally:
            self.stop()


def args_parse():
    """
    Парсер аргументов.
    """
    parser = argparse.ArgumentParser(
        'Client sends urls to server.'
    )
    parser.add_argument(
        '-w',
        '--workers_num',
        type=int,
        default=7,
    )
    parser.add_argument(
        '-k',
        '--top_num',
        type=int,
        default=3,
    )
    return parser


if __name__ == '__main__':
    args = args_parse().parse_args()
    server = Server(args.workers_num, args.top_num)
    server.start()"""
Сервер по поиску ниаболее часто встречаемых слов в url запросе.
"""
from threading import Thread
from multiprocessing import Queue, Lock, Pipe, Value
import argparse
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
from json import dumps
import requests
from bs4 import BeautifulSoup
from settings import HOST, PORT


class Server:
    """
    TCP сервер, возвращающий ниаболее часто встречаемые слова в url запросах.
    """
    class UrlParserWorker(Thread):
        """
        Воркер, который возвращает топ самых встречаемых слов в документе
        из запроса по входящему url.
        """
        def __init__(self, queue, top_num, total_count):
            super().__init__()
            self.queue = queue
            self.top_num = top_num
            self.total_count = total_count

        def run(self):
            for (url, pipe_write) in iter(self.queue.get, None):
                res = 'error occured'
                try:
                    response = requests.get(url, timeout=3)
                    response.raise_for_status()

                    words_counter = Counter()
                    page_data = BeautifulSoup(response.text, 'html.parser')
                    words_counter.update(page_data.get_text().split())
                    res = dumps(
                        dict(words_counter.most_common(self.top_num)),
                        ensure_ascii=False,
                    )
                except requests.HTTPError as exc:
                    print(exc)
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    print(exc)
                finally:
                    pipe_write.send(f'{url}: {res}')
                    with self.total_count.get_lock():
                        self.total_count.value += 1
                        print(f'Proceeded {self.total_count.value}')
                    pipe_write.close()

    class ClientWorker(Thread):
        """
        Воркер для каждого нового TCP соединения.
        """
        def __init__(self, conn, queue_lock, request_queue):
            super().__init__()
            self.conn = conn
            self.queue_lock = queue_lock
            self.request_queue = request_queue

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
        self.top_num = top_num
        self.server_socket = None
        self.request_queue = Queue()

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

    def start(self):
        """
        Запускает сервер принимать входящие подключения.
        """
        self.server_socket = socket(AF_INET, SOCK_STREAM)
        self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen()

        total_count = Value('i', 0)

        queue_lock = Lock()
        for _ in range(self.workers_num):
            self.UrlParserWorker(
                self.request_queue,
                self.top_num,
                total_count,
            ).start()

        try:
            while True:
                conn, _ = self.server_socket.accept()
                conn.settimeout(10)
                self.ClientWorker(conn, queue_lock, self.request_queue).start()
        except (KeyboardInterrupt, OSError):
            pass
        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(f'Unexpected exception while running: {exc}')
        finally:
            self.stop()


def args_parse():
    """
    Парсер аргументов.
    """
    parser = argparse.ArgumentParser(
        'Client sends urls to server.'
    )
    parser.add_argument(
        '-w',
        '--workers_num',
        type=int,
        default=7,
    )
    parser.add_argument(
        '-k',
        '--top_num',
        type=int,
        default=3,
    )
    return parser


if __name__ == '__main__':
    args = args_parse().parse_args()
    server = Server(args.workers_num, args.top_num)
    server.start()