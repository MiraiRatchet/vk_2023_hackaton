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


class Server:
    urls_paths: dict[tuple[str, frozenset[str]],
                     dict[str, Callable[[bytes], bytes]]] = {}

    def handle_reqv(self, data_bytes: bytes) -> bytes:
        try:
            data = json.loads(data_bytes)
            path, _, parametrs = data['url'].rpartition('?')

            parametrs = dict(parametr.split('=')
                             for parametr in parametrs.split('&'))

            method = data['method']
            reqv = request(parametrs, method)

            unique_path = (path, frozenset(parametrs))
            if (unique_path in self.urls_paths and
                    method in self.urls_paths[unique_path]):
                response_content = self.urls_paths[unique_path][method](reqv)
            else:
                response_content = self.urls_paths[(
                    path, frozenset({}))][method](reqv)
            response_status = 200

            response = {
                "content": response_content,
                "status": response_status,
            }

            return bytes(json.dumps(response), "utf-8")

        except Exception:
            return bytes(json.dumps({
                "content": "Bad Request",
                "status": 400,
            }), "utf-8")

    def route(self, url: str, methods: list[str]):
        path, _, parametrs = url.rpartition('/')

        """проверка аргументов methods"""
        """проверка <><><>"""
        """пример: (path, ?<name><abc><username>)"""
        parametrs = frozenset(parametrs[1:-1].split('><'))
        if parametrs == {""}:
            parametrs = frozenset()

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
                if unique_path not in Server.urls_paths:
                    self.urls_paths[unique_path] = {}
                self.urls_paths[unique_path][method] = inner

        return wrapper


# SuperServer.get({"url": "ya.ru/search?abc=1&cfd=2", "method": "post"})

# server = Server()


# @server.route("/self/<username>", methods=["post", "get"])
# def self_test(reqv, username):
#     if reqv.get_method() == "post":
#         return username[::-1] + "____POST"
#     return username[::-1] + "____GET"


# @server.route("/self/", methods=["delete"])
# def test_delete(reqv: request):
#     return reqv.get_argument("username") + "____DELETE"


# @server.route("/self/", methods=["patch"])
# def test_PATCH(reqv: request):
#     return "____PATCH"


# @server.route("/self/", methods=["patch"])
# def test_geeet(reqv: request):
#     return "____PATCH"


# print(server.handle_reqv(bytes(json.dumps({
#     "url": "/self?usernasme=petya",
#     "method": "post",
# }), "utf-8"))
# )
