"""
Django settings for base project.

Generated by 'django-admin startproject' using Django 4.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
import os

from glob import glob
from pathlib import Path
from dotenv import load_dotenv
from common_module.settings import SECRET_KEY, CHALLENGE_IMAGE_SIZE

load_dotenv()

GDAL_LIBRARY_PATH = glob("/usr/lib/libgdal.so.*")[0]
GEOS_LIBRARY_PATH = glob("/usr/lib/libgeos_c.so.*")[0]
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = SECRET_KEY
# SECRET_KEY = 'django-insecure-g)*y0n*^0k*xy+e2k7i#zf7ymw_(2@kfz5dci&vi11y-=w&%=q'

# SECURITY WARNING: don't run with debug turned on in production!
IS_DEBUG = os.getenv("DEBUG", None)
DEBUG = True if IS_DEBUG is not None else False

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "apigateway",
    "rest_framework",
    "common_module",
]

MIDDLEWARE = [
    "common_module.middleware.time_checking_middleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "base.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "base.wsgi.application"
ASGI_APPLICATION = "base.asgi.application"


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DB_ENGINE = os.getenv("DB_ENGINE", "django.db.backends.mysql")
DB_OPTIONS = (
    {}
    if DB_ENGINE.find("postgis")
    else {
        "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        "charset": "utf8mb4",
        "use_unicode": True,
    }
)
DATABASES = {
    "default": {
        "ENGINE": DB_ENGINE,
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
        "OPTIONS": DB_OPTIONS,
        "TEST": {"NAME": "auth_test", "MIRROR": "default"},
    },
}


REDIS_HOST = os.getenv("REDIS_HOST", None)

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(REDIS_HOST)],
        },
    },
    "notify": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(REDIS_HOST)],
        },
    },
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

CORS_ALLOW_ALL_ORIGINS = True

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
ALLOWED_HOSTS = ["*"]
STATIC_ROOT = "static/"

LOGIN_URL = "/gateway/"
