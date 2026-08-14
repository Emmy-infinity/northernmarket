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

# Django 6.1 changed InclusionAdminNode to take 'parser' and 'token' parameters natively.
# We explicitly override the node's initializer to handle both older 5.x and newer 6.x signatures seamlessly.
original_node_init = admin_list.InclusionAdminNode.__init__

def tolerant_unfold_node_init(self, parser, token, *args, **kwargs):
    try:
        # 1. Attempt the clean, standard Django 6.x compilation track
        return original_node_init(self, parser, token, *args, **kwargs)
    except TypeError:
        # 2. Fallback gracefully if running against older cached library states
        return original_node_init(self, parser, *args, **kwargs)

# Force inject the safety valve directly into the core administrative template class
admin_list.InclusionAdminNode.__init__ = tolerant_unfold_node_init
print("======== ✅ GLOBAL ADMINISTRATIVE TEMPLATE PARSERS LOCKED CONCURRENT ========")

# =====================================================================
# REST OF YOUR EXISTING SETTINGS PARAMETERS (DO NOT CHANGE BELOW)
# =====================================================================

# Load environment keys
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Security Parameters
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-fallback-key-change-me")
DEBUG = True

ALLOWED_HOSTS = ["*"]

# REST Framework Ecosystem
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

# 🌟 INSTALLED APPLICATIONS (COMPLIANT OVERRIDES)
INSTALLED_APPS = [
    'unfold',                  # Placed first to override administrative layout templates
    'unfold.contrib.filters',  # Modern filtering modules
    'cloudinary_storage',      # Asset pipeline hook (loads before contrib.admin)
    "django.contrib.admin",
    'cloudinary',              # Core layout package tracking
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    'django_filters',
    
    # 🌟 TARGET CHOSEN SINGLE APP ROUTE ENTRY ONLY:
    "myapp.apps.MyappConfig",  # Forces Django to execute emergency SQL syncs!
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    'whitenoise.middleware.WhiteNoiseMiddleware', # Processes compressed static admin styles
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

# Database Configuration (Supports Render DATABASE_URL automatically)
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

# Static & Media Base URL Mappings





STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# =====================================================================
# 🌟 THE COMPATIBILITY BRIDGE: SATISFIES OLD PACKAGES & NEW DJANGO
# =====================================================================
# 1. Old strings required by django-cloudinary-storage to prevent crashes
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
STATICFILES_STORAGE = 'cloudinary_storage.storage.StaticCloudinaryStorage'

# 2. Modern configuration dictionary block required by Django 5.x+
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

FLW_SECRET_KEY = os.environ.get("FLUTTERWAVE_SECRET_KEY")
FLW_SECRET_HASH = os.environ.get("FLUTTERWAVE_WEBHOOK_SECRET_HASH")





# Cloudinary Framework Authentication
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

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CORS Gateway Whitelist Origins
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]
