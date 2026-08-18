import os
import sys
from pathlib import Path
from datetime import timedelta
import dj_database_url
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import cloudinary.api

# ─── Unfold Admin Compatibility Patch ─────────────────────────────────
from django.contrib.admin.templatetags import admin_list

original_node_init = admin_list.InclusionAdminNode.__init__

def tolerant_unfold_node_init(self, parser, token, *args, **kwargs):
    try:
        return original_node_init(self, parser, token, *args, **kwargs)
    except TypeError:
        return original_node_init(self, parser, *args, **kwargs)

admin_list.InclusionAdminNode.__init__ = tolerant_unfold_node_init

# ─── Load Environment ──────────────────────────────────────────────────
load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Security ────────────────────────────────────────────────────────
# ✅ Fallback for local development – but set a real SECRET_KEY in production!
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-fallback-key-change-me")
DEBUG = os.getenv("DEBUG", "False") == "True"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,django-ecommerce-backend-4u8q.onrender.com").split(",")

# ─── CORS ──────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    os.getenv("FRONTEND_URL", "https://northernmarket-pwa.onrender.com"),
]
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS + [
    "https://django-ecommerce-backend-4u8q.onrender.com",
]

# ─── Security Settings for Production ──────────────────────────────
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ─── REST Framework ──────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
}

# ─── Installed Apps ────────────────────────────────────────────────────
INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.filters',
    'cloudinary_storage',
    "django.contrib.admin",
    'cloudinary',
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    'django_filters',
    "myapp.apps.MyappConfig",
]

# ─── Middleware ──────────────────────────────────────────────────────
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    'whitenoise.middleware.WhiteNoiseMiddleware',
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "myproject.urls"

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

WSGI_APPLICATION = "myproject.wsgi.application"

# ─── Database ──────────────────────────────────────────────────────
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{os.path.join(BASE_DIR, 'db.sqlite3')}",
        conn_max_age=600
    )
}

# ─── Password Validation ──────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ─── Internationalization ──────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ─── Static & Media ────────────────────────────────────────────────
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ─── CRITICAL FIX: Define STATICFILES_STORAGE ──────────────────────
# This prevents Cloudinary's custom collectstatic from raising an
# AttributeError because it looks for this setting.
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# ─── STORAGES (Django 4.2+) ─────────────────────────────────────────
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# ─── WhiteNoise (serves static files in production) ──────────────────
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = DEBUG

# ─── Cloudinary ────────────────────────────────────────────────────
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", "dtll1o9u0"),
    api_key=os.getenv("CLOUDINARY_API_KEY", "387833656525477"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET", "AmTSvrVHKiLlN2ArzFgctGx_-70"),
    secure=True
)

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv("CLOUDINARY_CLOUD_NAME", "dtll1o9u0"),
    'API_KEY': os.getenv("CLOUDINARY_API_KEY", "387833656525477"),
    'API_SECRET': os.getenv("CLOUDINARY_API_SECRET", "AmTSvrVHKiLlN2ArzFgctGx_-70"),
}

# ─── Flutterwave ──────────────────────────────────────────────────
FLW_SECRET_KEY = os.getenv("FLUTTERWAVE_SECRET_KEY")
FLW_SECRET_HASH = os.getenv("FLUTTERWAVE_WEBHOOK_SECRET_HASH")

BASE_URL = os.getenv("BASE_URL", "https://django-ecommerce-backend-4u8q.onrender.com")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─── Logging ──────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO' if not DEBUG else 'DEBUG',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO' if not DEBUG else 'DEBUG',
            'propagate': False,
        },
    },
}
