import uuid
import requests
import xml.etree.ElementTree as ET
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
# 💳 3. YO! PAYMENTS UGANDA MOBILE MONEY BILLING ENGINE
# =====================================================================
class PaymentTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentTransactionSerializer

    def get_queryset(self):
        return PaymentTransaction.objects.select_related('product') \
                                         .order_by('-created_at')

    def create(self, request, *args, **kwargs):
        """
        Initiates a mobile money payment via Yo! Payments (Uganda).
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

        # Check that required settings are present (only for production)
        yo_username = getattr(settings, 'YO_API_USERNAME', None)
        yo_password = getattr(settings, 'YO_API_PASSWORD', None)
        
        # In sandbox mode, we can skip credential check
        if not settings.DEBUG and (not yo_username or not yo_password):
            return Response(
                {"error": "Yo! Payments API credentials not configured."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        fixed_fee = 20000.00  # Promotional fee in UGX

        try:
            product = Product.objects.get(id=product_id, seller=request.user)
        except Product.DoesNotExist:
            return Response({"error": "Product not found or you don't own it."}, status=404)

        # Generate a unique transaction reference
        unique_ref = f"GULU-YOPAY-{uuid.uuid4().hex[:8].upper()}"

        # Create a pending transaction record
        transaction = PaymentTransaction.objects.create(
            product=product,
            amount=fixed_fee,
            phone_number=phone,
            tx_ref=unique_ref,
            status='PENDING'
        )

        # ================================================================
        # 🔧 SANDBOX MODE: Use mock endpoint when DEBUG=True
        # ================================================================
        if settings.DEBUG:
            # Use the mock endpoint for testing without real credentials
            yo_url = f"{settings.BASE_URL}/mock-yo-payments/"
            xml_payload = f"""<?xml version="1.0" encoding="UTF-8"?>
<AutoCreate>
    <Request>
        <APIUsername>mock_username</APIUsername>
        <APIPassword>mock_password</APIPassword>
        <Method>acdepositfunds</Method>
        <NonBlocking>TRUE</NonBlocking>
        <Account>{phone}</Account>
        <Amount>{int(fixed_fee)}</Amount>
        <Currency>UGX</Currency>
        <ExternalReference>{unique_ref}</ExternalReference>
        <Narrative>B2B Promo Fee for Product #{product.id}</Narrative>
    </Request>
</AutoCreate>"""
            print(f"🧪 SANDBOX MODE: Using mock Yo! Payments endpoint")
        else:
            # Production: Use real Yo! Payments endpoints
            yo_url = "https://paymentsapi1.yo.co.ug/ybs/task.php"
            narrative = f"B2B Promo Fee for Product #{product.id}"
            xml_payload = f"""<?xml version="1.0" encoding="UTF-8"?>
<AutoCreate>
    <Request>
        <APIUsername>{yo_username}</APIUsername>
        <APIPassword>{yo_password}</APIPassword>
        <Method>acdepositfunds</Method>
        <NonBlocking>TRUE</NonBlocking>
        <Account>{phone}</Account>
        <Amount>{int(fixed_fee)}</Amount>
        <Currency>UGX</Currency>
        <ExternalReference>{unique_ref}</ExternalReference>
        <Narrative>{narrative}</Narrative>
    </Request>
