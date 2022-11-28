import requests
import time
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken
from common_module.test import TestCase
from .models import Api, Upstream
from common_module.authentication import parse_jwt

# Create your tests here.
SCHEME = "http"


class TestApiGateway(TestCase):
    auth: Api

    # def setUp(self):
    #     Upstream.objects.all().delete()
    #     Api.objects.all().delete()
    #     self.auth_upstream = Upstream.objects.create(
    #         host="172.17.0.1:9001"
    #         # host="api.mypacer.palzakspot.com"
    #     )
    #     self.auth = Api.objects.create(
    #         name="auth",
    #         request_path="/auth",
    #         wrapped_path="/auth",
    #         scheme=SCHEME,
    #         upstream=self.auth_upstream,
    #         plugin=0
    #     )
    #     self.auth = Api.objects.create(
    #         name="users",
    #         request_path="/users/me",
    #         wrapped_path="/users/me",
    #         scheme=SCHEME,
    #         upstream=self.auth_upstream,
    #         plugin=0
    #     )
    def test_middleware(self):
        resp = self.client.get("/")
        print(resp)

    # def test_auth_server_authenticate(self):
    #     resp = self.client.post("/auth/token", {
    #         "email": "gksdjf1690@gmail.com",
    #         "password": "gksdjf452@"
    #     })
    #     self.assertEqual(200, status.HTTP_200_OK)
    #     access_token = resp.json().get("access")
    #     self.client.login(access_token)
    #     # print(f"{AccessToken(access_token)=}")
    #     resp = self.client.get("/users/me/")
    #     self.assertEqual(resp.status_code, status.HTTP_200_OK)

    #     request_url = "admin/users/1/activities"
    #     wrapped_path = "admin/users"

    # def test_ninja_router_test(self):
    #     resp = self.client.get("/test/events/test/inner")
    #     # self.assertEqual(resp.status_code, 200)
    #     # self.assertEqual(resp.json(), "test")
    #     print(resp.status_code)
