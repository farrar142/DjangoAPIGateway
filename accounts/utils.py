from datetime import datetime
from typing import TypedDict, Any
from base.settings import SECRET_KEY
from accounts.models import User
from jose import jwt


class Token(TypedDict):
    id: int
    exp: datetime
    iat: datetime


def parse_token(str_token: str) -> Token:
    token: Any = jwt.decode(str_token, SECRET_KEY, algorithms="HS256")
    return token


def get_user_from_token(parsed_token: Token):
    user: User = User.objects.filter(pk=parsed_token["id"]).get()
    return user
