import uuid
import requests
import json
from django.contrib.auth.models import User
from django.conf import settings
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

# ─── IMPORTS ──────────────────────────────────────────────────────────
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

# =====================================================================
# 🔍 USER-AGENT PARSING HELPER (for analytics)
# =====================================================================
def parse_user_agent(user_agent_str):
    """Simple parser to extract device type, browser, and OS from User-Agent string."""
    ua = user_agent_str.lower()

    # Device type
    if 'mobile' in ua or 'android' in ua or 'iphone' in ua:
        device = 'Mobile'
    elif 'tablet' in ua or 'ipad' in ua:
        device = 'Tablet'
    else:
        device = 'Desktop'

    # Browser
    if 'edg/' in ua:
        browser = 'Edge'
    elif 'chrome' in ua and 'chromium' in ua:
        browser = 'Chrome'
    elif 'firefox' in ua:
        browser = 'Firefox'
    elif 'safari' in ua and 'chrome' not in ua:
        browser = 'Safari'
    elif 'opera' in ua or 'opr/' in ua:
        browser = 'Opera'
    else:
        browser = 'Other'

    # OS
    if 'windows' in ua:
        os = 'Windows'
    elif 'android' in ua:
        os = 'Android'
    elif 'iphone' in ua or 'ipad' in ua or 'ios' in ua:
        os = 'iOS'
    elif 'mac os' in ua or 'macintosh' in ua:
        os = 'macOS'
    elif 'linux' in ua:
        os = 'Linux'
    else:
        os = 'Other'

    return device, browser, os


# =====================================================================
# 🎛️ FILTERS
# =====================================================================
class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr='lte')
    condition = django_filters.CharFilter(field_name="condition", lookup_expr='exact')

    category = django_filters.ModelChoiceFilter(
        field_name='category',
        queryset=Category.objects.filter(is_active=True),
        to_field_name='slug'
    )
    location = django_filters.ModelChoiceFilter(
        field_name='location',
        queryset=Location.objects.filter(is_active=True),
        to_field_name='code'
    )

    class Meta:
        model = Product
        fields = ['min_price', 'max_price', 'condition', 'category', 'location']


# =====================================================================
# 📦 PRODUCT VIEWSET
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


# =====================================================================
# 🗂️ CATEGORIES & LOCATIONS
# =====================================================================
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class LocationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Location.objects.filter(is_active=True)
    serializer_class = LocationSerializer
    permission_classes = [AllowAny]


# =====================================================================
# 🖼️ PHOTOS
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
# 🔍 SEARCH QUERY & PRODUCT CLICK TRACKING (ANALYTICS)
# =====================================================================
class SearchQueryCreateView(generics.CreateAPIView):
    queryset = SearchQuery.objects.all()
    serializer_class = SearchQuerySerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user_agent = self.request.META.get('HTTP_USER_AGENT', '')
        device, browser, os = parse_user_agent(user_agent)
        serializer.save(
            user=self.request.user if self.request.user.is_authenticated else None,
            session_key=self.request.data.get('session_key'),
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=user_agent,
            device_type=device,
            browser=browser,
            os=os,
        )


class ProductClickCreateView(generics.CreateAPIView):
    queryset = ProductClick.objects.all()
    serializer_class = ProductClickSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user_agent = self.request.META.get('HTTP_USER_AGENT', '')
        device, browser, os = parse_user_agent(user_agent)
        serializer.save(
            user=self.request.user if self.request.user.is_authenticated else None,
            session_key=self.request.data.get('session_key'),
            ip_address=self.request.META.get('REMOTE_ADDR'),
            referer=self.request.META.get('HTTP_REFERER'),
            user_agent=user_agent,
            device_type=device,
            browser=browser,
            os=os,
        )


