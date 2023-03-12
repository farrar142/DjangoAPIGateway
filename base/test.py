import json
from typing import Any, Callable, Literal

from django.http.response import HttpResponse
from django.core.handlers.wsgi import WSGIRequest
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework.test import APITestCase

from rest_framework_simplejwt.tokens import RefreshToken


def request_wrapper(func: Callable[..., Any]):
    def helper(*args, **kwargs) -> HttpResponse:
        return func(*args, **kwargs)

    return helper


class Client(APIClient):
    def login(self, token: str):
        self.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def wrong_login(self):
        self.credentials(HTTP_AUTHORIZATION="Bearer dawdawdw")

    def logout(self):
        self.credentials()

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


class TestCase(APITestCase):
    client: Client
    client_class = Client
