from typing import Callable

from json import loads


class request:
    __arguments: dict[str, str]

    @classmethod
    def get_argument(cls, argument: str):
        return cls.__arguments[argument]

    @classmethod
    def __set_argument(cls, argument: str, value: str):
        cls.__arguments[argument] = value

    @classmethod
    def parse_data(cls, data_bytes: bytes) -> dict:
        data_json = loads(data_bytes)
        return data_json


class Server:
    urls_paths: dict[tuple(str, frozenset[str]),
                     dict[str, Callable[[bytes], bytes]]]

    def handle_reqv(self, data: bytes) -> bytes:
        request.parse_data(data)
        # data
        # urls_paths[]()
        return ...


def dec(url: str, methods: list[str]):
    path, parametrs = url.rpartition('/')

    """проверка аргументов methods"""
    """проверка <><><>"""
    """пример: (path, ?<name><abc><username>)"""
    parametrs = frozenset(parametrs[1:-1].split('><'))

    def wrapper(func):
        """проверка на наличие нужных параметров у функции"""
        def inner():
            kwargs = {
                parametr: request.get_argument(parametr)
                for parametr in parametrs
            }

            response_html: str = func(**kwargs)

            return response_html

        for method in methods:
            Server.urls_paths[(path, frozenset)][method] = inner

    return wrapper
