# import requests_unixsocket
import json
import requests
from typing import Any, Callable, Self, Type

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.html import format_html
from django.urls import reverse_lazy
from .nodes import ChildNode, LoadBalancer
from .plugins import PluginMixin
from .caches import UseSingleCache
from .wrappers import MockRequest


class User(AbstractUser):
    nickname = models.CharField(max_length=150)

    @property
    def user_id(self):
        return self.pk

    def __str__(self):
        return self.username

    def __getitem__(self, key: str, default=None):
        return getattr(self, key, default)

    def get(self, key: str, default=None):
        return self.__getitem__(key, default)


class ApiType(models.TextChoices):
    NORMAL = "일반"
    ADMIN = "관리자"


class Upstream(LoadBalancer):
    alias = models.CharField(max_length=64, default="", unique=True)
    targets: models.Manager["Target"]
    api_set: models.Manager["Api"]

    @property
    def total_targets(self):
        return self.targets.count() or 1

    total_targets.fget.short_description = "Total Node Count"

    @property
    def total_apis(self):
        return self.api_set.count()

    total_apis.fget.short_description = "Total API Route Count"

    @property
    def total_weight(self):
        aggregate = self.targets.aggregate(total_weight=models.Sum(models.F("weight")))[
            "total_weight"
        ]
        # raise
        aggregate = aggregate or 0
        return aggregate + self.weight

    total_weight.fget.short_description = "Total Weight"

    def to_string(self):
        return self.host

    def __str__(self):
        return f"{self.alias}"

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


class Target(ChildNode):
    upstream = models.ForeignKey(
        Upstream, on_delete=models.CASCADE, related_name="targets"
    )
    upstream_id: int

    def toggle_button(self):
        text = "Activate" if not self.enabled else "Deactivate"
        return format_html(
            '<a href="{}" class="link">{}</a>',
            reverse_lazy("admin:admin_toggle_enabled", args=[self.pk]),
            text,
        )

    def to_string(self):
        return self.host

    def __str__(self):
        str(self.upstream.alias)
        return f"{self.scheme}/{self.host} - {self.weight}"

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


class Api(PluginMixin, models.Model):
    cache: UseSingleCache[Type[Self]] = UseSingleCache(0, "api")

    PLUGIN_CHOICE_LIST = (
        (0, "No auth"),
        (1, "Basic auth"),
        (2, "Key auth"),
        (3, "Admin only."),
    )

    name = models.CharField(max_length=128)
    request_path = models.CharField(max_length=255)
    wrapped_path = models.CharField(max_length=255)
    upstream = models.ForeignKey(
        Upstream, on_delete=models.CASCADE, related_name="api_set"
    )

    method_map: dict[str, Callable[..., requests.Response]] = {
        "get": requests.get,
        "post": requests.post,
        "put": requests.put,
        "patch": requests.patch,
        "delete": requests.delete,
    }

    def get_trailing_path(self, request: MockRequest):
        return request.get_full_path().removeprefix(self.request_path)

    def get_method(self, request: MockRequest):
        method = request.method or "get"
        return method.lower()

    def process_headers(self, request: MockRequest):
        headers = {}
        headers["X-Forwarded-For"] = request.headers.get("X-Forwarded-For", None)
        headers["Host"] = request.headers.get("Host", None)
        headers["Authorization"] = request.META.get("HTTP_AUTHORIZATION")
        if request.content_type and request.content_type.lower() == "application/json":
            headers["Content-Type"] = request.content_type
        return headers

    def process_data(self, request: MockRequest):
        if request.FILES is not None and isinstance(request.FILES, dict):
            for k, v in request.FILES.items():
                if request.data.get(k, False):
                    request.data.pop(k)
        if request.content_type and request.content_type.lower() == "application/json":
            data = json.dumps(request.data)
        else:
            data = request.data
        return data

    def show_errors(self, resp: requests.Response):
        if resp.status_code in [400, 404, 409]:
            try:
                print(resp.json())
            except:
                pass

    def send_request(self, request: MockRequest):
        trailing_path = self.get_trailing_path(request)
        method = self.get_method(request)
        headers = self.process_headers(request)
        data = self.process_data(request)
        resp = self.upstream.send_request(
            self, trailing_path, method, headers, data, request.FILES
        )
        self.show_errors(resp)
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
        return f"{self.name}"

    def get(self, __name: str):
        return self.__getattribute__(__name)

    def __enter__(self):
        # con = self.upstream.incr_conn()
        # print(f"{self.upstream} conn count", con)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # con = self.upstream.decr_conn()
        return
