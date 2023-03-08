from typing import Literal, Any, Callable
from typing import Protocol, Iterable

from django.http.request import HttpRequest, QueryDict
from django.utils.datastructures import MultiValueDict
from django.core.cache import BaseCache, cache as _cache
from django.core.files.uploadedfile import InMemoryUploadedFile

from rest_framework.request import Request


class MockRequest(HttpRequest, Request):
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE", "__default__"]
    user: Any | None
    data: MultiValueDict[str, Any]
    FILES: MultiValueDict[str, InMemoryUploadedFile]
    query_params: QueryDict


# 타입 힌트용 래퍼 데코레이터
def cache_wrapper(func: Callable[..., Any]):
    class CacheOverride(BaseCache):
        def keys(self, lookup: str) -> list[str]:
            ...

        def delete_many(self, lookups: Iterable[str]) -> None:
            ...

    def helper(*args, **kwargs) -> CacheOverride:
        return func(*args, **kwargs)

    return helper


@cache_wrapper
def get_cache(cache: BaseCache):
    return cache


cache = get_cache(_cache)
