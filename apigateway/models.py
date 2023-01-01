import requests
import requests_unixsocket
import json

from typing import Any, Callable, Optional, Self, Type, TypedDict

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.http.request import HttpRequest

from rest_framework.authentication import get_authorization_header, BasicAuthentication
from rest_framework import HTTP_HEADER_ENCODING
from rest_framework.request import Request

from common_module.authentication import (
    ThirdPartyAuthentication,
    InternalJWTAuthentication,
)
from common_module.caches import UseSingleCache
from common_module.mixins import MockRequest

# Create your models here.

SCHEME_DELIMETER = "://"


class SchemeType(models.TextChoices):
    HTTP = "http"
    HTTPS = "https"
    UNITX = "http+unix"


class ApiType(models.TextChoices):
    NORMAL = "일반"
    ADMIN = "관리자"


class Consumer(models.Model):
    user_id = models.IntegerField()
    apikey = models.CharField(max_length=32)

    def __unicode__(self):
        return self.user_id

    def __str__(self):
        return f"{self.user_id}"


class Upstream(models.Model):
    host = models.CharField(max_length=255)
    alias = models.CharField(max_length=64, default="", unique=True)
    scheme = models.CharField(
        max_length=64, choices=SchemeType.choices, default=SchemeType.HTTP
    )

    @property
    def full_path(self):
        return self.scheme + SCHEME_DELIMETER + self.host

    def to_string(self):
        return self.host

    def __str__(self):
        return f"{self.alias}"


"""
0=서버에 인증 유보
1=게이트웨이 인증
"""


class Api(models.Model):
    cache: UseSingleCache[Type[Self]] = UseSingleCache(0, "api")

    PLUGIN_CHOICE_LIST = (
        (0, "토큰을 검사하지 않습니다"),
        (1, "Basic auth"),
        (2, "Key auth"),
        (3, "게이트웨이에서 토큰을 검사합니다. 어드민 만 접근가능합니다."),
    )

    name = models.CharField(max_length=128, unique=True)
    request_path = models.CharField(max_length=255)
    wrapped_path = models.CharField(max_length=255)
    upstream = models.ForeignKey(Upstream, on_delete=models.CASCADE)
    plugin = models.IntegerField(choices=PLUGIN_CHOICE_LIST, default=0)
    consumers = models.ManyToManyField(Consumer, blank=True)

    method_map: dict[str, Callable[..., requests.Response]] = {
        "get": requests.get,
        "post": requests.post,
        "put": requests.put,
        "patch": requests.patch,
        "delete": requests.delete,
    }
    unix_session: requests_unixsocket.Session

    @property
    def unix_map(self):
        unix_session = requests_unixsocket.Session()
        self.unix_session = unix_session
        return {
            "get": unix_session.get,
            "post": unix_session.post,
            "patch": unix_session.patch,
            "delete": unix_session.delete,
            "put": unix_session.put,
        }

    @property
    def full_path(self):
        return self.upstream.full_path + self.wrapped_path

    def check_plugin(self, request: MockRequest):
        if self.plugin == 0:
            return True, ""

        elif self.plugin == 1:
            auth = BasicAuthentication()
            user: Optional[AbstractBaseUser] = None
            try:
                authenticated = auth.authenticate(request)
                if authenticated:
                    user, password = authenticated
            except:
                return False, "Authentication credentials were not provided"

            if user and self.consumers.filter(user=user):
                return True, ""
            else:
                return False, "permission not allowed"
        elif self.plugin == 2:
            apikey = request.META.get("HTTP_APIKEY")
            consumers = self.consumers.filter(apikey=apikey)
            if consumers.exists():
                return True, ""
            return False, "apikey need"
        elif self.plugin == 3:
            auth = InternalJWTAuthentication()
            token, _ = auth.authenticate(request)
            if token != None:
                if token.get("role") and "staff" in token.get("role"):
                    return True, ""
            return False, "permission not allowed"
        else:
            raise NotImplementedError("plugin %d not implemented" % self.plugin)

    def send_request(self, request: MockRequest):
        headers = {}
        # if self.plugin != 1 and request.META.get('HTTP_AUTHORIZATION'):
        headers["Authorization"] = request.META.get("HTTP_AUTHORIZATION")
        # headers['content-type'] = request.content_type
        """
        요청 http://localhost:9000/programs/1/data/
        strip = /service/programs
        full_path = /programs/1/data/
        """
        trailing_path = request.get_full_path().removeprefix(self.request_path)
        url = self.full_path + trailing_path
        method = request.method or "get"
        method = method.lower()

        if request.FILES is not None and isinstance(request.FILES, dict):
            for k, v in request.FILES.items():
                request.data.pop(k)

        if request.content_type and request.content_type.lower() == "application/json":
            data = json.dumps(request.data)
            print(f"{request.data=}")
            headers["content-type"] = request.content_type
        else:
            data = request.data
        print(f"{data=}")

        if self.upstream.scheme == SchemeType.UNITX:
            res = self.unix_map[method](
                url, headers=headers, data=data, files=request.FILES
            )
            self.unix_session.close()
            return res
        resp = self.method_map[method](
            url, headers=headers, data=data, files=request.FILES
        )
        if resp.status_code in [400, 404]:
            print(resp.json())
        return resp

    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)
        keys = Api.cache.get_global_keys()
        for key in keys:
            Api.cache.purge_global_keys(key)
        return instance

    def delete(
        self, using: Any = ..., keep_parents: bool = ...
    ) -> tuple[int, dict[str, int]]:
        deleted = super().delete(using, keep_parents)
        keys = Api.cache.get_global_keys()
        for key in keys:
            Api.cache.purge_global_keys(key)
        return deleted

    def __unicode__(self):
        return self.name

    def __str__(self):
        return f"{self.name} : {self.upstream}{self.request_path}"

    def get(self, __name: str):
        return self.__getattribute__(__name)
