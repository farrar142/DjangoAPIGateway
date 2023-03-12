from dataclasses import dataclass, field
import functools
import os
import json
import requests
from dotenv import load_dotenv
from typing import (
    Any,
    Callable,
    Generic,
    Literal,
    Optional,
    ParamSpec,
    TypeVar,
)

from django.http.response import HttpResponse
from rest_framework import exceptions
from rest_framework.test import APIClient
from rest_framework.test import APITestCase

from base.authentications import Token, parse_jwt


load_dotenv()


def request_wrapper(func: Callable[..., Any]):
    def helper(*args, **kwargs) -> HttpResponse:
        return func(*args, **kwargs)

    return helper


admin_token: Optional[str] = None
normal_token: Optional[str] = None


class Client(APIClient):
    admin_token: Optional[str] = None
    normal_token: Optional[str] = None

    def get_user_id(self, token: str | None):
        if not token:
            raise exceptions.ValidationError
        return parse_jwt(token).user_id

    def login(self):
        if not Client.admin_token:
            t = self.get_token("ADMIN_USER", "ADMIN_PASSWORD")
            admin_token = t
            Client.admin_token = t
        else:
            t = Client.admin_token
        self.credentials(HTTP_AUTHORIZATION=f"Bearer {t}")

    def normal_login(self):
        if not Client.normal_token:
            t = self.get_token("NORMAL_USER", "NORMAL_PASSWORD")
            self.normal_token = t
            Client.normal_token = t
        else:
            t = Client.normal_token
        # print(f"login {t}")
        self.credentials(HTTP_AUTHORIZATION=f"Bearer {t}")

    def wrong_login(self):
        self.credentials(HTTP_AUTHORIZATION="Bearer dawdawdw")

    def logout(self):
        print("log out!")
        self.credentials()

    def get_token(
        self,
        user_type: Literal["ADMIN_USER", "NORMAL_USER"],
        pw_type: Literal["ADMIN_PASSWORD", "NORMAL_PASSWORD"],
    ):
        email = os.getenv(user_type)
        password = os.getenv(pw_type)
        auth_server = os.getenv("AUTH_SERVER", "http://localhost:9001")
        resp = requests.post(
            f"{auth_server}/auth/signin/classic",
            data={"email": email, "password": password},
        )
        return resp.json().get("access")

    @request_wrapper
    def get(
        self, path, data=None, follow=False, content_type="application/json", **extra
    ):
        response = super(Client, self).get(path, data=data, **extra)
        return response

    @request_wrapper
    def post(
        self,
        path,
        data=None,
        format=None,
        content_type="application/json",
        follow=False,
        **extra,
    ):
        if content_type == "application/json":
            data = json.dumps(data)
        return super(Client, self).post(
            path, data, format, content_type, follow, **extra
        )

    @request_wrapper
    def patch(
        self,
        path,
        data=None,
        format=None,
        content_type="application/json",
        follow=False,
        **extra,
    ):
        if content_type == "application/json":
            data = json.dumps(data)
        return super(Client, self).patch(
            path,
            data,
            format,
            content_type,
            follow,
            **extra,
        )

    @request_wrapper
    def delete(
        self,
        path,
        data=None,
        format=None,
        content_type="application/json",
        follow=False,
        **extra,
    ):
        if content_type == "application/json":
            data = json.dumps(data)
        return super(Client, self).delete(
            path,
            data,
            format,
            content_type,
            follow,
            **extra,
        )


E = TypeVar("E")
B = TypeVar("B", bound=bool)
ErrorType = dict[str, exceptions.ErrorDetail]


class ErrorContainer(Generic[E, B]):
    detail: E
    is_error: B

    def __init__(self, data, is_error: B, status_code=200):
        self.is_error = is_error
        if self.is_error:
            self.detail = data.detail
            self.status_code = status_code
        else:
            self.detail = data
            self.status_code = status_code


token: Token = Token(
    **{
        "user_id": 68,
        "exp": "",
        "iat": 0,
        "jti": "",
        "token_type": "access",
        "role": [],
    }
)


class Request:
    user = token
    path = ""


class View:
    request = Request


@dataclass
class MockContext:
    request: Request = field(default_factory=Request)
    view: View = field(default_factory=View)

    def __getitem__(self, key: str, default=None):
        return getattr(self, key, default)

    def get(self, key: str, default=None):
        return self.__getitem__(key, default)


mock_context = MockContext()

P = ParamSpec("P")
R = TypeVar("R")


class TestCase(APITestCase):
    client: Client
    client_class = Client
    context = mock_context
    token = token

    def aware_error(
        self, func: Callable[P, R]
    ) -> Callable[
        P, ErrorContainer[R, Literal[False]] | ErrorContainer[ErrorType, Literal[True]]
    ]:
        @functools.wraps(func)
        def wrapper(
            *args: P.args, **kwargs: P.kwargs
        ) -> (
            ErrorContainer[R, Literal[False]] | ErrorContainer[ErrorType, Literal[True]]
        ):
            try:
                return ErrorContainer[R, Literal[False]](func(*args, **kwargs), False)
            except exceptions.APIException as e:
                return ErrorContainer[ErrorType, Literal[True]](e, True, e.status_code)

        return wrapper
