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
# 🏪 1. PRIMARY PLATFORM MARKETPLACE STOCK VIEWSETS
# =====================================================================
class ProductViewSet(viewsets.ModelViewSet):
    """
    Optimised queryset with select_related and prefetch_related to avoid N+1 queries.
    """
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ProductFilter
    search_fields = ['title', 'description']
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return Product.objects.select_related('seller') \
                              .prefetch_related('photos') \
                              .order_by('-is_featured', '-created_at')

    def perform_create(self, serializer):
        product_instance = serializer.save(seller=self.request.user)

        uploaded_images = self.request.FILES.getlist('image')
        if uploaded_images:
            print(f"📡 Backend Multi-Media Interceptor: Processing {len(uploaded_images)} diagnostic assets simultaneously...")
            for image_file in uploaded_images:
                Photo.objects.create(
                    product=product_instance,
                    image=image_file
                )
            print("🎉 Success - All multi-photo presentation frames saved and anchored into the database schema!")


# =====================================================================
# 📸 2. MULTI-IMAGE ASSETS FILE ROUTER VIEWSETS (URL ROUTER TARGET)
# =====================================================================
class PhotoViewSet(viewsets.ModelViewSet):
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
# 💳 3. SECURED UGANDA MOBILE MONEY BILLING ENGINE (MTN & AIRTEL)
# =====================================================================
class PaymentTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentTransactionSerializer

    def get_queryset(self):
        return PaymentTransaction.objects.select_related('product') \
                                         .order_by('-created_at')

    def create(self, request, *args, **kwargs):
        """
        Initiates a mobile money payment via Flutterwave (Uganda).
        Expects: product, phone_number, network (MTN or AIRTEL)
        """
        payload = request.data
        product_id = payload.get('product')
        phone = payload.get('phone_number')
        network = payload.get('network', 'MTN').upper()  # "MTN" or "AIRTEL"

        # Validate network
        if network not in ['MTN', 'AIRTEL']:
            return Response(
                {"error": "Network must be 'MTN' or 'AIRTEL'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        fixed_fee = 20000.00  # Your promotional fee

        try:
            product = Product.objects.get(id=product_id, seller=request.user)
        except Product.DoesNotExist:
            return Response({"error": "Product not found or you don't own it."}, status=404)

        # Generate a unique transaction reference
        unique_ref = f"GULU-B2B-PROMO-{uuid.uuid4().hex[:8].upper()}"

        # Create a pending transaction record
        transaction = PaymentTransaction.objects.create(
            product=product,
            amount=fixed_fee,
            phone_number=phone,
            tx_ref=unique_ref,
            status='PENDING'
        )

        # Flutterwave configuration
        # Use sandbox URL if in debug/development, else production
        if settings.DEBUG:
            flw_base_url = "https://api.flutterwave.com/v3"
        else:
            flw_base_url = "https://api.flutterwave.com/v3"

        flw_url = f"{flw_base_url}/charges?type=mobile_money_uganda"

        headers = {
            "Authorization": f"Bearer {settings.FLW_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        flw_payload = {
            "phone_number": phone,
            "network": network,
            "amount": str(fixed_fee),
            "currency": "UGX",
            "email": request.user.email,
            "tx_ref": unique_ref,
            "fullname": f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
        }

        try:
            flw_response = requests.post(flw_url, json=flw_payload, headers=headers, timeout=15)
            flw_data = flw_response.json()

            # Check if the charge was successful
            if flw_response.status_code == 200 and flw_data.get("status") == "success":
                # The charge was initiated; Flutterwave sends STK push
                # The transaction remains PENDING until webhook confirms completion
                print(f"✅ Mobile Money STK Push sent for {phone} ({network})")
                # Optionally store the Flutterwave transaction ID if returned
                transaction.transaction_id = flw_data.get("data", {}).get("id")
                transaction.save()
            else:
                # Payment initiation failed
                transaction.status = 'FAILED'
                transaction.save()
                error_msg = flw_data.get("message", "Unknown error")
                return Response(
                    {"error": f"Payment initiation failed: {error_msg}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except requests.exceptions.RequestException as e:
            # Network or timeout error
            transaction.status = 'FAILED'
            transaction.save()
            return Response(
                {"error": f"Payment gateway error: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # Return the transaction data (excluding sensitive details)
        serializer = self.get_serializer(transaction)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# =====================================================================
# 📡 FLUTTERWAVE WEBHOOK (for final status updates)
# =====================================================================
@api_view(['POST'])
@permission_classes([AllowAny])
def flutterwave_payment_webhook(request):
    """
    Listens for Flutterwave's background notifications when a user completes payment.
    Verifies using the Verif-Hash header.
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

                # Optionally mark the product as featured (if that's your business logic)
                prod = tx.product
                prod.is_featured = True
                prod.save()
            except PaymentTransaction.DoesNotExist:
                # Log or ignore – the transaction may have been deleted
                pass

    return Response({"status": "acknowledged"}, status=200)


# =====================================================================
# 📝 4. TRADER NOTE AND SECURITY ACCESS EXTENSION CHANNELS
# =====================================================================
class NoteListCreate(generics.ListCreateAPIView):
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Note.objects.filter(author=self.request.user)

    def perform_create(self, serializer):
        if serializer.is_valid():
            serializer.save(author=self.request.user)
        else:
            print(serializer.errors)


class NoteDelete(generics.DestroyAPIView):
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Note.objects.filter(author=self.request.user)


class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


# =====================================================================
# 📊 5. LOGISTICS PLOTLY GRAPH READINGS & HARDWARE SENSORS LOGS
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


class ImageListView(generics.ListAPIView):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
    permission_classes = [AllowAny]


class ImageUploadView(generics.CreateAPIView):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [AllowAny]
