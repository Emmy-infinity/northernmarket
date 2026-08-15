import uuid
import requests
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from rest_framework import generics, viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
import django_filters

# Unified local model and serializer imports
from .models import Note, SensorReading, Photo, StockMarketReading, Product, PaymentTransaction
from .serializers import (
    SensorReadingSerializer, 
    UserSerializer, 
    NoteSerializer, 
    PhotoSerializer,
    ProductSerializer,
    PaymentTransactionSerializer
)

# =====================================================================
# 🎛️ MULTIVARIABLE FILTERS SCHEMAS
# =====================================================================
class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr='lte')
    condition = django_filters.CharFilter(field_name="condition", lookup_expr='exact')
    item_location = django_filters.CharFilter(field_name="item_location", lookup_expr='exact')

    class Meta:
        model = Product
        fields = ['min_price', 'max_price', 'condition', 'item_location']


# =====================================================================
# 🏪 1. B2B MARKETPLACE ENGINE VIEWSETS (CORRECTED MULTI-PHOTO SAVE)
# =====================================================================
class ProductViewSet(viewsets.ModelViewSet):
    """
    Highly optimized database engine. Handles multi-variable processing, range slices, 
    and text search strings directly via indexed SQL operations.
    """
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ProductFilter
    search_fields = ['title', 'description']
    
    # 🌟 parser_classes use the properties natively
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return Product.objects.all().order_by('-is_featured', '-created_at')

    def perform_create(self, serializer):
        # 1. First, save the master product row bound to the logged-in JWT profile context
        product_instance = serializer.save(seller=self.request.user)
        
        # 2. 🌟 MULTI-IMAGE FRONTEND RESOLUTION: Intercepts the file array queue cleanly
        uploaded_images = self.request.FILES.getlist('image')
        
        if uploaded_images:
            print(f"📡 Backend Multi-Media Interceptor: Processing {len(uploaded_images)} diagnostic assets simultaneously...")
            
            # Loop through the files array list matrix and save every entry mapped directly to our product foreign key relation
            for image_file in uploaded_images:
                Photo.objects.create(
                    product=product_instance,
                    image=image_file
                )
            print("🎉 Success - All multi-photo presentation frames saved and anchored into the database schema!")


class PhotoViewSet(viewsets.ModelViewSet):
    """
    Handles uploading images via React binaries and linking them cleanly to specific products.
    """
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def perform_create(self, serializer):
        raw_product_id = self.request.data.get('product')
        if raw_product_id:
            try:
                product_id = int(raw_product_id)
                product = Product.objects.get(id=product_id)
                serializer.save(product=product)
            except (ValueError, Product.DoesNotExist):
                serializer.save()
        else:
            serializer.save()
# =====================================================================
# 💳 2. MOBILE MONEY BILLING ENGINE VIEWSETS
# =====================================================================
class PaymentTransactionViewSet(viewsets.ModelViewSet):
    queryset = PaymentTransaction.objects.all().order_by('-created_at')
    serializer_class = PaymentTransactionSerializer

    def create(self, request, *args, **kwargs):
        payload = request.data
        product_id = payload.get('product')
        phone = payload.get('phone_number') 
        fixed_fee = 20000.00                
        
        try:
            product = Product.objects.get(id=product_id, seller=request.user)
            unique_ref = f"GULU-B2B-PROMO-{uuid.uuid4().hex[:8].upper()}"
            
            transaction = PaymentTransaction.objects.create(
                product=product, amount=fixed_fee, phone_number=phone,
                tx_ref=unique_ref, status='PENDING'
            )
            
            flw_url = "https://flutterwave.com"
            flw_headers = {
                "Authorization": f"Bearer {settings.FLW_SECRET_KEY}",
                "Content-Type": "application/json"
            }
            flw_payload = {
                "tx_ref": unique_ref,
                "amount": str(fixed_fee),
                "currency": "UGX",
                "phone_number": phone,
                "email": request.user.email,
                "fullname": f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
            }
            
            try:
                flw_response = requests.post(flw_url, json=flw_payload, headers=flw_headers, timeout=15)
                flw_data = flw_response.json()
                
                if flw_response.status_code == 200 and flw_data.get("status") == "success":
                    print(f"📡 STK Push notification fired successfully via Flutterwave for {phone}")
                else:
                    transaction.status = 'FAILED'
                    transaction.save()
                    return Response({"error": flw_data.get("message", "Aggregator payment prompt rejected.")}, status=400)
                    
            except requests.exceptions.RequestException:
                transaction.status = 'FAILED'
                transaction.save()
                return Response({"error": "Payment aggregator network timeout. Please retry."}, status=503)

            serializer = self.get_serializer(transaction)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Product.DoesNotExist:
            return Response({"error": "Product assignment validation failed."}, status=404)


