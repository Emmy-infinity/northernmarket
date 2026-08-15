from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField

from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Note, SensorReading, Photo  # Import Photo model here, do not define it!




from rest_framework import serializers
from .models import Product, Photo




# Append to the very end of your local myapp/serializers.py file
from .models import PaymentTransaction

class PaymentTransactionSerializer(serializers.ModelSerializer):
    # Returns the human-readable string version of the transaction choices
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    # Returns the name of the product being promoted for clear UI receipts
    product_title = serializers.CharField(source='product.title', read_only=True)

    class Meta:
        model = PaymentTransaction
        fields = [
            'id',
            'product',
            'product_title',
            'amount',
            'phone_number',
            'tx_ref',
            'transaction_id',
            'status',
            'status_display',
            'created_at'
        ]
        # Protect internal transaction parameters from being tampered with by the frontend
        read_only_fields = ['id', 'status', 'transaction_id', 'tx_ref', 'created_at']


class PhotoSerializer(serializers.ModelSerializer):
    # Use a SerializerMethodField to ensure Cloudinary always outputs clean absolute URLs
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Photo
        # Exclude the direct product relation field to avoid cluttering the frontend arrays
        fields = ['id', 'image_url']

    def get_image_url(self, obj):
        if obj.image:
            # Safely extract the full 'https://cloudinary.com...' string
            try:
                return obj.image.url
            except AttributeError:
                # Fallback if it is stored as a raw string format in the database row
                return str(obj.image)
        return None

# Open your local project ──> myapp/serializers.py
# Open your local project ──> myapp/serializers.py
from rest_framework import serializers
from django.utils import timezone
from .models import Product, Photo

class ProductSerializer(serializers.ModelSerializer):
    seller_username = serializers.ReadOnlyField(source='seller.username')
    seller_email = serializers.ReadOnlyField(source='seller.email')
    
    # 🌟 THE COMPATIBILITY BRIDGE: Map the selection method variables explicitly
    condition_display = serializers.ReadOnlyField(source='get_condition_display')
    item_location_display = serializers.ReadOnlyField(source='get_item_location_display')
    
    # Calculated analytics metadata fields
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

    def get_days_since_listing(self, obj):
        delta = timezone.now() - obj.created_at
        return max(0, delta.days)

    def get_bulk_delivery_estimate_ugx(self, obj):
        # Base rate 5,000 UGX + 2,500 UGX per extra KG
        if not obj.weight:
            return 7000 
        return int(5000 + (float(obj.weight) * 2500))





class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ["id", "title", "content", "created_at", "author"]
        extra_kwargs = {"author": {"read_only": True}}


class SensorReadingSerializer(serializers.ModelSerializer):
    x = serializers.DateTimeField(source='timestamp', format='%Y-%m-%d %H:%M:%S')
    y = serializers.FloatField(source='value')

    class Meta:
        model = SensorReading
        fields = ['x', 'y']



