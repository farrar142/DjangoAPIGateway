import json

from django.core.handlers.wsgi import WSGIRequest
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework.test import APITestCase

from rest_framework_simplejwt.tokens import RefreshToken


class Client(APIClient):
    def login(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def wrong_login(self):
        self.credentials(HTTP_AUTHORIZATION='Bearer dawdawdw')

    def logout(self):
        self.credentials()

    def post(
        self,
        path,
        data=None,
        format=None,
        content_type='application/json',
        follow=False,
        **extra,
    ):
        if content_type == 'application/json':
            data = json.dumps(data)
        return super(Client, self).post(
            path, data, format, content_type, follow, **extra
        )

    def patch(
        self,
        path,
        data=None,
        format=None,
        content_type='application/json',
        follow=False,
        **extra,
    ) -> WSGIRequest:
        if content_type == 'application/json':
            data = json.dumps(data)
        return super(Client, self).patch(
            path,
            data,
            format,
            content_type,
            follow,
            **extra,
        )

    def delete(
        self,
        path,
        data=None,
        format=None,
        content_type='application/json',
        follow=False,
        **extra,
    ) -> WSGIRequest:
        if content_type == 'application/json':
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
    # client:Client
    client_class = Client
