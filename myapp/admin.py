# admin.py
# myapp/admin.py
from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline # 🧠 USE THESE INSTEAD
from .models import Product, Photo

class PhotoInline(TabularInline): # Elegant responsive inline inputs
    model = Photo
    extra = 3

@admin.register(Product)
class ProductAdmin(ModelAdmin): # Inherits clean Tailwind CSS styling
    list_display = ['title', 'price', 'condition', 'item_location', 'seller']
    list_filter = ['condition', 'item_location']
    search_fields = ['title', 'description']
    inlines = [PhotoInline]
