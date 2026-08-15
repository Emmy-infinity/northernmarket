from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 🌟 THE ABSOLUTE RESOLUTION: Explicitly declare the router asset mapping grid cleanly 
# to ensure Django's urlconf compiler resolves viewset references instantly!
router = DefaultRouter()
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'photos', views.PhotoViewSet, basename='photo')
router.register(r'payments', views.PaymentTransactionViewSet, basename='payment')

urlpatterns = [
    # 📡 ViewSet API Unified Router Core Tunnel
    path("", include(router.urls)),
    
    # 📝 Legacy note tracking structures & logistics chart data ports
    path("notes/", views.NoteListCreate.as_view(), name="note-list"),
    path("notes/delete/<int:pk>/", views.NoteDelete.as_view(), name="note-delete"),
    path('sensor_reading/', views.ChartDataView.as_view()),
    path('chart_data_two/', views.ChartDataView2.as_view()),
    
    # 📸 Cloudinary single file endpoints paths
    path('upload/', views.ImageUploadView.as_view(), name='image-upload'),
    path('images/', views.ImageListView.as_view(), name='image-list'),
    
    # 💳 Automated background verification gateway webhook portal
    path('webhook/flutterwave/', views.flutterwave_payment_webhook, name='flw-webhook'),
]
