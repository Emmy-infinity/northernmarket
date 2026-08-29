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
    # ─── 1. WEBHOOKS (🔄 CHANGED: Mapped to Pesapal IPN listener view) ──
    path('payments/webhook/', views.pesapal_webhook, name='pesapal_webhook'),

    # ─── 1b. ANALYTICS TRACKING ENDPOINTS (NEW) ──────────────────────
    path('track-search/', views.SearchQueryCreateView.as_view(), name='track-search'),
    path('track-click/', views.ProductClickCreateView.as_view(), name='track-click'),

    # ─── 2. MOCK & TEST ENDPOINTS (Development-only) ──────────────────
    # Note: Pesapal uses sandbox URLs built-in (cybqa.pesapal.com), 
    # so custom mock views are usually bypassed unless you want a local testing harness.
    #path('test-payment/', views.TestPaymentView.as_view(), name='test-payment'),

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
