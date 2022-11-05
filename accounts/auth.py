from ninja.security import HttpBearer
from django.contrib.auth.models import AnonymousUser
from .utils import parse_token, get_user_from_token
from base.settings import SECRET_KEY


class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        try:
            a = parse_token(token)
            user = get_user_from_token(a)
            return user
            # return a
        except:
            return AnonymousUser()
