import json

from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test.client import Client as _Client
from django.db.models import QuerySet

from django.test import TestCase as _TestCase


from accounts.models import User


class Client(_Client):
    header = {}

    def credentials(self, **kwargs):
        self.header = {**kwargs}

    def authorize(self, user: User):
        token = user.make_token()
        self.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def expired(self, user: User):
        token = User.expired_token(user.pk)
        self.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def not_validated_token(self):
        self.credentials(HTTP_AUTHORIZATION="Bearer nonvalidatedtoken")

    def logout(self):
        self.credentials()

    def post(
        self,
        path,
        data=None,
        content_type='application/json',
        follow=False,
        **extra,
    ):
        if content_type == 'application/json':
            data = json.dumps(data)
        return super(Client, self).post(
            path, data, content_type, follow, **extra, **self.header
        )

    def put(
        self,
        path,
        data=None,
        content_type='application/json',
        follow=False,
        **extra,
    ):
        if content_type == 'application/json':
            data = json.dumps(data)
        return super(Client, self).put(
            path,
            data,
            content_type,
            follow,
            **extra, **self.header
        )

    def patch(
        self,
        path,
        data=None,
        content_type='application/json',
        follow=False,
        **extra,
    ):
        if content_type == 'application/json':
            data = json.dumps(data)
        return super(Client, self).patch(
            path,
            data,
            content_type,
            follow,
            **extra, **self.header
        )

    def delete(
        self,
        path,
        data=None,
        content_type='application/json',
        follow=False,
        **extra,
    ):
        if content_type == 'application/json':
            data = json.dumps(data)
        return super(Client, self).delete(
            path,
            data,
            content_type,
            follow,
            **extra, **self.header
        )


class TestCase(_TestCase):
    client_class = Client
    client: Client
    # user: User
    # username = "gksdjf1690"
    # password = "test"
    # email = "gksdjf1690@gmail.com"

    # def setUp(self):
    #     super().setUp()
    #     self.user = User.objects.create(
    #         username=self.username, password=make_password(self.password), email=self.email)
