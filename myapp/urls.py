from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'photos', views.PhotoViewSet, basename='photo')
router.register(r'payments', views.PaymentTransactionViewSet, basename='payment')

urlpatterns = [
    # ─── FLUTTERWAVE WEBHOOK ──────────────────────────────────────────
    path('payments/webhook/', views.flutterwave_webhook, name='flw_webhook'),
    path('site-config/', views.SiteConfigView.as_view(), name='site-config'),

    # ─── MOCK FLUTTERWAVE (DEBUG only) ────────────────────────────────
    path('mock-flutterwave/', views.mock_flutterwave, name='mock_flutterwave'),

    # ─── TEST PAYMENT CONFIRMATION (DEBUG only) ──────────────────────
    path('test-payment/', views.TestPaymentView.as_view(), name='test-payment'),

    # ─── LEGACY ENDPOINTS ──────────────────────────────────────────────
    path("notes/", views.NoteListCreate.as_view(), name="note-list"),
    path("notes/delete/<int:pk>/", views.NoteDelete.as_view(), name="note-delete"),
    path('sensor_reading/', views.ChartDataView.as_view(), name="sensor-reading"),
    path('charts/stocks/', views.ChartDataView2.as_view(), name='stock-chart'),
    path('images/', views.ImageListView.as_view(), name='image-list'),
    path('upload/', views.ImageUploadView.as_view(), name='image-upload'),
    path('register/', views.CreateUserView.as_view(), name='register'),

    # ─── VIEWSET ROUTES ────────────────────────────────────────────────
    path('', include(router.urls)),
]