</AutoCreate>"""

        headers = {"Content-Type": "text/xml"}

        try:
            response = requests.post(yo_url, data=xml_payload, headers=headers, timeout=20)
            
            # For mock endpoint, response will be XML
            # For real endpoint, response will also be XML
            if response.status_code == 200:
                try:
                    root = ET.fromstring(response.text)
                    status_element = root.find('.//Status')
                    if status_element is not None and status_element.text == 'OK':
                        print(f"✅ Payment initiated successfully for {phone} ({network})")
                        transaction.save()
                    else:
                        error_msg = root.find('.//Message')
                        error_text = error_msg.text if error_msg is not None else "Unknown error"
                        transaction.status = 'FAILED'
                        transaction.save()
                        return Response(
                            {"error": f"Yo! Payments initiation failed: {error_text}"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except ET.ParseError:
                    if "OK" in response.text or "SUCCEEDED" in response.text:
                        print(f"✅ Payment initiated successfully for {phone} ({network})")
                        transaction.save()
                    else:
                        transaction.status = 'FAILED'
                        transaction.save()
                        return Response(
                            {"error": f"Yo! Payments initiation failed: {response.text[:100]}"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
            else:
                transaction.status = 'FAILED'
                transaction.save()
                return Response(
                    {"error": f"Yo! Payments API returned status {response.status_code}"},
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
# 📡 YO! PAYMENTS INSTANT PAYMENT NOTIFICATION (IPN) WEBHOOK
# =====================================================================
@api_view(['POST'])
@permission_classes([AllowAny])
def yo_payments_webhook(request):
    """
    Listens for Yo! Payments IPN callbacks when a subscriber completes payment.
    Handles both form-encoded and JSON payloads.
    """
    # Handle form-encoded data (Yo! Payments default)
    if request.content_type == 'application/x-www-form-urlencoded':
        payload = request.POST.dict()
    else:
        payload = request.data

    # Extract transaction reference (handles multiple naming conventions)
    tx_ref = (
        payload.get('external_reference') or 
        payload.get('ExternalReference') or 
        payload.get('private_transaction_reference') or 
        payload.get('transaction_reference')
    )
    
    # Extract status
    status_flag = (
        payload.get('status') or 
        payload.get('transaction_status') or 
        payload.get('Status') or
        payload.get('TransactionStatus')
    )

    print(f"📡 Yo! Payments IPN received: tx_ref={tx_ref}, status={status_flag}")

    if tx_ref and status_flag:
        if status_flag.upper() in ['SUCCEEDED', 'OK', 'SUCCESS']:
            try:
                tx = PaymentTransaction.objects.get(tx_ref=tx_ref)
                tx.status = 'SUCCESSFUL'
                tx.save()
                
                # Mark product as featured
                prod = tx.product
                prod.is_featured = True
                prod.save()
                print(f"✅ Transaction {tx_ref} marked as successful.")
            except PaymentTransaction.DoesNotExist:
                print(f"⚠️ Transaction {tx_ref} not found.")

    return Response({"status": "acknowledged"}, status=200)


# =====================================================================
# 🧪 MOCK YO! PAYMENTS SANDBOX (For testing without credentials)
# =====================================================================
@api_view(['POST'])
@permission_classes([AllowAny])
def mock_yo_payments(request):
    """
    MOCK Yo! Payments Sandbox – simulates the real Yo! Payments API.
    Only active when DEBUG=True.
    """
    if not settings.DEBUG:
        return Response({"error": "Mock endpoint only available in DEBUG mode"}, status=404)
    
    # Parse XML payload
    xml_data = request.body.decode('utf-8')
    print(f"🧪 Mock Yo! Payments received: {xml_data[:200]}...")
    
    # Extract external reference from XML
    import re
    match = re.search(r'<ExternalReference>(.*?)</ExternalReference>', xml_data)
    tx_ref = match.group(1) if match else "MOCK-REF-001"
    
    # Return success response
    response_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<AutoCreate>
    <Response>
        <Status>OK</Status>
        <StatusCode>1</StatusCode>
        <TransactionStatus>PENDING</TransactionStatus>
        <TransactionReference>MOCK-TX-{uuid.uuid4().hex[:8]}</TransactionReference>
        <ExternalReference>{tx_ref}</ExternalReference>
        <Message>Transaction initiated successfully (MOCK)</Message>
    </Response>
</AutoCreate>"""
    
    return Response(response_xml, content_type='text/xml', status=200)


# =====================================================================
# 🔧 TEST PAYMENT CONFIRMATION (Manual webhook simulation)
# =====================================================================
class TestPaymentView(APIView):
    """
    MANUAL TEST ENDPOINT: Simulates a successful Yo! Payments transaction.
    Only use in development/sandbox!
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not settings.DEBUG:
            return Response({"error": "Test endpoint only available in DEBUG mode"}, status=404)
        
        tx_ref = request.data.get('tx_ref')
        
        if not tx_ref:
            return Response({"error": "tx_ref required"}, status=400)
        
        try:
            tx = PaymentTransaction.objects.get(tx_ref=tx_ref)
            tx.status = 'SUCCESSFUL'
            tx.save()
            
            prod = tx.product
            prod.is_featured = True
            prod.save()
            
            return Response({
                "status": "success",
                "message": f"Transaction {tx_ref} marked as successful",
                "product": prod.title,
                "is_featured": prod.is_featured
            })
            
        except PaymentTransaction.DoesNotExist:
            return Response({"error": "Transaction not found"}, status=404)


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
