import requests
import time
from django.db import connection
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken
from runthe_backend.test import TestCase
from common_module.mixins import ServerRequests
from .models import Api, Upstream, Target
from common_module.authentication import parse_jwt
from common_module.caches import UseSingleCache, cache

# Create your tests here.
SCHEME = "https"


class TestApiGateway(TestCase):
    auth: Api

    def setUp(self):
        Upstream.objects.all().delete()
        Api.objects.all().delete()
        self.auth_upstream = Upstream.objects.create(
            host="new.test.palzakspot.com", scheme=SCHEME, alias="API_GATEWAY"
        )
        self.auth = Api.objects.create(
            name="auth",
            request_path="/auth",
            wrapped_path="/auth",
            upstream=self.auth_upstream,
            plugin=0,
        )
        self.auth = Api.objects.create(
            name="users",
            request_path="/users",
            wrapped_path="/users",
            upstream=self.auth_upstream,
            plugin=0,
        )

    def test_middleware(self):
        resp = self.client.get("/")
        print(resp)

    def test_auth_server_authenticate(self):
        resp = self.client.post(
            "/auth/signin/classic",
            {"email": "gksdjf1690@gmail.com", "password": "gksdjf452@"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        print("====")
        print(resp.json())
        access_token = resp.json().get("access")
        self.client.login(access_token)
        # print(f"{AccessToken(access_token)=}")
        resp = self.client.get("/users/me/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_upstream_round_robin(self):
        from django.conf import settings

        cache.clear()
        for i in range(5):
            self.auth_upstream.targets.create(
                host="www.naver.com", scheme="https", weight=50
            )
        settings.DEBUG = True
        for i in range(10):
            resp = self.client.get("/users/")

        # self.auth_upstream.targets.create(
        #     host="www.naver.com", scheme="https", weight=50
        # )
        # for i in range(15):
        #     self.client.get("/users/")

        # print(self.auth_upstream.weight_round())

    def test_cache(self):
        cache.clear()
        c = UseSingleCache(0, "test")
        c.set("object", path="/test", upstream=1)
        c.set("object", path="/test", upstream=2)
        c.set("object", path="/test", upstream=3)
        self.assertEqual(len(c.get_global_keys()), 3)
        c.purge_global_key()
        self.assertEqual(len(c.get_global_keys()), 0)
        c.set("object", path="/test", upstream=1)
        c.set("object", path="/test", upstream=2)
        c.set("object", path="/test", upstream=3)
        self.assertEqual(len(c.get_global_keys()), 3)
        c.purge(path="/test", upstream=1)
        self.assertEqual(len(c.get_global_keys()), 2)
        c.purge_by_regex(upstream="*", path="/test")
        self.assertEqual(len(c.get_global_keys()), 0)
        c.set("object", path="/auth", upstream=1)
        c.set("object", path="/test", upstream=1)
        c.set("object", path="/users", upstream=1)
        self.assertEqual(len(c.get_global_keys()), 3)
        print(c.get_global_keys())
        c.purge_by_regex(upstream=1, path="*")
        self.assertEqual(len(c.get_global_keys()), 0)
