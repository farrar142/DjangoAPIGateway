import requests
from typing import Generic, Optional, List
from django.db.models import F, Value, QuerySet
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from common_module.caches import UseSingleCache
from common_module.mixins import MockRequest
from .models import Api

# from ninja import NinjaAPI, Router

# api = NinjaAPI()

# router = Router()

# inner = Router()


# @router.get("/test")
# class Test:
#     string = "test"

#     def __init__(self, request):
#         print("add router")
#         return

#     def __call__(self, request):
#         return

#     @inner.get("test")
#     def test(self, request):
#         return 'test'


class gateway(APIView):
    authentication_classes = ()
    cache: UseSingleCache[Api] = UseSingleCache(0, "api")

    def operation(self, request: MockRequest):
        path = request.path_info.split("/")
        if len(path) < 2:
            return Response("bad request", status=status.HTTP_400_BAD_REQUEST)

        api_cache = self.cache.get(path=request.path_info)
        if not api_cache:
            api_caches: QuerySet[Api] = (
                Api.objects.prefetch_related("upstream")
                .annotate(search_path=Value(request.path_info))
                .filter(search_path__startswith=F("request_path"))
            )
            api_cache = api_caches.first()
            if api_cache:
                self.cache.set(api_cache, 3600 * 24 * 30)

        # api_cache = Api.objects.filter(name=(api_name)).first()
        if not api_cache:
            return Response("bad request", status=status.HTTP_404_NOT_FOUND)
        # api_cache: Api = cache.get(f"api/{api_name}")
        # if api_cache:
        #     print("get from cache")
        # if not api_cache:
        #     apimodel = Api.objects.filter(name=api_name).first()
        #     if apimodel is None:
        #         return Response('bad request', status=status.HTTP_400_BAD_REQUEST)
        #     print("set cache")
        #     cache.set(f"api/{api_name}", apimodel)
        #     api_cache = apimodel

        valid, msg = api_cache.check_plugin(request)
        if not valid:
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        res = api_cache.send_request(request)
        if res.headers.get("Content-Type", "").lower() == "application/json":
            data = res.json()
        elif res.headers.get("Content-Type", "").lower() == "text/html":
            return HttpResponse(content=res.content, content_type="text/html")
        else:
            data = res.content
        return Response(data=data, status=res.status_code)

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


# router.add_router('/inner', inner)
# api.add_router("/events", router)
