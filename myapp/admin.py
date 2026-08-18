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


# ─── PRODUCT ADMIN ──────────────────────────────────────────────────
@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ['title', 'price', 'condition', 'category', 'location', 'stock_count', 'is_featured']
    list_filter = ['condition', 'category', 'location', 'is_featured']
    search_fields = ['title', 'description', 'seller__username']
    inlines = [PhotoInline]
    # Optional: add fieldsets if you want a custom layout
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
    # You can add custom list_display if needed
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')


# ─── OTHER MODELS (simple registrations) ──────────────────────────
# If you want these to be managed in the admin, uncomment:
# admin.site.register(PaymentTransaction, ModelAdmin)
# admin.site.register(Note, ModelAdmin)
# admin.site.register(SensorReading, ModelAdmin)
# admin.site.register(StockMarketReading, ModelAdmin)
# admin.site.register(UserProfile, ModelAdmin)
