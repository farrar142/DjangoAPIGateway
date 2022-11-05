from .models import User
from accounts.auth import AuthBearer
import os
import requests
from typing import Optional, List
from ninja import NinjaAPI, Schema, errors
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from dotenv import load_dotenv
load_dotenv()


class UserOut(Schema):
    user_id: int
    blog_id: int
    username: str
    email: str
    profile_url: Optional[str] = None


class UserLoginSchema(Schema):
    password: str
    email: str


class SimpleResponse(Schema):
    status: int
    message: str
    data: List[UserOut]


class UserSignUpForm(Schema):
    username: str
    email: str
    password: str


auth = NinjaAPI(urls_namespace="auth", csrf=False, version="1.01")
gateway = NinjaAPI(urls_namespace="gateway", csrf=False, version="1.02")
"""
로그인
회원가입
인증
"""


@gateway.get('{sub_urls}')
def sub_urls(request, sub_urls: str):
    return sub_urls


@auth.post('signin')
def signin(request, form: UserLoginSchema):
    user = User.objects.filter(email=form.email).first()
    if user and check_password(form.password, user.password):
        return {"token": User.offer_token(user.pk)}
    raise errors.AuthenticationError()


@auth.post('signup')
def signup(request, form: UserSignUpForm):
    is_username = User.objects.filter(username=form.username)
    is_email = User.objects.filter(email=form.email)
    if is_username.exists():
        return {
            "status": 1,
            "message": f"{form.username}이 이미 존재합니다",
            "data": []
        }
    elif is_email.exists():
        return {
            "status": 1,
            "message": f"{form.email}이 이미 존재합니다",
            "data": []
        }
    else:
        user = User.create(**form.dict())
        return {
            "status": 0,
            "message": f"환영합니다 {form.username}님",
            "data": []
        }


@auth.put('update', auth=AuthBearer())
def update(request, payload: UserSignUpForm):
    print(f"{request.auth=}")
    # for attr, value in payload.dict().items():
    #     setattr(employee, attr, value)
    return "hi"


@auth.get("kakao/login")
def Kakao_login(request):
    REST_API_KEY = os.environ.get("KAKAO__REST_API_KEY")
    REDIRECT_URI = os.environ.get("KAKAO__LOGIN_REDIRECT_URI")
    next_url = request.GET.get('next')
    kakao_auth_api = "https://kauth.kakao.com/oauth/authorize?"
    return {"url":
            f"{kakao_auth_api}client_id={REST_API_KEY}&redirect_uri={REDIRECT_URI}&response_type=code"
            }


class KakaoCallback(Schema):
    code: str


@auth.post("kakao/callback")
def Kakao_login_callback(request, form: KakaoCallback):
    code = form.code
    print(code)
    REST_API_KEY = os.environ.get("KAKAO__REST_API_KEY")
    REDIRECT_URI = os.environ.get("KAKAO__LOGIN_REDIRECT_URI")
    token_request = requests.get(
        f"https://kauth.kakao.com/oauth/token?grant_type=authorization_code&client_id={REST_API_KEY}&code={code}"
    )
    "&redirect_uri={REDIRECT_URI}"
    print(token_request)
    token_json = token_request.json()
    print(token_json)
    error = token_json.get("error", None)
    print(error)
    if error is not None:
        raise errors.HttpError(400, "bad request")

    access_token = token_json.get("access_token")

    profile_request = requests.get(
        "https://kapi.kakao.com/v2/user/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    profile_json = profile_request.json()

    id = profile_json.get("id")

    user = User.login_with_kakao(request, id)
    return {"token": user.make_token()}
