import datetime
import pytz
from django.utils import timezone
from django.db import models
from django.db.models import QuerySet
from django.apps import apps
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import check_password, make_password
from jose import jwt

from base.settings import SECRET_KEY
# Create your models here.


def get_default_nickname(instance):
    return instance.username


class User(AbstractUser):
    """
    패스워드는 상속
    """
    class Meta:
        db_table = "accounts_user"

    class ProviderTypeCodeChoices(models.TextChoices):
        LOCAL = "local", "로컬"
        KAKAO = "kakao", "카카오"

    TIMEZONES = tuple(zip(pytz.all_timezones, pytz.all_timezones))
    timezone = models.CharField(
        max_length=32, choices=TIMEZONES, default="Asia/Seoul")

    username = models.CharField(
        '유저이름',
        max_length=20,
        help_text='20자 이하로 작성해주세요 @/./+/-/_ 를 사용 할 수 있습니다..',
        unique=True
    )
    nickname = models.CharField(
        '닉네임',
        max_length=20,
        help_text='20자 이하로 작성해주세요 @/./+/-/_ 를 사용 할 수 있습니다..',
        default="nickname"
    )
    email = models.EmailField('이메일')
    profile_url = models.CharField(max_length=256, null=True, blank=True)

    provider_type_code = models.CharField(
        '프로바이더 타입코드', max_length=20, choices=ProviderTypeCodeChoices.choices, default=ProviderTypeCodeChoices.LOCAL)
    provider_accounts_id = models.PositiveIntegerField('프로바이더 회원번호', default=0)

    @classmethod
    def create(cls, username: str, email: str, password: str):
        user: User = User.objects.create(
            username=username, email=email, password=make_password(password), nickname=username)
        return user

    def get_timezone(self):
        return pytz.timezone(self.timezone)

    def check_password(self, password: str):
        return check_password(password, self.password)

    @classmethod
    def expired_token(cls, pk):
        payload = {
            "id": pk,
            "exp": datetime.datetime.now()+datetime.timedelta(days=-2, hours=-9),
            'iat': datetime.datetime.now()+datetime.timedelta(hours=-9),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        return token

    @staticmethod
    def offer_token(pk):
        payload = {
            "id": pk,
            "exp": datetime.datetime.now()+datetime.timedelta(days=2, hours=-9),
            'iat': datetime.datetime.now()+datetime.timedelta(hours=-9),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        return token

    def make_token(self):
        payload = {
            "id": self.pk,
            "exp": datetime.datetime.now()+datetime.timedelta(days=2, hours=-9),
            'iat': datetime.datetime.now()+datetime.timedelta(hours=-9),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        return token

    @staticmethod
    def login_with_kakao(request, provider_accounts_id):
        provider_type_code = User.ProviderTypeCodeChoices.KAKAO
        qs: QuerySet = User.objects.filter(provider_type_code=provider_type_code,
                                           provider_accounts_id=provider_accounts_id)
        qs_first = qs.first()
        if not qs_first:
            username = provider_type_code + "__" + str(provider_accounts_id)
            name = provider_type_code + "__" + str(provider_accounts_id)
            email = ""
            password = ""
            user: User = User.objects.create(username=username, email=email, password=password,
                                             nickname=name,
                                             provider_type_code=provider_type_code,
                                             provider_accounts_id=provider_accounts_id)
            return user
        else:
            return qs_first
