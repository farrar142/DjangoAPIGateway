from typing import Callable, Optional, Self
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser

from rest_framework.authentication import BasicAuthentication

from base.authentications import (
    InternalJWTAuthentication,
)
from base.exceptions import TokenExpiredExcpetion


from base.wrappers import MockRequest


class Consumer(models.Model):
    user_id = models.IntegerField()
    identifier = models.CharField(max_length=256, default="")
    apikey = models.CharField(max_length=32)

    def __unicode__(self):
        return self.user_id

    def __str__(self):
        return f"{self.user_id}"


class PluginChoices(models.IntegerChoices):
    NO_AUTH = 0
    BASIC_AUTH = 1
    KEY_AUTH = 2
    ADMIN_ONLY = 3


class PluginMap:
    plugins: dict[
        int, Callable[["PluginProcessor", MockRequest], tuple[bool, str, int]]
    ] = dict()

    @classmethod
    def plugin_injector(cls, order: int):
        def decorator(
            func: Callable[["PluginProcessor", MockRequest], tuple[bool, str, int]]
        ):
            def wrapper(*args):
                return func(*args)

            # if cls.done:
            #     return wrapper

            cls.plugins[order] = func

            return wrapper

        return decorator


class PluginProcessor:
    def __init__(self, plugin_manager: "PluginMixin", request: MockRequest):
        self.plugin_manager = plugin_manager
        self.request = request

    def process(self, plugin: int):
        return PluginMap.plugins[plugin](self, self.request)

    @PluginMap.plugin_injector(order=PluginChoices.NO_AUTH)
    def process_plugin(self, request: MockRequest):
        return True, "", 200

    @PluginMap.plugin_injector(order=PluginChoices.BASIC_AUTH)
    def process_basic_auth(self, request: MockRequest):
        auth = BasicAuthentication()
        user: Optional[AbstractBaseUser] = None
        try:
            authenticated = auth.authenticate(request)
            if authenticated:
                user, password = authenticated
        except:
            return False, "Authentication credentials were not provided", 401

        if user and self.plugin_manager.consumers.filter(user=user):
            return True, "", 200
        else:
            return False, "permission not allowed", 403

    @PluginMap.plugin_injector(order=PluginChoices.KEY_AUTH)
    def process_key_auth(self, request: MockRequest):
        apikey = request.META.get("HTTP_APIKEY")
        consumers = self.plugin_manager.consumers.filter(apikey=apikey)
        if consumers.exists():
            return True, "", 200
        return False, "apikey need", 401

    @PluginMap.plugin_injector(order=PluginChoices.ADMIN_ONLY)
    def process_admin_auth(self, request: MockRequest):
        auth = InternalJWTAuthentication()
        try:
            user, token = auth.authenticate(request)
            if token != None:
                if token.role and "staff" in token.role:
                    return True, "", 200
            return False, "permission not allowed", 403
        except TokenExpiredExcpetion:
            return False, "Token Expired", 422
        except:
            pass
        return False, "permission not allowed", 401
            

# PluginMap.done = True


class PluginMixin(models.Model):
    class Meta:
        abstract = True

    plugin = models.IntegerField(choices=PluginChoices.choices, default=0)
    consumers = models.ManyToManyField(Consumer, blank=True)

    def check_plugin(self, request: MockRequest) -> tuple[bool, str, int]:
        processor = PluginProcessor(self, request)
        try:
            return processor.process(self.plugin)
        except:
            raise NotImplementedError("plugin %d not implemented" % self.plugin)
