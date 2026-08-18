from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'myapp'

# =====================================================================
# 🚀 ROUTER REGISTRATION
# =====================================================================
router = DefaultRouter()
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'photos', views.PhotoViewSet, basename='photo')
router.register(r'payments', views.PaymentTransactionViewSet, basename='payment')
router.register(r'categories', views.CategoryViewSet, basename='category')   # ✅ NEW
router.register(r'locations', views.LocationViewSet, basename='location')     # ✅ NEW

# =====================================================================
# 🌐 URL PATTERNS
# =====================================================================
urlpatterns = [
    # ─── FLUTTERWAVE WEBHOOK ──────────────────────────────────────────
    # Register this URL in your Flutterwave dashboard:
    # https://your-domain.com/api/payments/webhook/
    path('payments/webhook/', views.flutterwave_webhook, name='flw_webhook'),

    # ─── SANDBOX & TEST ENDPOINTS ─────────────────────────────────────
    path('mock-flutterwave/', views.mock_flutterwave, name='mock_flutterwave'),
    path('test-payment/', views.TestPaymentView.as_view(), name='test-payment'),

    # ─── SITE CONFIGURATION ───────────────────────────────────────────
    # Returns the admin‑controlled promotion fee for the frontend
    path('site-config/', views.SiteConfigView.as_view(), name='site-config'),

    # ─── LEGACY & SENSOR ENDPOINTS ────────────────────────────────────
    path("notes/", views.NoteListCreate.as_view(), name="note-list"),
    path("notes/delete/<int:pk>/", views.NoteDelete.as_view(), name="note-delete"),
    path('sensor_reading/', views.ChartDataView.as_view(), name="sensor-reading"),
    path('charts/stocks/', views.ChartDataView2.as_view(), name='stock-chart'),

    # ─── IMAGE ENDPOINTS ──────────────────────────────────────────────
    path('images/', views.ImageListView.as_view(), name='image-list'),
    path('upload/', views.ImageUploadView.as_view(), name='image-upload'),

    # ─── USER REGISTRATION ────────────────────────────────────────────
    path('register/', views.CreateUserView.as_view(), name='register'),

    # ─── VIEWSET ROUTES ────────────────────────────────────────────────
    # Products, Photos, Payments, Categories, Locations
    path('', include(router.urls)),
]
