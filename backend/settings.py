"""
Django settings for backend project (production-ready, Render-friendly).

Design goal: this file must NEVER raise at import time just because an
environment variable is missing. Missing config falls back to a safe local
default; anything that truly can't run without a secret (Razorpay calls)
fails at the moment it's used, with a clear error response — not at process
startup. This is what lets `manage.py check`, `migrate`, `collectstatic`
and even `gunicorn` boot successfully on Render before you've added a
single environment variable.
"""

from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
import os
import warnings

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv()


def env_bool(key, default=False):
    return os.getenv(key, str(default)).strip().lower() in ("1", "true", "yes", "on")


def env_list(key, default=""):
    value = os.getenv(key, default)
    return [item.strip() for item in value.split(",") if item.strip()]


# --- Secret key -------------------------------------------------------
# Falls back to a temporary insecure key so the process can still boot.
# Set DJANGO_SECRET_KEY in Render's environment for a real deployment.
_INSECURE_FALLBACK_KEY = "django-insecure-temporary-key-set-DJANGO_SECRET_KEY-in-env"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY") or _INSECURE_FALLBACK_KEY

if SECRET_KEY == _INSECURE_FALLBACK_KEY:
    warnings.warn(
        "DJANGO_SECRET_KEY is not set — using a temporary insecure key. "
        "Set DJANGO_SECRET_KEY in your environment before serving real traffic.",
        RuntimeWarning,
    )

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env_bool("DEBUG", False)

# Render auto-injects RENDER_EXTERNAL_HOSTNAME for every web service, so the
# app is reachable on its *.onrender.com URL even before you add any env
# vars yourself.
RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "" if not DEBUG else "localhost,127.0.0.1")
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173" if DEBUG else "",
)

CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "")
if RENDER_EXTERNAL_HOSTNAME:
    _render_origin = f"https://{RENDER_EXTERNAL_HOSTNAME}"
    if _render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(_render_origin)


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "rest_framework",
    "corsheaders",
    "payments",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'


# --- Database -----------------------------------------------------------
# Precedence: DATABASE_URL (Render's standard — set automatically when you
# attach a Postgres instance via render.yaml, or paste manually) takes
# priority since that's the idiomatic Render setup. Falls back to discrete
# POSTGRES_HOST/DB/USER/PASSWORD if you prefer to wire it up that way
# instead. With neither set, SQLite is used — no setup required at all,
# which is what keeps local dev and a bare Render deploy working with zero
# environment variables.

DATABASE_URL = os.getenv("DATABASE_URL")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=not DEBUG,
        )
    }
elif POSTGRES_HOST and POSTGRES_DB and POSTGRES_USER and POSTGRES_PASSWORD:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': POSTGRES_DB,
            'USER': POSTGRES_USER,
            'PASSWORD': POSTGRES_PASSWORD,
            'HOST': POSTGRES_HOST,
            'PORT': os.getenv("POSTGRES_PORT", "5432"),
            'CONN_MAX_AGE': 600,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# --- Static & media files ------------------------------------------------
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if not DEBUG
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --- Razorpay -------------------------------------------------------------
# Never crash on missing keys — RAZORPAY_CONFIGURED / _WEBHOOK_CONFIGURED
# let the affected views return a clean 503 "not configured" response
# instead of a stack trace when a key is missing.
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")

RAZORPAY_CONFIGURED = bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)
RAZORPAY_WEBHOOK_CONFIGURED = bool(RAZORPAY_WEBHOOK_SECRET)

if not DEBUG and not RAZORPAY_CONFIGURED:
    warnings.warn(
        "RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET are not set — payment "
        "endpoints will return a 503 until they're configured.",
        RuntimeWarning,
    )


REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
}


# --- Production security hardening (only enforced when DEBUG=False) ------
if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "payments": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
