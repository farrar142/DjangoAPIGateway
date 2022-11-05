import requests
import json

from typing import Optional

from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.http.request import HttpRequest

from rest_framework.authentication import get_authorization_header, BasicAuthentication
from rest_framework import HTTP_HEADER_ENCODING
from rest_framework.request import Request

from accounts.models import User

# Create your models here.


class Consumer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    apikey = models.CharField(max_length=32)

    def __unicode__(self):
        return self.user.username

    def __str__(self):
        return self.user.username


class Api(models.Model):
    PLUGIN_CHOICE_LIST = (
        (0, 'Remote auth'),
        (1, 'Basic auth'),
        (2, 'Key auth'),
        (3, 'Server auth')
    )
    name = models.CharField(max_length=128, unique=True)
    request_path = models.CharField(max_length=255)
    upstream_url = models.CharField(max_length=255)
    plugin = models.IntegerField(choices=PLUGIN_CHOICE_LIST, default=0)
    consumers = models.ManyToManyField(Consumer, blank=True)

    def check_plugin(self, request: HttpRequest):
        if self.plugin == 0:
            return True, ''

        elif self.plugin == 1:
            auth = BasicAuthentication()
            user: Optional[AbstractBaseUser] = None
            try:
                authenticated = auth.authenticate(request)
                if authenticated:
                    user, password = authenticated
            except:
                return False, 'Authentication credentials were not provided'

            if user and self.consumers.filter(user=user):
                return True, ''
            else:
                return False, 'permission not allowed'
        elif self.plugin == 2:
            apikey = request.META.get('HTTP_APIKEY')
            consumers = self.consumers.filter(apikey=apikey)
            if consumers.exists():
                return True, ''
            return False, 'apikey need'
        elif self.plugin == 3:
            consumer = self.consumers.all()
            if not consumer.exists():
                return False, 'consumer need'
            request.META['HTTP_AUTHORIZATION'] = "#FIXME"
            return True, ''
        else:
            raise NotImplementedError(
                "plugin %d not implemented" % self.plugin)

    def send_request(self, request: HttpRequest) -> requests.Response:
        headers = {}
        if self.plugin != 1 and request.META.get('HTTP_AUTHORIZATION'):
            headers['Authorization'] = request.META.get('HTTP_AUTHORIZATION')
        # headers['content-type'] = request.content_type
        print("send_request")
        """
        요청 http://localhost:9000/programs/1/data/
        strip = /service/programs
        full_path = /programs/1/data/
        """
        full_path = request.get_full_path()[len(self.request_path)+1:]
        url = self.upstream_url + full_path
        method = request.method or 'get'
        method = method.lower()
        method_map = {
            'get': requests.get,
            'post': requests.post,
            'put': requests.put,
            'patch': requests.patch,
            'delete': requests.delete
        }

        for k, v in request.FILES.items():
            request.data.pop(k)

        if request.content_type and request.content_type.lower() == 'application/json':
            data = json.dumps(request.data)
            headers['content-type'] = request.content_type
        else:
            data = request.data

        return method_map[method](url, headers=headers, data=data, files=request.FILES)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name
