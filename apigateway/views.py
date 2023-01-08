import requests
from typing import Generic, Optional, List
from django.db.models import F, Value, QuerySet
from django.http.request import HttpRequest
from django.http.response import HttpResponse

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404
from apigateway.serializers import UpstreamSerializer
from common_module.caches import UseSingleCache
from common_module.mixins import MockRequest, ReadOnlyMixin
from .models import Api, Upstream

# from ninja import NinjaAPI, Router

# api = NinjaAPI()

# router = Router()

# inner = Router()


class Consul(ReadOnlyMixin, viewsets.ModelViewSet):
    authentication_classes = ()
    queryset = Upstream.objects.all()
    lookup_field = "alias"
    serializer_class = UpstreamSerializer


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

        valid, msg, _status = api_cache.check_plugin(request)
        if not valid:
            return Response(msg, status=_status)

        res = api_cache.send_request(request)
        if res.headers.get("Content-Type", "").lower() == "application/json":
            data = res.json()
        elif res.headers.get("Content-Type", "").lower() == "text/html":
            return HttpResponse(
                content=res.content, status=res.status_code, content_type="text/html"
            )
        else:
            data = res.content
        if res.status_code == 204:
            return Response(status=res.status_code)
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
