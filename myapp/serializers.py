from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import serializers
from .models import Note, SensorReading, Photo, Product, PaymentTransaction

# =====================================================================
# 🔐 1. USER & AUTHENTICATION SERIALIZERS
# =====================================================================
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        # ✅ Uses create_user to hash password – unchanged and safe.
        return User.objects.create_user(**validated_data)


# =====================================================================
# 💳 2. MOBILE MONEY BILLING TRANSACTION ENGINE
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
        # ✅ No changes – already clean.


# =====================================================================
# 📸 3. MULTI-IMAGE ASSETS COMPRESSION PIPELINE
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
# 🌾 4. B2B MARKETPLACE PRODUCT LISTING GRID ENGINE
# =====================================================================
class ProductSerializer(serializers.ModelSerializer):
    # Seller fields are read‑only by using ReadOnlyField – explicit and safe.
    seller = serializers.ReadOnlyField(source='seller.id')
    seller_username = serializers.ReadOnlyField(source='seller.username')
    seller_email = serializers.ReadOnlyField(source='seller.email')
    
    photos = PhotoSerializer(many=True, read_only=True)
    
    condition_display = serializers.ReadOnlyField(source='get_condition_display')
    item_location_display = serializers.ReadOnlyField(source='get_item_location_display')
    
    days_since_listing = serializers.SerializerMethodField()
    bulk_delivery_estimate_ugx = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'seller', 'seller_username', 'seller_email', 'title', 
            'description', 'price', 'condition', 'condition_display', 
            'stock_count', 'item_location', 'item_location_display', 
            'seller_location_details', 'weight', 'contact_phone', 
            'photos', 'is_featured', 'created_at', 'days_since_listing',
            'bulk_delivery_estimate_ugx'
        ]
        # ✅ Removed redundant 'seller' from read_only_fields because it's already a ReadOnlyField.
        #    'is_featured' and 'created_at' are kept read‑only to prevent mass‑assignment issues.
        read_only_fields = ['id', 'is_featured', 'created_at']

    def get_days_since_listing(self, obj):
        delta = timezone.now() - obj.created_at
        return max(0, delta.days)

    def get_bulk_delivery_estimate_ugx(self, obj):
        # Safe fallback: if no weight, return a base estimate.
        if not obj.weight:
            return 7000
        return int(5000 + (float(obj.weight) * 2500))


# =====================================================================
# 📝 5. SENSOR READINGS & LEGACY NOTE MANAGEMENT TRACKS
# =====================================================================
class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ["id", "title", "content", "created_at", "author"]
        extra_kwargs = {"author": {"read_only": True}}


class SensorReadingSerializer(serializers.ModelSerializer):
    # Mapping to 'x' and 'y' for charting – unchanged.
    x = serializers.DateTimeField(source='timestamp', format='%Y-%m-%d %H:%M:%S')
    y = serializers.FloatField(source='value')

    class Meta:
        model = SensorReading
        fields = ['x', 'y']
