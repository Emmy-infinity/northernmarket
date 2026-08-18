from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import serializers
from .models import (
    Note, SensorReading, Photo, Product, PaymentTransaction,
    Category, Location  # ✅ Import new models
)

# =====================================================================
# 🔐 1. USER & AUTHENTICATION SERIALIZERS
# =====================================================================
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


# =====================================================================
# 🏷️ 2. CATEGORY & LOCATION SERIALIZERS (READ-ONLY)
# =====================================================================
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'is_active']


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'code', 'is_active']


# =====================================================================
# 💳 3. PAYMENT TRANSACTION SERIALIZER
# =====================================================================
class PaymentTransactionSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    product_title = serializers.CharField(source='product.title', read_only=True)

    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 'product', 'product_title', 'amount', 'phone_number',
            'tx_ref', 'transaction_id', 'status', 'status_display', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'transaction_id', 'tx_ref', 'created_at']


# =====================================================================
# 📸 4. PHOTO SERIALIZER
# =====================================================================
class PhotoSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Photo
        fields = ['id', 'image_url']

    def get_image_url(self, obj):
        if obj.image:
            try:
                return obj.image.url
            except AttributeError:
                return str(obj.image)
        return None


# =====================================================================
# 🌾 5. PRODUCT SERIALIZER (with dynamic category & location)
# =====================================================================
class ProductSerializer(serializers.ModelSerializer):
    # ─── Seller fields ──────────────────────────────────────────────
    seller = serializers.ReadOnlyField(source='seller.id')
    seller_username = serializers.ReadOnlyField(source='seller.username')
    seller_email = serializers.ReadOnlyField(source='seller.email')

    # ─── Photos ─────────────────────────────────────────────────────
    photos = PhotoSerializer(many=True, read_only=True)

    # ─── Condition display ──────────────────────────────────────────
    condition_display = serializers.ReadOnlyField(source='get_condition_display')

    # ─── DYNAMIC CATEGORY & LOCATION FIELDS ──────────────────────
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    location_code = serializers.CharField(source='location.code', read_only=True)

    # ─── Custom fields ─────────────────────────────────────────────
    days_since_listing = serializers.SerializerMethodField()
    bulk_delivery_estimate_ugx = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id',
            'seller', 'seller_username', 'seller_email',
            'title', 'description',
            'price',
            'condition', 'condition_display',
            'stock_count',
            # ─── Dynamic fields ──────────────────────────────────
            'category', 'category_name', 'category_slug',
            'location', 'location_name', 'location_code',
            # ─── Legacy fields ──────────────────────────────────
            'seller_location_details',
            'weight',
            'contact_phone',
            # ─── Media & rankings ────────────────────────────────
            'photos',
            'is_featured',
            'created_at',
            'days_since_listing',
            'bulk_delivery_estimate_ugx'
        ]
        read_only_fields = ['id', 'is_featured', 'created_at']

    def get_days_since_listing(self, obj):
        delta = timezone.now() - obj.created_at
        return max(0, delta.days)

    def get_bulk_delivery_estimate_ugx(self, obj):
        if not obj.weight:
            return 7000
        return int(5000 + (float(obj.weight) * 2500))


# =====================================================================
# 📝 6. NOTE SERIALIZER
# =====================================================================
class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ["id", "title", "content", "created_at", "author"]
        extra_kwargs = {"author": {"read_only": True}}


# =====================================================================
# 📊 7. SENSOR READING SERIALIZER
# =====================================================================
class SensorReadingSerializer(serializers.ModelSerializer):
    x = serializers.DateTimeField(source='timestamp', format='%Y-%m-%d %H:%M:%S')
    y = serializers.FloatField(source='value')

    class Meta:
        model = SensorReading
        fields = ['x', 'y']
