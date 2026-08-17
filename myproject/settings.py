import os
from pathlib import Path
from datetime import timedelta
import sys
import dj_database_url
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import cloudinary.api


import sys
import types
from django.contrib.admin.templatetags import admin_list

# Django 6.1 compatibility patch for Unfold admin
original_node_init = admin_list.InclusionAdminNode.__init__

def tolerant_unfold_node_init(self, parser, token, *args, **kwargs):
    try:
        return original_node_init(self, parser, token, *args, **kwargs)
    except TypeError:
        return original_node_init(self, parser, *args, **kwargs)

admin_list.InclusionAdminNode.__init__ = tolerant_unfold_node_init
print("======== ✅ GLOBAL ADMINISTRATIVE TEMPLATE PARSERS LOCKED CONCURRENT ========")

# =====================================================================
# LOAD ENVIRONMENT (keep hardcoded fallbacks for rapid testing)
# =====================================================================
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ─── SECURITY (keep as-is for rapid testing) ────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-fallback-key-change-me")
DEBUG = True
ALLOWED_HOSTS = ["*"]

# ─── CORS ──────────────────────────────────────────────────────────────
# 🔥 FIX: Added your production frontend URL to the allowed origins
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
     "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "https://northernmarket-pwa.onrender.com",   # ✅ YOUR PRODUCTION FRONTEND
]

# 🔥 Optional: Allow all origins temporarily (uncomment if needed)
# CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept", "accept-encoding", "authorization",
    "content-type", "dnt", "origin", "user-agent",
    "x-csrftoken", "x-requested-with",
]

# 🔥 Force CORS headers for all responses (guarantees the header is present)
class ForceCorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Allow your frontend origin (or use "*" for testing)
        response["Access-Control-Allow-Origin"] = "https://northernmarket-pwa.onrender.com"
        response["Access-Control-Allow-Headers"] = "accept, authorization, content-type"
        response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        return response

# ─── REST FRAMEWORK ────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=20),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=2),
}

# ─── INSTALLED APPS ────────────────────────────────────────────────────
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

# ─── MIDDLEWARE ────────────────────────────────────────────────────────
# 🔥 Insert our ForceCorsMiddleware at the very top to ensure CORS headers
MIDDLEWARE = [
    "myproject.settings.ForceCorsMiddleware",   # ✅ Force CORS (must be first)
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

# ─── DATABASE ──────────────────────────────────────────────────────────
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{os.path.join(BASE_DIR, 'db.sqlite3')}",
        conn_max_age=600
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ─── STATIC & MEDIA ────────────────────────────────────────────────────
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ─── STORAGE (Hardcoded Cloudinary – keep as-is for rapid testing) ──
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
STATICFILES_STORAGE = 'cloudinary_storage.storage.StaticCloudinaryStorage'

STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ─── CLOUDINARY CONFIG (Hardcoded – keep for rapid testing) ──────────
cloudinary.config(
    cloud_name = 'dtll1o9u0',
    api_key = '387833656525477',
    api_secret = 'AmTSvrVHKiLlN2ArzFgctGx_-70',
    secure = True
)

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'dtll1o9u0',
    'API_KEY': '387833656525477',
    'API_SECRET': 'AmTSvrVHKiLlN2ArzFgctGx_-70'
}

# ─── FLUTTERWAVE (optional) ───────────────────────────────────────────
FLW_SECRET_KEY = os.environ.get("FLUTTERWAVE_SECRET_KEY")
FLW_SECRET_HASH = os.environ.get("FLUTTERWAVE_WEBHOOK_SECRET_HASH")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
