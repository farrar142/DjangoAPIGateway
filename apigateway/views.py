import requests
from django.shortcuts import render
from django.http import HttpResponse
from django.http.request import HttpRequest
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .models import Api


class gateway(APIView):
    authentication_classes = ()

    def operation(self, request: HttpRequest):
        path = request.path_info.split('/')
        print(f"{request.path_info=}")
        if len(path) < 2:
            return Response('bad request', status=status.HTTP_400_BAD_REQUEST)

        apimodel = Api.objects.filter(name=path[1]).first()
        if apimodel is None:
            return Response('bad request', status=status.HTTP_400_BAD_REQUEST)

        valid, msg = apimodel.check_plugin(request)
        if not valid:
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        res = apimodel.send_request(request)
        if res.headers.get('Content-Type', '').lower() == 'application/json':
            data = res.json()
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
