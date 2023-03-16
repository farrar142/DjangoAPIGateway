import re
import requests
import hashlib
from typing import Callable, Optional
from django.db.models import F, Value
from django.http.response import HttpResponse
from django.conf import settings

from rest_framework import status, exceptions
from rest_framework.views import APIView
from base.exceptions import TimeoutException, ConflictException
from base.caches import UseSingleCache, cache
from base.wrappers import MockRequest

from .models import Api

MINUTE = 60
HOUR = MINUTE * 60
DAY = HOUR * 24
OPERAION_FUNC = Callable[["gateway", MockRequest], requests.Response]


def hasher(string: str) -> str:
    return hashlib.blake2b(string.encode("utf-8")).hexdigest()


def get_idempotent_key(request: MockRequest):
    key = request.headers.get("Idempotency-Key", None)
    user = request.headers.get("Authorization", "Anon")
    content_type = request.headers.get("Content-Type", "application/json")
    if key:
        string = f"{user}:{request.get_full_path()}:{request.method}:{content_type}:{request.data}:{key}"
        return hasher(string)
    return None


def block_cached_idempotent_response(
    key: str, retries=0
) -> Optional[requests.Response]:
    if retries >= 10:
        raise TimeoutException
    response = cache.get(key, None)
    if response == "in_progress":
        raise ConflictException(detail={"duplicated": ["이미 처리중인 요청입니다."]})
    else:
        cache.add(key, "in_progress")
    return response


def idempotent_wrapper(func: OPERAION_FUNC):
    def wrapper(view: "gateway", request: MockRequest):
        response: Optional[requests.Response] = None
        key = get_idempotent_key(request)
        if key:
            # 캐시에서 키검색
            response = block_cached_idempotent_response(key)
            if response != None:
                print("hit idemp")
            if not response:
                response = func(view, request)
                cache.set(key, response, timeout=15 * DAY)
        else:
            response = func(view, request)
        return response

    return wrapper


def http_responser(func: OPERAION_FUNC):
    def wrapper(view: "gateway", request: MockRequest):
        response = func(view, request)

        if response.status_code == 204:
            return HttpResponse(status=status.HTTP_204_NO_CONTENT)

        content_type = response.headers.get("Content-Type", "").lower()
        return HttpResponse(
            content=response.content,
            status=response.status_code,
            content_type=content_type,
        )

    return wrapper


class gateway(APIView):
    # authentication_classes = ()
    cache: UseSingleCache[Api] = UseSingleCache(0, "api")

    def validate_path(self, path: list[str]):
        if len(path) < 2:
            raise exceptions.NotFound

    def get_path_mathced_api(self, path: str):
        return (
            Api.objects.prefetch_related("upstream", "upstream__targets")
            .annotate(search_path=Value(path))
            .filter(search_path__startswith=F("request_path"))
        )

    def get_cached_api(self, path: str) -> Optional[Api]:
        search_key = "0/api:path=(.+?):upstream=(.*):end"
        for key in cache.keys("0/api:*:end"):
            result = re.search(search_key, key)
            if not result:
                continue
            target_path = result.group(1)
            if path.startswith(target_path):
                return cache.get(key, None)
        return None

    def get_api(self, path: str):
        api = self.get_cached_api(path)
        if api:
            if settings.DEBUG == True:
                cache.add("cache_hit", 0)
                cache.incr("cache_hit", 1)
        if not api:
            apis = self.get_path_mathced_api(path)
            api = apis.first()
            if api:
                self.cache.set(
                    api,
                    30 * DAY,
                    path=api.request_path,
                    upstream=api.upstream.pk,
                )
        if not api:
            raise exceptions.NotFound
        return api

    def check_plugin(self, api: Api, request: MockRequest):
        valid, msg, _status = api.check_plugin(request)

        if not valid:
            err = exceptions.APIException(detail={"error": [msg]}, code=_status)
            err.status_code = _status
            raise err

    @http_responser
    @idempotent_wrapper
    def operation(self, request: MockRequest):
        self.validate_path(request.path_info.split("/"))
        api = self.get_api(request.path_info)
        self.check_plugin(api, request)
        with api:
            return api.send_request(request)

    def get(self, request):
        return self.operation(request)

    def post(self, request):
        return self.operation(request)

    def put(self, request):
        return self.operation(request)

    def patch(self, request):
        return self.operation(request)

    def delete(self, request):
        return self.operation(request)
