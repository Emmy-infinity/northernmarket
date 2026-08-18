from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'myapp'

# =====================================================================
# 📡 ROUTER REGISTRATION (REST API Endpoints)
# =====================================================================
router = DefaultRouter()
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'photos', views.PhotoViewSet, basename='photo')
router.register(r'payments', views.PaymentTransactionViewSet, basename='payment')
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'locations', views.LocationViewSet, basename='location')

# =====================================================================
# 🔗 URL PATTERNS (Ordered by priority: Webhooks → Utilities → Router)
# =====================================================================
urlpatterns = [
    # ─── 1. WEBHOOKS (Must be externally accessible & high-priority) ──
    path('payments/webhook/', views.flutterwave_webhook, name='flw_webhook'),

    # ─── 2. MOCK & TEST ENDPOINTS (Development-only) ──────────────────
    path('mock-flutterwave/', views.mock_flutterwave, name='mock_flutterwave'),
    path('test-payment/', views.TestPaymentView.as_view(), name='test-payment'),

    # ─── 3. CONFIGURATION & UTILITY ENDPOINTS ──────────────────────────
    path('site-config/', views.SiteConfigView.as_view(), name='site-config'),

    # ─── 4. NOTE MANAGEMENT ─────────────────────────────────────────────
    path("notes/", views.NoteListCreate.as_view(), name="note-list"),
    path("notes/delete/<int:pk>/", views.NoteDelete.as_view(), name="note-delete"),

    # ─── 5. CHART DATA ENDPOINTS ───────────────────────────────────────
    path('sensor_reading/', views.ChartDataView.as_view(), name="sensor-reading"),
    path('charts/stocks/', views.ChartDataView2.as_view(), name='stock-chart'),

    # ─── 6. IMAGE UPLOAD & LISTING ─────────────────────────────────────
    path('images/', views.ImageListView.as_view(), name='image-list'),
    path('upload/', views.ImageUploadView.as_view(), name='image-upload'),

    # ─── 7. USER REGISTRATION ──────────────────────────────────────────
    path('register/', views.CreateUserView.as_view(), name='register'),

    # ─── 8. ROUTER (Must be last to avoid overriding specific paths) ──
    path('', include(router.urls)),
]
