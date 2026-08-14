# Open your local project ──> myapp/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 🚀 INITIALIZE THE AUTOMATED REST ROUTER
router = DefaultRouter()
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'photos', views.PhotoViewSet, basename='photo')
router.register(r'payments', views.PaymentTransactionViewSet, basename='payment')

urlpatterns = [
    # 🌟 1. STANDALONE SECURE FLUTTERWAVE WEBHOOK
    path('payments/webhook/', views.flutterwave_payment_webhook, name='flw_webhook'),
    
    # 🌟 2. PRESERVED LEGACY & SENSOR ENDPOINTS
    path("notes/", views.NoteListCreate.as_view(), name="note-list"),
    path("notes/delete/<int:pk>/", views.NoteDelete.as_view(), name="note-delete"),
    path('sensor_reading/', views.ChartDataView.as_view(), name="sensor-reading"),
    path('charts/stocks/', views.ChartDataView2.as_view(), name='stock-chart'),

    # 🌟 3. AUTOMATED VIEWSET NETWORKS (Appended cleanly at the bottom)
    # This automatically includes paths for your products, payments, and photos!
    path('', include(router.urls)),
]
