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

class ProductSerializer(serializers.ModelSerializer):
    # 'photos' matches the related_name='photos' string defined inside your Photo ForeignKey model
    # read_only=True ensures image upload logic is handled on its own separate endpoint
    photos = PhotoSerializer(many=True, read_only=True)
    
    # Human-readable displays for choices fields on the React frontend
    condition_display = serializers.CharField(source='get_condition_display', read_only=True)
    item_location_display = serializers.CharField(source='get_item_location_display', read_only=True)
    
    # Display the seller's username instead of just a raw database integer number
    seller_username = serializers.CharField(source='seller.username', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 
            'seller', 
            'seller_username',
            'title', 
            'description', 
            'price', 
            'condition', 
            'condition_display', 
            'stock_count', 
            'item_location', 
            'item_location_display', 
            'seller_location_details', 
            'photos', # Returns an array of nested photo objects
            'created_at'
        ]
        read_only_fields = ['id', 'seller', 'created_at']








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



