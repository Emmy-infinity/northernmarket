# Open your local project ──> myapp/views.py
import uuid
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import generics, viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

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
# 🌟 1. CORE MARKETPLACE API VIEWSETS (MODERN ROUTERS)
# =====================================================================

from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from .models import Product
from .serializers import ProductSerializer

class ProductFilter(django_filters.FilterSet):
    # Map range slider variables safely to database evaluation parameters
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr='lte')
    
    # Match exact string representations on indexed fields
    condition = django_filters.CharFilter(field_name="condition", lookup_expr='exact')
    item_location = django_filters.CharFilter(field_name="item_location", lookup_expr='exact')

    class Meta:
        model = Product
        fields = ['min_price', 'max_price', 'condition', 'item_location']


class ProductViewSet(viewsets.ModelViewSet):
    """
    Highly optimized database engine. Handles multi-variable processing, range slices, 
    and text search strings directly via indexed SQL operations.
    """
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    # Attach our high-performance query parsing pipelines
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ProductFilter
    
    # Triggers optimized text search matching indexes across string properties
    search_fields = ['title', 'description']

    def get_queryset(self):
        # Enforces paid featured items to load first, sorted by the newest arrival timestamp,
        # fetching any foreign user details concurrently using select_related to prevent N+1 overhead queries.
        return Product.objects.all().select_related('seller').order_by('-is_featured', '-created_at')
class PhotoViewSet(viewsets.ModelViewSet):
    """
    Handles uploading images via React binaries and linking them cleanly to specific products.
    """
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        product_id = self.request.data.get('product')
        if product_id:
            try:
                product = Product.objects.get(id=product_id)
                serializer.save(product=product)
            except Product.DoesNotExist:
                serializer.save()
        else:
            serializer.save()


# Open your local project ──> myapp/views.py
import requests
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Product, PaymentTransaction
from .serializers import PaymentTransactionSerializer

class PaymentTransactionViewSet(viewsets.ModelViewSet):
    queryset = PaymentTransaction.objects.all().order_by('-created_at')
    serializer_class = PaymentTransactionSerializer

    def create(self, request, *args, **kwargs):
        payload = request.data
        product_id = payload.get('product')
        phone = payload.get('phone_number') # Expected format from React: 256770000000
        fixed_fee = 20000.00                # 20,000 UGX flat premium listing fee
        
        try:
            product = Product.objects.get(id=product_id, seller=request.user)
            unique_ref = f"GULU-B2B-PROMO-{uuid.uuid4().hex[:8].upper()}"
            
            # 1. Lock the local database ledger row safely
            transaction = PaymentTransaction.objects.create(
                product=product, amount=fixed_fee, phone_number=phone,
                tx_ref=unique_ref, status='PENDING'
            )
            
            # 2. Structure the outward Flutterwave request payload
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
            
            # 3. Dispatch the payload request directly to Flutterwave over HTTPS
            try:
                flw_response = requests.post(flw_url, json=flw_payload, headers=flw_headers, timeout=15)
                flw_data = flw_response.json()
                
                # If Flutterwave successfully accepts the prompt request
                if flw_response.status_code == 200 and flw_data.get("status") == "success":
                    print(f"📡 STK Push notification fired successfully via Flutterwave for {phone}")
                else:
                    # Update local state tracking if Flutterwave instantly rejects the number
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

# Add to the bottom of myapp/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.utils import timezone
from datetime import timedelta

@api_view(['POST'])
@permission_classes([AllowAny]) # Flutterwave must be allowed public access to ping this route
def flutterwave_payment_webhook(request):
    """
    Listens for Flutterwave's background notification when a user inputs their phone PIN.
    """
    # 🌟 SECURITY GUARD: Validate the signature token hash to verify this is genuinely Flutterwave
    signature = request.headers.get('Verif-Hash')
    if not signature or signature != settings.FLW_SECRET_HASH:
        return Response({"error": "Unauthorised signature handshake verification failed."}, status=401)
        
    payload = request.data
    event = payload.get('event')
    
    # We only care when a transaction officially concludes
    if event == "charge.completed":
        data = payload.get('data', {})
        tx_ref = data.get('tx_ref')
        status_flag = data.get('status') # 'successful' or 'failed'
        flw_id = data.get('id')
        
        try:
            transaction = PaymentTransaction.objects.get(tx_ref=tx_ref)
            
            # Guard loop: Only process if we haven't already marked it successful
            if transaction.status == 'PENDING':
                if status_flag == "successful":
                    # 1. Update the ledger row permanently
                    transaction.status = 'SUCCESSFUL'
                    transaction.transaction_id = str(flw_id)
                    transaction.save()
                    
                    # 2. Promote the product visibility inside the top 200 feed array
                    product = transaction.product
                    product.is_featured = True
                    product.featured_until = timezone.now() + timedelta(days=30) # Active for 30 days
                    product.save()
                    
                    print(f"🎉 Success! Product #{product.id} successfully promoted to Top 200.")
                else:
                    transaction.status = 'FAILED'
                    transaction.save()
                    
            return Response({"status": "acknowledged"}, status=200)
            
        except PaymentTransaction.DoesNotExist:
            return Response({"error": "Transaction trace reference ledger matching code not found."}, status=404)
            
    return Response({"status": "ignored"}, status=200)




# =====================================================================
# 📝 2. LEGACY GENERICS & AUTHENTICATION ENDPOINTS
# =====================================================================

class CreateUserView(generics.CreateAPIView):
    """Handles frontend public user account registration."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class NoteListCreate(generics.ListCreateAPIView):
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Note.objects.filter(author=self.request.user)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class NoteDelete(generics.DestroyAPIView):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Note.objects.filter(author=self.request.user)


# =====================================================================
# 📊 3. ANALYTICS & SENSOR GRAPH DATA ENDPOINTS
# =====================================================================

class ChartDataView2(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        readings = StockMarketReading.objects.all().order_by('timestamp')
        x = [r.timestamp.strftime('%Y-%m-%d %H:%M:%S') for r in readings]
        y1 = [r.value1 for r in readings]
        y2 = [r.value2 for r in readings]
        chart_data = {
            "data": [
                {"x": x, "y": y1, "type": "scatter", "mode": "lines+markers", "name": "Stock Value 1"},
                {"x": x, "y": y2, "type": "scatter", "mode": "lines+markers", "name": "Stock Value 2"}
            ],
            "layout": {"title": "Stock Market Reading", "xaxis": {"title": "Time"}, "yaxis": {"title": "Value"}}
        }
        return Response(chart_data)


class ChartDataView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        readings = SensorReading.objects.all().order_by('timestamp')
        x = [r.timestamp.strftime('%Y-%m-%d %H:%M:%S') for r in readings]
        y = [r.value for r in readings]
        chart_data = {
            "data": [{"x": x, "y": y, "type": "scatter", "mode": "lines+markers", "name": "Sensor"}],
            "layout": {"title": "Sensor Data", "xaxis": {"title": "Time"}, "yaxis": {"title": "Value"}}
        }
        return Response(chart_data)
