# myapp/admin.py

from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline  # Unfold premium Tailwind styles
from unfold.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    Product, Photo, Category, Location, SiteConfiguration,
    PaymentTransaction, Note, SensorReading, StockMarketReading,
    UserProfile
)


# ─── PHOTO INLINE ──────────────────────────────────────────────────────
class PhotoInline(TabularInline):
    model = Photo
    extra = 3


# ─── PRODUCT ADMIN (OPTIMIZED) ──────────────────────────────────────
@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ['title', 'price', 'condition', 'category', 'location', 'stock_count', 'is_featured']
    list_filter = ['condition', 'category', 'location', 'is_featured']
    search_fields = ['title', 'description', 'seller__username']
    inlines = [PhotoInline]
    
    # 🚀 OPTIMIZATION: Fetches seller, category, and location in a single SQL query.
    # Without this, the admin list page runs 1 query per row for each foreign key.
    list_select_related = ('seller', 'category', 'location')
    
    fieldsets = (
        (None, {
            'fields': ('seller', 'title', 'description', 'price', 'condition', 'stock_count')
        }),
        ('Category & Location', {
            'fields': ('category', 'location', 'seller_location_details')
        }),
        ('Logistics', {
            'fields': ('weight', 'contact_phone')
        }),
        ('Premium Ranking', {
            'fields': ('is_featured', 'featured_until')
        }),
    )
    readonly_fields = ('created_at',)


# ─── CATEGORY ADMIN ──────────────────────────────────────────────────
@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug')
    list_filter = ('is_active',)


# ─── LOCATION ADMIN ──────────────────────────────────────────────────
@admin.register(Location)
class LocationAdmin(ModelAdmin):
    list_display = ('name', 'code', 'is_active')
    search_fields = ('name', 'code')
    list_filter = ('is_active',)


# ─── SITE CONFIGURATION ADMIN ──────────────────────────────────────
@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(ModelAdmin):
    compressed_fields = []   # Unfold fix: required for compressed layout
    fields = ('promotion_fee',)
    readonly_fields = ('updated_at',)
    list_display = ('id', 'promotion_fee', 'updated_at')


# ─── USER ADMIN (Unfold‑styled) ────────────────────────────────────
# Unregister the default User admin
admin.site.unregister(User)

@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = UserChangeForm
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')


# ─── PAYMENT TRANSACTION ADMIN (OPTIMIZED) ──────────────────────────
@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(ModelAdmin):
    list_display = ('tx_ref', 'product', 'amount', 'phone_number', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('tx_ref', 'transaction_id', 'phone_number', 'product__title')
    
    # 🚀 OPTIMIZATION: Fetches the related Product in a single SQL query.
    list_select_related = ('product',)
    
    readonly_fields = ('tx_ref', 'transaction_id', 'created_at')


# ─── USER PROFILE ADMIN ──────────────────────────────────────────────
@admin.register(UserProfile)
class UserProfileAdmin(ModelAdmin):
    list_display = ('user', 'phone_number', 'whatsapp_number')
    search_fields = ('user__username', 'phone_number', 'whatsapp_number')
    list_select_related = ('user',)


# ─── NOTE ADMIN ──────────────────────────────────────────────────────
@admin.register(Note)
class NoteAdmin(ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    list_filter = ('created_at',)
    list_select_related = ('author',)


# ─── SENSOR READING ADMIN ────────────────────────────────────────────
@admin.register(SensorReading)
class SensorReadingAdmin(ModelAdmin):
    list_display = ('timestamp', 'value')
    list_filter = ('timestamp',)


# ─── STOCK MARKET READING ADMIN ──────────────────────────────────────
@admin.register(StockMarketReading)
class StockMarketReadingAdmin(ModelAdmin):
    list_display = ('timestamp', 'value1', 'value2')
    list_filter = ('timestamp',)
