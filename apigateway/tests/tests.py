import os
from uuid import uuid4
from dotenv import load_dotenv

from django.conf import settings
from rest_framework import status
from base.test import TestCase
from apigateway.models import Api, Upstream, Target, User
from base.caches import UseSingleCache, cache

load_dotenv()
# Create your tests here.
SCHEME = "https"

AUTH_SERVER = os.getenv("AUTH_SERVER", "http://localhost:9001")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL","")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD","")


class TestApiGateway(TestCase):
    auth: Api

    def setUp(self):
        Upstream.objects.all().delete()
        Api.objects.all().delete()
        self.auth_upstream = Upstream.objects.create(
            host=AUTH_SERVER, scheme=SCHEME, alias="API_GATEWAY"
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
        self.auth = Api.objects.create(
            name="admin_users",
            request_path="/admin/users",
            wrapped_path="/admin/users",
            upstream=self.auth_upstream,
            plugin=3,
        )

    def test_middleware(self):
        resp = self.client.get("/")
        print(resp)

    def test_auth_server_authenticate(self):
        print("start=========================")
        cache.clear()
        resp = self.client.post(
            "/auth/signin/classic",
            {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        print(resp.json())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        print("====")
        print(resp.json())
        access_token = resp.json().get("access")
        self.assertEqual(User.objects.count(), 0)
        self.client.login(access_token)
        # print(f"{AccessToken(access_token)=}")
        resp = self.client.get("/admin/users/me/")
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_upstream_round_robin(self):
        from django.conf import settings

        cache.clear()
        for i in range(5):
            self.auth_upstream.targets.create(
                host=AUTH_SERVER, scheme="https", weight=50
            )
        for i in range(10):
            resp = self.client.get("/users/")

    def test_cached_api(self):
        stream = Upstream.objects.create(host=AUTH_SERVER, scheme=SCHEME, alias=uuid4())
        Api.objects.create(
            name="programs",
            request_path="/programs",
            wrapped_path="/programs",
            upstream=stream,
            plugin=0,
        )
        Api.objects.create(
            name="audios",
            request_path="/audios",
            wrapped_path="/audios",
            upstream=stream,
            plugin=0,
        )
        cache.clear()
        settings.DEBUG = True
        self.client.get("/users/")
        self.client.get("/users/not_matched")
        self.client.get("/audios/")
        self.client.get("/audios/me/")
        self.assertEqual(cache.get("cache_hit"), 2)
        cache.clear()
        api_cache = UseSingleCache(0, "api")
        for api in Api.objects.prefetch_related(
            "upstream", "upstream__targets"
        ).iterator():
            api_cache.set(api, 3600, path=api.request_path, upstream=api.upstream.pk)
        self.client.get("/users/")
        self.client.get("/users/not_matched")
        self.client.get("/audios/")
        self.client.get("/audios/me/")
        self.assertEqual(cache.get("cache_hit"), 4)

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
