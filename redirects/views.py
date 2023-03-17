from django.shortcuts import render,redirect
from django.db import models
# Create your views here.
from django.http.response import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response

from base.wrappers import MockRequest
from .models import RedirectionPage

class RedirectionViewSet(APIView):
    PREFIX='redirections'
    authentication_classes = ()
    def operation(self, request: MockRequest):
        requested_path = request.path_info.removeprefix(f"/{self.PREFIX}/")
        page = RedirectionPage.objects.annotate(search_path=models.Value(requested_path)).filter(search_path__startswith=models.F('requested_path')).first()
        if not page:
            return Response({})
        return redirect(page.target_path)

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
