import requests

# import requests_unixsocket
import json
from itertools import accumulate
from random import randint

from typing import Any, Callable, Iterable, Optional, Protocol, Self, Type, TypedDict

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.utils.html import format_html
from django.urls import reverse_lazy
from django.core.cache import cache

from rest_framework.authentication import get_authorization_header, BasicAuthentication
from rest_framework import HTTP_HEADER_ENCODING
from rest_framework.request import Request

from common_module.authentication import (
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


class LoadBalancingType(models.TextChoices):
    ROUND_ROBIN = "round_robin"
    WEIGHT_ROBIN = "weight_robin"


class Consumer(models.Model):
    user_id = models.IntegerField()
    identifier = models.CharField(max_length=256, default="")
    apikey = models.CharField(max_length=32)

    def __unicode__(self):
        return self.user_id

    def __str__(self):
        return f"{self.user_id}"


"""
1. 로드 밸런싱 기능
2. 다른 Target으로 Retry기능
"""


class Node(models.Model):
    class Meta:
        abstract = True

    host = models.CharField(max_length=255)
    scheme = models.CharField(
        max_length=64, choices=SchemeType.choices, default=SchemeType.HTTP
    )
    weight = models.PositiveIntegerField(default=100)

    @property
    def full_path(self):
        return self.scheme + SCHEME_DELIMETER + self.host


class ServerConnectionRecord:
    pk: int

    @property
    def conn_key(self):
        return f"upstream:{self.pk}-connection"

    def get_conn(self):
        return cache.get(self.conn_key, 0)

    def incr_conn(self):
        # 현재 업스트림에 연결돈 커넥션 수를 증가시킵니다
        cache.add(self.conn_key, 0)
        return cache.incr(self.conn_key, 1)

    def decr_conn(self):
        # 현재 업스트림에 연결돈 커넥션 수를 감소시킵니다
        return cache.decr(self.conn_key, 1)


class Upstream(ServerConnectionRecord, Node):
    alias = models.CharField(max_length=64, default="", unique=True)
    load_balance = models.CharField(
        max_length=64,
        default=LoadBalancingType.ROUND_ROBIN,
        choices=LoadBalancingType.choices,
    )
    targets: models.Manager["Target"]

    @property
    def total_weight(self):
        aggregate = self.targets.aggregate(total_weight=models.Sum(models.F("weight")))[
            "total_weight"
        ]
        # raise
        aggregate = aggregate or 0
        return aggregate + self.weight

    total_weight.fget.short_description = "총 가중치"

    # def initialize_target(self):
    #     keys = list(map(lambda x: x.my_key, self.targets.all()))
    #     key_map = {k: 1 for k in keys}
    #     cache.set_many(key_map)

    @property
    def target_keys(self):
        return f"upstream:{self.pk}-target:*-lb"

    def to_string(self):
        return self.host

    def __str__(self):
        return f"{self.alias}"

    @property
    def req_key(self):
        return f"upstream:{self.pk}-called"

    def call(self):
        cache.add(self.req_key, 0)
        return cache.incr(self.req_key, 1)

    def round_robin(
        self, req_count: int, targets: list["Target"], target_count: int
    ) -> Node:
        cur_idx = req_count % target_count
        return targets[cur_idx - 1]

    def weight_round(self, req_count: int, targets: list["Target"], target_count: int):
        """
        100,50,200 가중치를
        100 150 250 구간으로 나눔
        """
        max = sum(map(lambda x: x.weight, targets))
        accs = accumulate(map(lambda x: x.weight, targets))
        zipped = list(zip(accs, targets))

        rand = randint(0, max)

        def find(node: tuple[int, Node]):
            weight = node[0]
            return rand < weight

        node: tuple[int, Node] = next(filter(find, zipped), (0, self))
        return node[1]

    def load_balancing(self) -> Node:
        req_count = self.call()
        targets = list(filter(lambda x: x.enabled, self.targets.all()))
        target_count = len(targets)
        if target_count == 0:
            return self
        if self.load_balance == LoadBalancingType.WEIGHT_ROBIN:
            return self.weight_round(req_count, targets, target_count)
        return self.round_robin(req_count, targets, target_count)

    def save(self, *args, **kwargs) -> None:
        res = super().save(*args, **kwargs)
        single_cache = UseSingleCache(0, "api")
        single_cache.purge_by_regex(upstream=self.pk, path="*")
        return res

    def delete(self, *args, **kwargs):
        result = super().delete(*args, **kwargs)
        single_cache = UseSingleCache(0, "api")
        single_cache.purge_by_regex(upstream=self.pk, path="*")
        return result


class Target(Node):
    upstream = models.ForeignKey(
        Upstream, on_delete=models.CASCADE, related_name="targets"
    )
    upstream_id: int
    enabled = models.BooleanField("활성화", default=True)

    def toggle_button(self):
        text = "Activate" if not self.enabled else "Deactivate"
        return format_html(
            '<a href="{}" class="link">{}</a>',
            reverse_lazy("admin:admin_toggle_enabled", args=[self.pk]),
            text,
        )

    # @property
    # def my_key(self):
    #     return f"upstream:{self.upstream_id}-target:{self.pk}-lb"

    # def initialize(self):
    #     cache.add(self.my_key, 1)

    # def call(self):
    #     cache.incr(self.my_key, 1)

    def to_string(self):
        return self.host

    def __str__(self):
        return f"{self.upstream.alias}/{self.host} - {self.weight}"

    def save(self, *args, **kwargs) -> None:
        res = super().save(*args, **kwargs)
        single_cache = UseSingleCache(0, "api")
        single_cache.purge_by_regex(upstream=self.upstream_id, path="*")
        return res

    def delete(self, *args, **kwargs):
        result = super().delete(*args, **kwargs)
        single_cache = UseSingleCache(0, "api")
        single_cache.purge_by_regex(upstream=self.upstream_id, path="*")
        return result


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
    # unix_session: requests_unixsocket.Session

    # @property
    # def unix_map(self) -> dict[str, Callable[..., requests.Response]]:
    #     unix_session = requests_unixsocket.Session()
    #     self.unix_session = unix_session
    #     return {
    #         "get": unix_session.get,
    #         "post": unix_session.post,
    #         "patch": unix_session.patch,
    #         "delete": unix_session.delete,
    #         "put": unix_session.put,
    #     }

    @property
    def full_path(self):
        return self.upstream.load_balancing().full_path + self.wrapped_path

    def check_plugin(self, request: MockRequest) -> tuple[bool, str, int]:
        if self.plugin == 0:
            return True, "", 200

        elif self.plugin == 1:
            auth = BasicAuthentication()
            user: Optional[AbstractBaseUser] = None
            try:
                authenticated = auth.authenticate(request)
                if authenticated:
                    user, password = authenticated
            except:
                return False, "Authentication credentials were not provided", 401

            if user and self.consumers.filter(user=user):
                return True, "", 200
            else:
                return False, "permission not allowed", 403
        elif self.plugin == 2:
            apikey = request.META.get("HTTP_APIKEY")
            consumers = self.consumers.filter(apikey=apikey)
            if consumers.exists():
                return True, "", 200
            return False, "apikey need", 401
        elif self.plugin == 3:
            auth = InternalJWTAuthentication()
            token, _ = auth.authenticate(request)
            if token != None:
                if token.role and "staff" in token.role:
                    return True, "", 200
            return False, "permission not allowed", 403
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
            headers["content-type"] = request.content_type
        else:
            data = request.data

        resp = self.method_map[method](
            url, headers=headers, data=data, files=request.FILES
        )
        if resp.status_code in [400, 404]:
            try:
                print(resp.json())
            except:
                return resp
        return resp

    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)
        self.cache.purge_by_regex(path="*", upstream=self.upstream.pk)
        return instance

    def delete(
        self, using: Any = ..., keep_parents: bool = ...
    ) -> tuple[int, dict[str, int]]:
        self.cache.purge_by_regex(path="*", upstream=self.upstream.pk)
        deleted = super().delete(using, keep_parents)
        return deleted

    def __unicode__(self):
        return self.name

    def __str__(self):
        return f"{self.name} : {self.upstream}{self.request_path}"

    def get(self, __name: str):
        return self.__getattribute__(__name)

    def __enter__(self):
        con = self.upstream.incr_conn()
        print("conn count", con)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        con = self.upstream.decr_conn()
        return
