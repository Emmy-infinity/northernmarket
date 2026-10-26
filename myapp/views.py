import uuid
import requests
from django.contrib.auth.models import User
from django.conf import settings
from django.core.cache import cache
from django.db.models import Max
from rest_framework import generics, viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
import django_filters

# ─── CLOUDINARY IMPORT ────────────────────────────────────────────────
import cloudinary.uploader # ✅ Added for safe uploads

from .models import (
    Note, SensorReading, Photo, StockMarketReading,
    Product, PaymentTransaction, SiteConfiguration,
    Category, Location, SearchQuery, ProductClick,
    UserProfile
)
from .serializers import (
    SensorReadingSerializer,
    UserSerializer,
    NoteSerializer,
    PhotoSerializer,
    ProductSerializer,
    PaymentTransactionSerializer,
    CategorySerializer,
    LocationSerializer,
    SearchQuerySerializer,
    ProductClickSerializer,
    UserProfileSerializer,
)

# ... (Keep parse_user_agent and ProductFilter exactly as they are) ...

# =====================================================================
# 📦 PRODUCT VIEWSET (UPDATED FOR SAFE CLOUDINARY UPLOADS)
# =====================================================================
class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ProductFilter
    search_fields = ['title', 'description']
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return ProductSerializer.optimize_for_list(
            Product.objects.all()
        ).order_by('-is_featured', '-created_at')

    def perform_create(self, serializer):
        product_instance = serializer.save(seller=self.request.user)
        uploaded_images = self.request.FILES.getlist('image')
        
        for image_file in uploaded_images:
            try:
                # ✅ EXPLICIT CLOUDINARY UPLOAD (Bypasses STORAGES issues)
                upload_result = cloudinary.uploader.upload(
                    image_file, 
                    folder="products" # Optional: organizes your Cloudinary media library
                )
                # Save the public_id to the database
                Photo.objects.create(
                    product=product_instance, 
                    image=upload_result['public_id']
                )
            except Exception as e:
                print(f"❌ Cloudinary upload failed: {e}")
                # Fallback: save locally if Cloudinary fails (won't render on Render, but prevents crash)
                Photo.objects.create(product=product_instance, image=image_file)

    @action(detail=False, methods=['get'], url_path='price-bounds', permission_classes=[AllowAny])
    def price_bounds(self, request):
        agg = Product.objects.aggregate(max_price=Max('price'))
        max_price = agg.get('max_price') or 0

        if max_price <= 0:
            ceiling = 5_000_000
        else:
            magnitude = 10 ** (len(str(int(max_price))) - 1)
            ceiling = int((int(max_price) // magnitude + 1) * magnitude)

        return Response({
            "min_price": 0,
            "max_price": ceiling,
            "actual_max": float(max_price),
        })

# ... (Keep CategoryViewSet, LocationViewSet, PhotoViewSet exactly as they are) ...
# ... (Keep SearchQueryCreateView, ProductClickCreateView exactly as they are) ...
# ... (Keep PaymentTransactionViewSet, pesapal_webhook exactly as they are) ...

# =====================================================================
# 📝 UTILITY & GENERAL VIEWS (FIXED PROFILE BUG)
# =====================================================================
class SiteConfigView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        config = SiteConfiguration.objects.first()
        fee = config.promotion_fee if config else 20000.00
        return Response({"promotion_fee": fee})


class NoteListCreate(generics.ListCreateAPIView):
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Note.objects.filter(author=self.request.user)

    def perform_create(self, serializer):
        if serializer.is_valid():
            serializer.save(author=self.request.user)


class NoteDelete(generics.DestroyAPIView):
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Note.objects.filter(author=self.request.user)


class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class CurrentUserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # ✅ FIXED: Changed from request.user.userprofile to request.user.profile
            profile = request.user.profile
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=404)


class ChartDataView2(APIView):
    # ... (Keep as is) ...
    pass

class ChartDataView(APIView):
    # ... (Keep as is) ...
    pass

class ImageListView(generics.ListAPIView):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
    permission_classes = [AllowAny]


class ImageUploadView(generics.CreateAPIView):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [AllowAny]
