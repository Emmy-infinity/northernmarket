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
    # 🌟 1. STANDALONE SECURE FLUTTERWAVE WEBHOOK (Takes absolute priority)
    # Target live link: POST https://your-domain.com
    path('payments/webhook/', views.flutterwave_payment_webhook, name='flw_webhook'),
    
    # 🌟 2. PRESERVED LEGACY & SENSOR ENDPOINTS (YOUR ORIGINAL CODE)
    path("notes/", views.NoteListCreate.as_view(), name="note-list"),
    path("notes/delete/<int:pk>/", views.NoteDelete.as_view(), name="note-delete"),
    path('sensor_reading/', views.ChartDataView.as_view(), name="sensor-reading"),
    path('upload/', views.ImageUploadView.as_view(), name='image-upload'),
    path('images/', views.ImageListView.as_view(), name='image-list'),
    
    # Keeping your stock data view mapped alongside the sensor views
    path('charts/stocks/', views.ChartDataView2.as_view(), name='stock-chart'),

    # 🌟 3. AUTOMATED VIEWSET NETWORKS (Appended cleanly at the bottom)
    # GET /api/products/  --> Lists premium top 200 items first
    # POST /api/payments/ --> Registers a PENDING billing ledger row
    path('', include(router.urls)),
]
