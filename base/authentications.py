import jwt
from dataclasses import dataclass, field, fields
from uuid import uuid4
from typing import Optional, Literal, TypedDict, Mapping
from django.http import HttpRequest

# from django.contrib.auth.models import AnonymousUser

from rest_framework import authentication, exceptions
from rest_framework.request import Request

from base.exceptions import TokenExpiredExcpetion

from .utils import aware_utcnow, datetime_from_epoch


@dataclass(init=False)
class Token:
    exp: str
    iat: int
    jti: str
    user_id: int
    username: str
    nickname: str
    token_type: Literal["refresh", "access"] = "access"
    role: list[Literal["staff", "creator"]] = field(default_factory=list)
    membership: Optional[dict] = None

    def __init__(self, **kwargs):
        names = set([f.name for f in fields(self)])
        for k, v in kwargs.items():
            if k in names:
                setattr(self, k, v)

    def __getitem__(self, key: str, default=None):
        return getattr(self, key, default)

    def get(self, key: str, default=None):
        return self.__getitem__(key, default)

    @classmethod
    def make_user_token(cls, user_id: int):
        return Token(exp="", iat=0, jti="", user_id=user_id, username="", nickname="")


def get_jwt_token_from_dict(data: dict):
    bearer_token: Optional[str] = data.get("HTTP_AUTHORIZATION")
    if not bearer_token:
        return False
    splitted = bearer_token.split(" ")
    if not len(splitted) == 2:
        return False
    if splitted[0] != "Bearer":
        return False
    return splitted[1]


def parse_jwt(access_token: str) -> Token:
    try:
        token = jwt.decode(access_token, options={"verify_signature": False})
        return Token(**token)
    except:
        raise TokenExpiredExcpetion(detail=["잘못된 토큰입니다."])


USER_CACHE_KEY = lambda x: f"GATEWAY:user:{x}:cached"


def has_user_cached(token: Token):
    from .caches import cache

    cached = cache.get(USER_CACHE_KEY(token.user_id))
    if cached:
        print("hit cached!@!#@$%#")
        return cached
    return False


def set_user_cache(user):
    from .caches import cache

    cache.set(USER_CACHE_KEY(user.pk), user)


def check_user_changed(user, token: Token):
    if user.nickname != token.nickname or user.username != token.username:
        user.nickname = token.nickname
        user.username = token.username
        user.save()
        user.refresh_from_db()


def create_user(user_class, token: Token):
    is_staff = "staff" in token.role
    user = user_class(
        nickname=token.nickname,
        username=token.username,
        id=token.user_id,
        is_staff=is_staff,
    )
    user.set_password(str(uuid4()))
    user.save()
    user.refresh_from_db()
    return user


def get_or_create_user(token: Token):
    from django.contrib.auth import get_user_model

    cached = has_user_cached(token)
    if cached:
        return cached
    User = get_user_model()
    user = User.objects.filter(id=token.user_id).first()
    if user:
        check_user_changed(user, token)
    else:
        user = create_user(User, token)
    set_user_cache(user)
    return user


def token_clarify(user: Optional[Token]):
    if not user:
        raise exceptions.NotAuthenticated
    return user


class InternalJWTAuthentication(authentication.BaseAuthentication):
    def check_exp(self, payload: Token, claim="exp", current_time=None):
        if current_time is None:
            current_time = aware_utcnow()
        try:
            claim_value = payload[claim]
        except:
            raise exceptions.NotAuthenticated
        claim_time = datetime_from_epoch(claim_value)
        if claim_time <= current_time:
            raise TokenExpiredExcpetion

    def authenticate(self, request: HttpRequest):
        jwt = get_jwt_token_from_dict(request.META)
        if not jwt:
            return (None, None)
        try:
            parsed = parse_jwt(jwt)
            try:
                self.check_exp(parsed)
                # user = get_or_create_user(parsed)
                return (None, parsed)
            except TokenExpiredExcpetion as e:
                raise e
            except:
                return (None, None)
        except TokenExpiredExcpetion as e:
            raise e
        except:
            return (None, None)
