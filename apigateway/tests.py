import requests
import time
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken
from runthe_backend.test import TestCase
from common_module.mixins import ServerRequests
from .models import Api, Upstream
from common_module.authentication import parse_jwt

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
            request_path="/users/me",
            wrapped_path="/users/me",
            upstream=self.auth_upstream,
            plugin=0,
        )

    def test_middleware(self):
        resp = self.client.get("/")
        print(resp)

    def test_auth_server_authenticate(self):
        resp = self.client.post(
            "/auth/token",
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

    def test_server_request(self):
        auth = ServerRequests("ASSET_SERVER", "")
        print(auth.host)
