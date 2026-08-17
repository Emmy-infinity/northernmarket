import uuid
import requests
import json
from django.contrib.auth.models import User
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
# 🎛️ FILTERS
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
# 🏪 PRODUCT VIEWSET
# =====================================================================
class ProductViewSet(viewsets.ModelViewSet):
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
        for image_file in uploaded_images:
            Photo.objects.create(product=product_instance, image=image_file)


# =====================================================================
# 📸 PHOTO VIEWSET
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
# 💳 FLUTTERWAVE MOBILE MONEY PAYMENT (UGANDA)
# =====================================================================
class PaymentTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentTransactionSerializer

    def get_queryset(self):
        return PaymentTransaction.objects.select_related('product') \
                                         .order_by('-created_at')

    def create(self, request, *args, **kwargs):
        """
        Initiate Flutterwave mobile money charge (MTN/AIRTEL Uganda).
        """
        payload = request.data
        product_id = payload.get('product')
        phone = payload.get('phone_number')
        network = payload.get('network', 'MTN').upper()

        if network not in ['MTN', 'AIRTEL']:
            return Response(
                {"error": "Network must be 'MTN' or 'AIRTEL'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check for API key
        flw_secret = getattr(settings, 'FLW_SECRET_KEY', None)
        if not flw_secret and not settings.DEBUG:
            return Response(
                {"error": "Flutterwave secret key not configured."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        fixed_fee = 20000.00

        try:
            product = Product.objects.get(id=product_id, seller=request.user)
        except Product.DoesNotExist:
            return Response({"error": "Product not found or you don't own it."}, status=404)

        unique_ref = f"FLW-UG-{uuid.uuid4().hex[:8].upper()}"
        transaction = PaymentTransaction.objects.create(
            product=product,
            amount=fixed_fee,
            phone_number=phone,
            tx_ref=unique_ref,
            status='PENDING'
        )

        # ----------------------------------------------------------------
        # 🔧 SANDBOX MODE: Use mock when DEBUG=True
        # ----------------------------------------------------------------
        if settings.DEBUG:
            flw_url = f"{settings.BASE_URL}/mock-flutterwave/"
            # We'll use a mock payload; the mock endpoint will ignore it.
            flw_payload = {
                "phone_number": phone,
                "network": network,
                "amount": str(fixed_fee),
                "currency": "UGX",
                "email": request.user.email,
                "tx_ref": unique_ref,
                "fullname": request.user.get_full_name() or request.user.username,
                "country": "UG"
            }
            headers = {"Content-Type": "application/json"}
            print(f"🧪 SANDBOX: Using mock Flutterwave endpoint")
        else:
            # Production: real Flutterwave
            flw_url = "https://api.flutterwave.com/v3/charges?type=mobile_money_uganda"
            headers = {
                "Authorization": f"Bearer {flw_secret}",
                "Content-Type": "application/json"
            }
            flw_payload = {
                "phone_number": phone,
                "network": network,
                "amount": str(fixed_fee),
                "currency": "UGX",
                "email": request.user.email,
                "tx_ref": unique_ref,
                "fullname": request.user.get_full_name() or request.user.username,
                "country": "UG"
            }

        try:
            response = requests.post(flw_url, json=flw_payload, headers=headers, timeout=15)
            data = response.json()

            if response.status_code in [200, 201] and data.get("status") == "success":
                print(f"✅ Flutterwave charge initiated for {phone} ({network})")
                transaction.transaction_id = data.get("data", {}).get("id")
                transaction.save()
            else:
                transaction.status = 'FAILED'
                transaction.save()
                error_msg = data.get("message", "Unknown error")
                return Response(
                    {"error": f"Payment initiation failed: {error_msg}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except requests.exceptions.RequestException as e:
            transaction.status = 'FAILED'
            transaction.save()
            return Response(
                {"error": f"Payment gateway error: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            transaction.status = 'FAILED'
            transaction.save()
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        serializer = self.get_serializer(transaction)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# =====================================================================
# 📡 FLUTTERWAVE WEBHOOK (Charge Completed)
# =====================================================================
@api_view(['POST'])
@permission_classes([AllowAny])
def flutterwave_webhook(request):
    """
    Flutterwave webhook for charge.completed events.
    Verifies signature using Verif-Hash header.
    """
    # Verify signature
    signature = request.headers.get('Verif-Hash')
    expected = getattr(settings, 'FLW_SECRET_HASH', None)
    if not signature or signature != expected:
        print("⚠️ Invalid or missing Verif-Hash")
        return Response({"error": "Unauthorised"}, status=401)

    payload = request.data
    event = payload.get('event')

    if event == "charge.completed":
        data = payload.get('data', {})
        tx_ref = data.get('tx_ref')
        status_flag = data.get('status')

        if status_flag == "successful" and tx_ref:
            try:
                tx = PaymentTransaction.objects.get(tx_ref=tx_ref)
                tx.status = 'SUCCESSFUL'
                tx.save()
                # Mark product as featured
                tx.product.is_featured = True
                tx.product.save()
                print(f"✅ Transaction {tx_ref} marked successful.")
            except PaymentTransaction.DoesNotExist:
                print(f"⚠️ Transaction {tx_ref} not found.")
    else:
        print(f"ℹ️ Ignored event: {event}")

    return Response({"status": "acknowledged"}, status=200)


# =====================================================================
# 🧪 MOCK FLUTTERWAVE SANDBOX (for testing without real key)
# =====================================================================
@api_view(['POST'])
@permission_classes([AllowAny])
def mock_flutterwave(request):
    """
    Mock Flutterwave charge endpoint – always returns success.
    Only available when DEBUG=True.
    """
    if not settings.DEBUG:
        return Response({"error": "Mock only in DEBUG"}, status=404)

    payload = request.data
    tx_ref = payload.get('tx_ref', 'MOCK-REF-001')
    print(f"🧪 Mock Flutterwave called for tx_ref: {tx_ref}")

    return Response({
        "status": "success",
        "message": "Charge initiated (MOCK)",
        "data": {
            "id": 123456,
            "tx_ref": tx_ref,
            "flw_ref": "FLW-MOCK-001",
            "amount": payload.get('amount'),
            "charged_amount": payload.get('amount'),
            "status": "pending"
        }
    }, status=200)


# =====================================================================
# 🔧 TEST PAYMENT CONFIRMATION (Manual webhook simulation)
# =====================================================================
class TestPaymentView(APIView):
    """
    Manually mark a transaction as successful (for testing).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not settings.DEBUG:
            return Response({"error": "Test endpoint only in DEBUG"}, status=404)

        tx_ref = request.data.get('tx_ref')
        if not tx_ref:
            return Response({"error": "tx_ref required"}, status=400)

        try:
            tx = PaymentTransaction.objects.get(tx_ref=tx_ref)
            tx.status = 'SUCCESSFUL'
            tx.save()
            tx.product.is_featured = True
            tx.product.save()
            return Response({
                "status": "success",
                "message": f"Transaction {tx_ref} marked successful"
            })
        except PaymentTransaction.DoesNotExist:
            return Response({"error": "Transaction not found"}, status=404)


# =====================================================================
# 📝 NOTE, USER, CHART, IMAGE VIEWS (unchanged – included for completeness)
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


class ChartDataView2(APIView):
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
    def get(self, request):
        readings = SensorReading.objects.all().order_by('timestamp')
        x = [r.timestamp.strftime('%Y-%m-%d %H:%M:%S') for r in readings]
        y = [r.value for r in readings]
        chart_data = {
            "data": [{"x": x, "y": y, "type": "scatter", "mode": "lines+markers", "name": "Sensor"}],
            "layout": {"title": "Sensor Data", "xaxis": {"title": "Time"}, "yaxis": {"title": "Value"}}
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
