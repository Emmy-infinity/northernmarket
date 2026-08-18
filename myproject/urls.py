from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.views.generic import RedirectView
from myapp.views import CreateUserView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# =====================================================================
# 🔗 URL PATTERNS (Ordered by specificity)
# =====================================================================
urlpatterns = [
    # ─── ROOT REDIRECT ──────────────────────────────────────────────────
    # Redirects base URL (/) to the API root (/api/)
    path('', RedirectView.as_view(url='/api/', permanent=False)),

    # ─── DJANGO ADMIN ──────────────────────────────────────────────────
    path("admin/", admin.site.urls),

    # ─── AUTHENTICATION & USER MANAGEMENT ────────────────────────────
    # User registration (custom view)
    path("api/user/register/", CreateUserView.as_view(), name="register"),
    # JWT token endpoints
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # DRF browsable API authentication
    path("api-auth/", include("rest_framework.urls")),

    # ─── APP ROUTER (Products, Payments, Categories, etc.) ──────────
    # Must come after specific paths so it doesn't accidentally
    # override /api/token/ or /api/user/register/
    path("api/", include("myapp.urls")),
]

# =====================================================================
# 📁 MEDIA FILE SERVING (Development only)
# =====================================================================
# 🚀 OPTIMIZATION: Only serve media files via Django in DEBUG mode.
# In production (DEBUG=False), media files should be served by your
# web server (nginx, S3, Cloudinary, etc.) – this avoids unnecessary
# overhead and potential security warnings.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
