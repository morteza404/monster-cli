import os
import json
import warnings
import requests
from shlex import quote
from pathlib import Path
from urllib.parse import urlparse
from pygments import highlight, lexers, formatters
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning

warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

UNWANTED_HEADERS = [
    "User-Agent",
    "Accept-Encoding",
    "Accept",
    "Connection",
    "Content-Length",
]


def update_headers(headers, kv):
    new_headers = headers
    if kv:
        key, value = kv.split(":")[0].strip(), kv.split(":")[1].strip()
        new_headers.update({f"{key}": f"{value}"})

    return new_headers


def convert_to_curl(request, compressed=False, verify=True, preserve_body=False):
    parts = [("curl", None)]

    if request.method == "HEAD":
        parts += [("--head", None)]

    elif request.method != "GET":
        parts += [("-X", request.method)]

    if request.method == "PUT":
        splited_url = request.url.split("/")
        auth_index = [
            i for i, word in enumerate(splited_url) if word.startswith("AUTH")
        ][0]
        if len(splited_url) > auth_index + 2:
            file_name = "".join(splited_url[auth_index + 2 :])
            parts += [("-T", file_name)]

    for k, v in sorted(request.headers.items()):
        if k not in UNWANTED_HEADERS:
            parts += [("-H", f"{k}: {v}")]

    if request.body and preserve_body:
        body = request.body
        if isinstance(body, bytes):
            body = body.decode("utf-8")
        parts += [("-d", body)]

    if compressed:
        parts += [("--compressed", None)]

    if not verify:
        parts += [("--insecure", None)]

    parts += [(None, f"{request.url}")]

    flat_parts = []
    for k, v in parts:
        if k:
            flat_parts.append(quote(k))
        if v:
            flat_parts.append(quote(v))

    return " ".join(flat_parts)


