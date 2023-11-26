from typing import Callable, Any

import json


class request:
    __user_data: dict[str, Any] = {}

    def __init__(self, params: list[str], method: str, token: str):
        self.__params = params
        self.__method = method
        self.__token = token

    def get_argument(self, param: str) -> str:
        return self.__params[param]

    def get_method(self) -> str:
        return self.__method

    def get_user_data(self):
        # if self.token == "":
        #     return {}
        if self.__token not in type(self).__user_data:
            type(self).__user_data[self.__token] = {}
        return type(self).__user_data[self.__token]

    def set_user_data(self, user_data: Any):
        type(self).__user_data[self.__token] = user_data


class Server:
    urls_paths: dict[tuple[str, frozenset[str]],
                     dict[str, Callable[[bytes], bytes]]] = {}

    def handle_reqv(self, data_bytes: bytes) -> bytes:
        try:
            data = json.loads(data_bytes)
            path = data["url"]
            if "?" in path:
                path, _, parametrs = path.rpartition('?')
                parametrs = dict(parametr.split('=')
                                 for parametr in parametrs.split('&'))
            else:
                parametrs = {}

            method = data['method']
            token = data['token']
            reqv = request(parametrs, method, token)

        except Exception as e:
            print(e)
            return bytes(json.dumps({
                "content": "Bad Request",
                "status": 400,
            }), "utf-8")
        try:
            unique_path = (path, frozenset(parametrs))
            if (unique_path in self.urls_paths and
                    method in self.urls_paths[unique_path]):
                response_content = self.urls_paths[unique_path][method](reqv)
            else:
                response_content = self.urls_paths[(
                    path, frozenset())][method](reqv)
        except Exception as e:
            print(e)
            return bytes(json.dumps({
                "content": "Not Found",
                "status": 404,
            }), "utf-8")

        response_status = 200
        response = {
            "content": response_content,
            "status": response_status,
        }

        return bytes(json.dumps(response), "utf-8")

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

server = Server()


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


# @server.route("/self/", methods=["post"])
# def test_sdsds(reqv: request):
#     return "____POST_empty"


# @server.route("/self/", methods=["post", "get"])
# def self_test(reqv: request):
#     if reqv.get_method() == "post":
#         data = reqv.get_user_data()
#         data["username"] = reqv.get_argument("username") + "OXOXOXXOXOXOX"
#         reqv.set_user_data(data)
#         # print(reqv.get_user_data(), 123)
#         return "____POSTEDDDDD"
#     data = reqv.get_user_data()
#     # print(data)
#     return data["username"] + "____GET"

# print(server.handle_reqv(bytes(json.dumps({
#     "url": "? ? ?",
#     "method": "post",
# }), "utf-8")))  # b'{"content": "Bad Request", "status": 400}'

# print(server.handle_reqv(bytes(json.dumps({
#     "url": "/self?userpassword=HEHEHEHEEHEH",
#     "method": "get",
# }), "utf-8")))  # b'{"content": "Not Found", "status": 404}'


# print(server.handle_reqv(bytes(json.dumps({
#     "url": "/self?username=HAHAHHAHA",
#     "method": "get",
# }), "utf-8")))  # b'{"content": "AHAHHAHAH____GET", "status": 200}'

# print(server.handle_reqv(bytes(json.dumps({
#     "url": "/self?username=APAPAPAPA",
#     "method": "post",
#     "token": "123123123213",
# }), "utf-8")))  # b'{"content": "AHAHHAHAH____GET", "status": 200}'

# print(server.handle_reqv(bytes(json.dumps({
#     "url": "/self?username=asdasdasdsdasdasdadda",
#     "method": "post",
#     "token": "))))))))",
# }), "utf-8")))  # b'{"content": "AHAHHAHAH____GET", "status": 200}'

# print(server.handle_reqv(bytes(json.dumps({
#     "url": "/self",
#     "method": "get",
#     "token": "123123123213",
# }), "utf-8")))  # b'{"content": "AHAHHAHAH____GET", "status": 200}'

# print(server.handle_reqv(bytes(json.dumps({
#     "url": "/self",
#     "method": "get",
#     "token": "))))))))",
# }), "utf-8")))  # b'{"content": "AHAHHAHAH____GET", "status": 200}'