# =====================================================================
# 💳 PESAPAL PAYMENT TRANSACTION VIEWSET (FIXED FOR PRODUCTION)
# =====================================================================
class PaymentTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentTransactionSerializer

    def get_queryset(self):
        return PaymentTransactionSerializer.optimize_queryset(
            PaymentTransaction.objects.all()
        ).order_by('-created_at')

    def _get_pesapal_token(self, consumer_key, consumer_secret, base_url):
        auth_url = f"{base_url}/api/Auth/RequestToken"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        payload = {
            "consumer_key": consumer_key,
            "consumer_secret": consumer_secret
        }
        response = requests.post(auth_url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json().get("token")
        return None

    def create(self, request, *args, **kwargs):
        payload = request.data
        product_id = payload.get('product')
        phone = payload.get('phone_number')

        consumer_key = getattr(settings, 'PESAPAL_CONSUMER_KEY', None)
        consumer_secret = getattr(settings, 'PESAPAL_CONSUMER_SECRET', None)
        ipn_id = getattr(settings, 'PESAPAL_IPN_ID', None)
        
        # ✅ Use the React callback URL from settings
        callback_url = getattr(settings, 'PESAPAL_CALLBACK_URL', 'https://northernmarket-pwa.onrender.com/tokens')

        if not consumer_key or not consumer_secret:
            return Response(
                {"error": "Pesapal credentials not configured."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            config = SiteConfiguration.objects.first()
            fee = config.promotion_fee if config else 20000.00
        except Exception:
            fee = 20000.00

        try:
            product = Product.objects.select_related('seller').get(id=product_id, seller=request.user)
        except Product.DoesNotExist:
            return Response({"error": "Product not found or you don't own it."}, status=404)

        unique_ref = f"PP-UG-{uuid.uuid4().hex[:8].upper()}"
        transaction = PaymentTransaction.objects.create(
            product=product,
            amount=fee,
            phone_number=phone,
            tx_ref=unique_ref,
            status='PENDING'
        )

        # ✅ Determine environment based on PESAPAL_ENV
        if getattr(settings, 'PESAPAL_ENV', 'sandbox') == "sandbox":
            base_url = "https://cybqa.pesapal.com/pesapalv3"
            print(f"🧪 SANDBOX: Using Pesapal Demo Environment")
        else:
            base_url = "https://pay.pesapal.com/v3"

        token = self._get_pesapal_token(consumer_key, consumer_secret, base_url)
        if not token:
            transaction.status = 'FAILED'
            transaction.save()
            return Response({"error": "Failed to authenticate with Pesapal API."}, status=502)

        order_url = f"{base_url}/api/Transactions/SubmitOrderRequest"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        order_payload = {
            "id": unique_ref,
            "currency": "UGX",
            "amount": float(fee),
            "description": f"Promotion fee for product: {product.title[:50]}",
            "callback_url": callback_url,
            "notification_id": ipn_id,
            "billing_address": {
                "email_address": request.user.email or "client@example.com",
                "phone_number": phone,
                "first_name": request.user.first_name or "Customer",
                "last_name": request.user.last_name or "User",
                "country_code": "UG"
            }
        }

        try:
            response = requests.post(order_url, json=order_payload, headers=headers, timeout=60)
            data = response.json()

            if response.status_code in [200, 201] and "redirect_url" in data:
                print(f"✅ Pesapal order created for Ref: {unique_ref}")
                transaction.transaction_id = data.get("order_tracking_id")
                transaction.save()

                serializer = self.get_serializer(transaction)
                res_data = serializer.data
                res_data["redirect_url"] = data.get("redirect_url")
                return Response(res_data, status=status.HTTP_201_CREATED)
            else:
                transaction.status = 'FAILED'
                transaction.save()
                error_msg = data.get("message", "Unknown error from gateway")
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


# =====================================================================
# 📡 PESAPAL IPN WEBHOOK (FIXED RESPONSE)
# =====================================================================
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def pesapal_webhook(request):
    order_tracking_id = request.GET.get('OrderTrackingId') or request.data.get('OrderTrackingId')
    merchant_reference = request.GET.get('OrderMerchantReference') or request.data.get('OrderMerchantReference')

    if not order_tracking_id or not merchant_reference:
        return Response({"error": "Missing tracking parameters"}, status=400)

    consumer_key = getattr(settings, 'PESAPAL_CONSUMER_KEY', None)
    consumer_secret = getattr(settings, 'PESAPAL_CONSUMER_SECRET', None)
    
    # ✅ Determine environment based on PESAPAL_ENV, not DEBUG
    if getattr(settings, 'PESAPAL_ENV', 'sandbox') == "sandbox":
        base_url = "https://cybqa.pesapal.com/pesapalv3"
    else:
        base_url = "https://pay.pesapal.com/v3"

    temp_vs = PaymentTransactionViewSet()
    token = temp_vs._get_pesapal_token(consumer_key, consumer_secret, base_url)

    if token:
        status_url = f"{base_url}/api/Transactions/GetTransactionStatus?orderTrackingId={order_tracking_id}"
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        status_resp = requests.get(status_url, headers=headers, timeout=30)

        if status_resp.status_code == 200:
            status_data = status_resp.json()
            payment_status = status_data.get('payment_status_description')

            try:
                tx = PaymentTransaction.objects.get(tx_ref=merchant_reference)
                if payment_status == "Completed":
                    tx.status = 'SUCCESSFUL'
                    tx.save()
                    tx.product.is_featured = True
                    tx.product.save()
                    print(f"✅ Pesapal Transaction {merchant_reference} marked successful.")
                elif payment_status == "Failed":
                    tx.status = 'FAILED'
                    tx.save()
                    print(f"❌ Pesapal Transaction {merchant_reference} failed.")
            except PaymentTransaction.DoesNotExist:
                print(f"⚠️ Transaction reference {merchant_reference} not found in database.")

    # ✅ CRITICAL: Return the exact JSON Pesapal expects
    return Response({
        "orderNotificationType": "IPNCHANGE",
        "orderTrackingId": order_tracking_id,
        "orderMerchantReference": merchant_reference,
        "status": 200
    }, status=200)


# =====================================================================
# 📝 UTILITY & GENERAL VIEWS
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
            profile = request.user.userprofile
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=404)


class ChartDataView2(APIView):
    def get(self, request):
        readings = StockMarketReading.objects.all().order_by('timestamp')
        x = [r.timestamp.strftime('%Y-%m-%d %H:%M:%S') for r in readings]
        y1 = [r.value1 for r in readings]
        y2 = [r.value2 for r in readings]
        return Response({
            "data": [
                {"x": x, "y": y1, "type": "scatter", "mode": "lines+markers", "name": "Stock Value 1"},
                {"x": x, "y": y2, "type": "scatter", "mode": "lines+markers", "name": "Stock Value 2"}
            ],
            "layout": {"title": "Stock Market Reading", "xaxis": {"title": "Time"}, "yaxis": {"title": "Value"}}
        })


class ChartDataView(APIView):
    def get(self, request):
        readings = SensorReading.objects.all().order_by('timestamp')
        x = [r.timestamp.strftime('%Y-%m-%d %H:%M:%S') for r in readings]
        y = [r.value for r in readings]
        return Response({
            "data": [{"x": x, "y": y, "type": "scatter", "mode": "lines+markers", "name": "Sensor"}],
            "layout": {"title": "Sensor Data", "xaxis": {"title": "Time"}, "yaxis": {"title": "Value"}}
        })


class ImageListView(generics.ListAPIView):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
    permission_classes = [AllowAny]


class ImageUploadView(generics.CreateAPIView):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [AllowAny]