class Response:
    def __init__(self, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    def repr(self, **kwargs):
        ans = ""
        for key, value in vars(self).items():
            if key in kwargs and kwargs[key] == False:
                continue
            elif value is not None:
                tmp = self.prettify(value)
                try:
                    soup = BeautifulSoup(tmp, "html.parser")
                    beautified_html = soup.prettify()
                    tmp = beautified_html
                except:
                    pass
                ans += tmp + "\n"

        ans = ans.replace("\n\n", "\n")
        return ans

    def prettify(self, inp):
        res = str(inp)
        jsify = res.replace("'", '"')
        try:
            data = json.loads(jsify)
            tmp = json.dumps(data, indent=4)
            colorized_json = highlight(
                tmp, lexers.JsonLexer(), formatters.TerminalFormatter()
            )
            return colorized_json
        except:
            return res


class Token:
    def __init__(self) -> None:
        self.auth_endpoint = ""
        self.url_endpoint = ""
        self.username = ""
        self.password = ""

    def get_token(self):
        pass


class TokenV3(Token):
    def __init__(self) -> None:
        self.monster_endpoint = os.getenv("OS_MONSTER_URL", "http://127.0.0.1:8080")
        self.auth_endpoint_postfix = "/v3/auth/tokens"
        self.auth_endpoint = os.getenv("OS_AUTH_URL", "http://127.0.0.1:5000")
        self.url_endpoint = ""
        self.user_domain_id = os.getenv("OS_USER_DOMAIN", "default")
        self.project_domain_id = os.getenv("OS_PROJ_DOMAIN", "default")
        self.username = os.getenv("OS_USERNAME", "tester")
        self.password = os.getenv("OS_PASSWORD", "testing")
        self.project_name = os.getenv("OS_PROJECT_NAME", None)
        self.project_id = os.getenv("OS_PROJECT_ID", None)
        if self.project_id:
            self.payload = json.dumps(
                {
                    "auth": {
                        "identity": {
                            "methods": ["password"],
                            "password": {
                                "user": {
                                    "name": f"{self.username}",
                                    "domain": {"id": f"{self.user_domain_id}"},
                                    "password": f"{self.password}",
                                }
                            },
                        },
                        "scope": {
                            "project": {
                                "id": f"{self.project_id}",
                            }
                        },
                    }
                }
            )
        elif self.project_name:
            self.payload = json.dumps(
                {
                    "auth": {
                        "identity": {
                            "methods": ["password"],
                            "password": {
                                "user": {
                                    "name": f"{self.username}",
                                    "domain": {"id": f"{self.user_domain_id}"},
                                    "password": f"{self.password}",
                                }
                            },
                        },
                        "scope": {
                            "project": {
                                "domain": {"id": f"{self.project_domain_id}"},
                                "name": f"{self.project_name}",
                            }
                        },
                    }
                }
            )
        else:
            raise Exception("No project ID or project name provided")

    def get_token(self):
        payload = self.payload
        headers = {"Content-Type": "application/json"}
        url = self.auth_endpoint + self.auth_endpoint_postfix
        req = requests.Request(method="POST", url=url, data=payload, headers=headers)

        with requests.Session() as session:
            prepared_req = session.prepare_request(req)
            response = session.send(prepared_req)

        project_id = response.json()["token"]["project"]["id"]
        storage_path = self.monster_endpoint + "/v1/AUTH_" + project_id
        self.url_endpoint = storage_path
        token = response.headers["X-Subject-Token"]
        return token, self.url_endpoint, response


class TokenV1(Token):
    def get_token(self):
        auth_endpoint = os.getenv("ST_AUTH", "http://127.0.0.1:8080/auth/v1.0")
        url_endpoint = os.getenv("ST_URL", "http://127.0.0.1:8080/v1/AUTH_test")
        username = os.getenv("ST_USER", "test:tester")
        password = os.getenv("ST_KEY", "testing")

        headers = {"X-Storage-User": username, "X-Storage-Pass": password}
        req = requests.Request(method="GET", url=auth_endpoint, headers=headers)

        with requests.Session() as session:
            prepared_req = session.prepare_request(req)
            response = session.send(prepared_req)

        token = response.headers["X-Auth-Token"]
        return token, url_endpoint, response


class AuthAPI:
    def __init__(self) -> None:
        self.path = os.path.join(Path.home(), ".monster")

    def set_new_monster_connection(self, token: Token):
        token, monster_endpoint, response = token.get_token()
        token_json = {"token": token, "monster": monster_endpoint}
        self.write_to_monster_connection_file(token_json)

        modified_curl = convert_to_curl(response.request, preserve_body=True)

        return Response(
            status_code=response.status_code,
            token=token,
            curl=modified_curl,
        )

    def write_to_monster_connection_file(self, monster_conn):
        path = self.path
        with open(path, "w") as data:
            json.dump(monster_conn, data)

    def change_project_id(self, id):
        if id.startswith("AUTH_"):
            id = id.split("_")[1]
        monster_conn = self.read_from_monster_connection_file()
        monster_url = monster_conn["monster"]
        splited_url = monster_url.split("/")
        auth_index = [
            i for i, word in enumerate(splited_url) if word.startswith("AUTH")
        ][0]
        splited_url[auth_index] = "AUTH_" + id
        new_url = "/".join(splited_url)
        monster_conn["monster"] = new_url
        self.write_to_monster_connection_file(monster_conn)
        return Response(
            status_code=200,
        )

    def read_from_monster_connection_file(self):
        path = self.path
        try:
            with open(path, "r") as data:
                jdata = json.load(data)
            return jdata
        except:
            return {"token": None, "monster": "http://127.0.0.1:8080/v1/AUTH_test"}


class MonsterAPI:
    def __init__(self) -> None:
        auth = AuthAPI()
        connection = auth.read_from_monster_connection_file()
        self.monster_endpoint = connection["monster"]
        self.token = connection["token"]
        self.headers = {"X-Auth-Token": self.token}

    # Create
    def create_container(self, container_name, new_headers):
        url = self.monster_endpoint
        headers = update_headers(self.headers, new_headers)

        req = requests.Request(
            method="PUT", url=f"{url}/{container_name}", headers=headers
        )

        with requests.Session() as session:
            prepared_req = session.prepare_request(req)
            response = session.send(prepared_req)

        modified_curl = convert_to_curl(prepared_req)

        return Response(
            status_code=response.status_code,
            content=response.content.decode(),
            curl=modified_curl,
        )

    def upload_object(self, container_name, object_name, new_headers):
        url = self.monster_endpoint
        headers = update_headers(self.headers, new_headers)

        with open(object_name, "rb") as f:
            data = f.read()

        req = requests.Request(
            method="PUT",
            url=f"{url}/{container_name}/{object_name}",
            headers=headers,
            data=data,
        )

        with requests.Session() as session:
            prepared_req = session.prepare_request(req)
            response = session.send(prepared_req)

        modified_curl = convert_to_curl(prepared_req)
        return Response(
            status_code=response.status_code,
            content=response.content.decode(),
            curl=modified_curl,
        )

    # Delete
    def delete_container(self, container_name, new_headers):
        url = self.monster_endpoint
        headers = update_headers(self.headers, new_headers)

        req = requests.Request(
            method="DELETE", url=f"{url}/{container_name}", headers=headers
        )

        with requests.Session() as session:
            prepared_req = session.prepare_request(req)
            response = session.send(prepared_req)

        modified_curl = convert_to_curl(prepared_req)
        return Response(
            status_code=response.status_code,
            content=response.content.decode(),
            curl=modified_curl,
        )

    def delete_object(self, container_name, object_name, new_headers):
        url = self.monster_endpoint
        headers = update_headers(self.headers, new_headers)

        req = requests.Request(
            method="DELETE",
            url=f"{url}/{container_name}/{object_name}",
            headers=headers,
        )

        with requests.Session() as session:
            prepared_req = session.prepare_request(req)
            response = session.send(prepared_req)

        modified_curl = convert_to_curl(prepared_req)
        return Response(
            status_code=response.status_code,
            content=response.content.decode(),
            curl=modified_curl,
        )

    # Head
    def head_account(self, new_headers):
        url = self.monster_endpoint
        headers = update_headers(self.headers, new_headers)

        req = requests.Request(method="HEAD", url=f"{url}", headers=headers)

        with requests.Session() as session:
            prepared_req = session.prepare_request(req)
            response = session.send(prepared_req)

        modified_curl = convert_to_curl(prepared_req)
        return Response(
            status_code=response.status_code,
            headers=response.headers,
            curl=modified_curl,
        )

    def head_container(self, container_name, new_headers):
        url = self.monster_endpoint
        headers = update_headers(self.headers, new_headers)

        req = requests.Request(
            method="HEAD", url=f"{url}/{container_name}", headers=headers
        )

        with requests.Session() as session:
            prepared_req = session.prepare_request(req)
            response = session.send(prepared_req)

        modified_curl = convert_to_curl(prepared_req)
        return Response(
            status_code=response.status_code,
            headers=response.headers,
            curl=modified_curl,
        )

    def head_object(self, container_name, object_name, new_headers):
        url = self.monster_endpoint
        headers = update_headers(self.headers, new_headers)

        req = requests.Request(
            method="HEAD", url=f"{url}/{container_name}/{object_name}", headers=headers
        )

        with requests.Session() as session:
            prepared_req = session.prepare_request(req)
            response = session.send(prepared_req)

        modified_curl = convert_to_curl(prepared_req)
        return Response(
            status_code=response.status_code,
            headers=response.headers,
            curl=modified_curl,
        )

    # Get
    def get_account(self, new_headers):
        url = self.monster_endpoint
        headers = update_headers(self.headers, new_headers)

        req = requests.Request(method="GET", url=f"{url}", headers=headers)

        with requests.Session() as session:
            prepared_req = session.prepare_request(req)
            response = session.send(prepared_req)

        modified_curl = convert_to_curl(prepared_req)
        return Response(
            status_code=response.status_code,
            content=response.content.decode(),
            curl=modified_curl,
        )

    def get_container(self, container_name, new_headers):
        url = self.monster_endpoint
        headers = update_headers(self.headers, new_headers)

        req = requests.Request(
            method="GET", url=f"{url}/{container_name}", headers=headers
        )

        with requests.Session() as session:
            prepared_req = session.prepare_request(req)
            response = session.send(prepared_req)

        modified_curl = convert_to_curl(prepared_req)
        return Response(
            status_code=response.status_code,
            content=response.content.decode(),
            curl=modified_curl,
        )

    def get_object(self, container_name, object_name, new_headers):
        url = self.monster_endpoint
        headers = update_headers(self.headers, new_headers)

        req = requests.Request(
            method="GET", url=f"{url}/{container_name}/{object_name}", headers=headers
        )

        with requests.Session() as session:
            prepared_req = session.prepare_request(req)
            response = session.send(prepared_req)

        modified_curl = convert_to_curl(prepared_req)
        with open(f"{object_name}", "wb") as data:
            data.write(response.content)

        try:
            return Response(
                status_code=response.status_code,
                content=response.content.decode(),
                curl=modified_curl,
            )
        except:
            return Response(
                status_code=response.status_code,
                curl=modified_curl,
            )

    # Metadata
    def post_account(self, new_headers):
        url = self.monster_endpoint
        headers = update_headers(self.headers, new_headers)

        req = requests.Request(method="POST", url=f"{url}", headers=headers)

        with requests.Session() as session:
            prepared_req = session.prepare_request(req)
            response = session.send(prepared_req)

        modified_curl = convert_to_curl(prepared_req)

        return Response(
            status_code=response.status_code,
            content=response.content.decode(),
            curl=modified_curl,
        )

    def post_container(self, container_name, new_headers):
        url = self.monster_endpoint
        headers = update_headers(self.headers, new_headers)

        req = requests.Request(
            method="POST", url=f"{url}/{container_name}", headers=headers
        )

        with requests.Session() as session:
            prepared_req = session.prepare_request(req)
            response = session.send(prepared_req)

        modified_curl = convert_to_curl(prepared_req)
        return Response(
            status_code=response.status_code,
            content=response.content.decode(),
            curl=modified_curl,
        )

    def post_object(self, container_name, object_name, new_headers):
        url = self.monster_endpoint
        headers = update_headers(self.headers, new_headers)

        req = requests.Request(
            method="POST", url=f"{url}/{container_name}/{object_name}", headers=headers
        )

        with requests.Session() as session:
            prepared_req = session.prepare_request(req)
            response = session.send(prepared_req)

        modified_curl = convert_to_curl(prepared_req)
        return Response(
            status_code=response.status_code,
            content=response.content.decode(),
            curl=modified_curl,
        )

    # Info
    def get_info(self):
        url = self.monster_endpoint

        parsed_url = urlparse(url)
        base_url = parsed_url.scheme + "://" + parsed_url.netloc
        req = requests.Request(method="GET", url=f"{base_url}/info")
        with requests.Session() as session:
            prepared_req = session.prepare_request(req)
            response = session.send(prepared_req)
        modified_curl = convert_to_curl(prepared_req)
        return Response(
            status_code=response.status_code,
            content=response.content.decode(),
            curl=modified_curl,
        )