@api_view(['POST'])
@permission_classes([AllowAny]) 
def flutterwave_payment_webhook(request):
    """
    Listens for Flutterwave's background notification when a user inputs their phone PIN.
    """
    signature = request.headers.get('Verif-Hash')
    if not signature or signature != settings.FLW_SECRET_HASH:
        return Response({"error": "Unauthorised signature handshake verification failed."}, status=401)
        
    payload = request.data
    event = payload.get('event')
    
    if event == "charge.completed":
        data = payload.get('data', {})
        tx_ref = data.get('tx_ref')
        status_flag = data.get('status') 
        
        if status_flag == "successful":
            try:
                tx = PaymentTransaction.objects.get(tx_ref=tx_ref)
                tx.status = 'SUCCESSFUL'
                tx.save()
                
                prod = tx.product
                prod.is_featured = True
                prod.save()
            except PaymentTransaction.DoesNotExist:
                pass
                
    return Response({"status": "acknowledged"}, status=200)


# =====================================================================
# 📝 3. LEGACY NOTE MANAGEMENT TRACKS
# =====================================================================
class NoteListCreate(generics.ListCreateAPIView):
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Note.objects.filter(author=user)

    def perform_create(self, serializer):
        if serializer.is_valid():
            serializer.save(author=self.request.user)
        else:
            print(serializer.errors)


class NoteDelete(generics.DestroyAPIView):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Note.objects.filter(author=user)


class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


# =====================================================================
# 📊 4. LOGISTICS CHART & REPAIR DATA READINGS
# =====================================================================
class ChartDataView2(APIView):
    def get(self, request):
        readings = StockMarketReading.objects.all().order_by('timestamp')
        x = [r.timestamp.strftime('%Y-%m-%d %H:%M:%S') for r in readings]
        y1 = [r.value1 for r in readings]
        y2 = [r.value2 for r in readings]
        chart_data = {
            "data": [
                {
                    "x": x,
                    "y": y1,
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": "Stock Value 1",
                },
                {
                    "x": x,
                    "y": y2,
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": "Stock Value 2",
                }
            ],
            "layout": {
                "title": "Stock Market Reading",
                "xaxis": {"title": "Time"},
                "yaxis": {"title": "Value"},
            }
        }
        return Response(chart_data)


class ChartDataView(APIView):
    def get(self, request):
        readings = SensorReading.objects.all().order_by('timestamp')
        x = [r.timestamp.strftime('%Y-%m-%d %H:%M:%S') for r in readings]
        y = [r.value for r in readings]

        chart_data = {
            "data": [
                {
                    "x": x,
                    "y": y,
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": "Sensor",
                }
            ],
            "layout": {
                "title": "Sensor Data",
                "xaxis": {"title": "Time"},
                "yaxis": {"title": "Value"},
            }
        }
        return Response(chart_data)


# =====================================================================
# 📸 5. CLOUDINARY DIRECT COMPRESSION CHANNELS
# =====================================================================
class ImageListView(generics.ListAPIView):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
    permission_classes = [AllowAny]


class ImageUploadView(generics.CreateAPIView):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
    parser_classes = (MultiPartParser, FormParser)  
    permission_classes = [AllowAny]















