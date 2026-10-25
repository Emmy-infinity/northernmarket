import os
from pathlib import Path
from datetime import timedelta
import dj_database_url
from dotenv import load_dotenv

# ─── CLOUDINARY ──────────────────────────────────────────────────────
import cloudinary
import cloudinary.uploader
import cloudinary.api

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ─── SECURITY ────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-fallback-key-change-me")

DEBUG = os.getenv("DEBUG", "True") == "True" 

ALLOWED_HOSTS = [
    "localhost", 
    "127.0.0.1", 
    "django-ecommerce-backend-4u8q.onrender.com",
    ".onrender.com"
]

# ─── CORS & CSRF ────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://northernmarket-pwa.onrender.com",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept", "accept-encoding", "authorization",
    "content-type", "dnt", "origin", "user-agent",
    "x-csrftoken", "x-requested-with",
]

CSRF_TRUSTED_ORIGINS = [
    "https://*.onrender.com",      
    "https://*.trycloudflare.com", 
    "http://localhost:5173",
]

# ─── REST FRAMEWORK ─────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
}

# ─── INSTALLED APPS ──────────────────────────────────────────────────
INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.filters',
    # 'cloudinary_storage',  # ❌ REMOVED to fix collectstatic crash
    "django.contrib.admin",
    'cloudinary',
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "myapp",
]

# ─── MIDDLEWARE ──────────────────────────────────────────────────────
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

# ─── DATABASE ──────────────────────────────────────────────────────
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

# ─── STATIC & MEDIA ────────────────────────────────────────────────
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ─── CLOUDINARY CONFIGURATION ──────────────────────────────────────
# ✅ Explicitly load these from env for the serializer
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True
)

# ✅ STORAGES still points to the Cloudinary storage backend for media
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ─── PESAPAL CONFIGURATION ──────────────────────────────────────────
PESAPAL_CONSUMER_KEY = os.getenv("PESAPAL_CONSUMER_KEY")
PESAPAL_CONSUMER_SECRET = os.getenv("PESAPAL_CONSUMER_SECRET")
PESAPAL_IPN_ID = os.getenv("PESAPAL_IPN_ID")
PESAPAL_IPN_URL = os.getenv("PESAPAL_IPN_URL")
PESAPAL_CALLBACK_URL = os.getenv("PESAPAL_CALLBACK_URL", "https://northernmarket-pwa.onrender.com/tokens")
PESAPAL_ENV = os.getenv("PESAPAL_ENV", "sandbox")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
