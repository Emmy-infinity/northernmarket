from django.db import models
from django.contrib.auth import get_user_model
from cloudinary.models import CloudinaryField
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify

User = get_user_model()

# =====================================================================
# 🌟 USER PROFILE INFRASTRUCTURE
# =====================================================================
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True, help_text="Primary business phone number")
    whatsapp_number = models.CharField(max_length=15, blank=True, help_text="For direct quick-chats")

    def __str__(self):
        return f"Profile for {self.user.username}"

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    UserProfile.objects.get_or_create(user=instance)


# =====================================================================
# 🏷️ DYNAMIC CATEGORIES & LOCATIONS
# =====================================================================
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']


class Location(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


# =====================================================================
# CORE MARKETPLACE LISTINGS BLUEPRINT (FULLY OPTIMIZED)
# =====================================================================
class Product(models.Model):
    CONDITION_CHOICES = [
        ('NEW', 'Brand New / Sealed'),
        ('REFURB', 'Refurbished / Tested'),
        ('USED', 'Used / Working'),
        ('SCRAP', 'Scrap / For Spare Parts'),
    ]

    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    
    # ✅ FIXED: Added db_index=True for lightning-fast search
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField()

    # Financials & Inventory
    price = models.DecimalField(max_digits=12, decimal_places=2, db_index=True)
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='USED', db_index=True)
    stock_count = models.PositiveIntegerField(default=1)

    # Dynamic Category & Location
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        help_text="Select a product category"
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        help_text="Where the item is located"
    )

    # Legacy fields
    seller_location_details = models.CharField(max_length=255, blank=True, help_text="e.g., Near Gulu University Main Gate")
    weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Weight in KG")
    contact_phone = models.CharField(max_length=15, blank=True, help_text="Direct phone number for item inquiries")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    # B2B Premium Ranking Fields
    is_featured = models.BooleanField(default=False, db_index=True)
    featured_until = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            # 🚀 OPTIMIZATION: Composite indexes for the most common e-commerce queries.
            models.Index(fields=['is_featured', 'featured_until'], name='prod_feat_until_idx'),
            models.Index(fields=['category', 'price'], name='prod_cat_price_idx'),
            models.Index(fields=['location', '-created_at'], name='prod_loc_created_idx'),
        ]

    def save(self, *args, **kwargs):
        if self.featured_until and self.featured_until < timezone.now():
            self.is_featured = False
            self.featured_until = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.price:,} UGX"


class Photo(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='photos', null=True, blank=True)
    image = CloudinaryField('image')
    created_at = models.DateTimeField(auto_now_add=True)


# =====================================================================
# PAYMENT LEDGERS & HISTORICAL MODELS (FULLY OPTIMIZED)
# =====================================================================
class PaymentTransaction(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Payment Prompt'),
        ('SUCCESSFUL', 'Payment Captured Securely'),
        ('FAILED', 'Transaction Declined'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    phone_number = models.CharField(max_length=15)
    tx_ref = models.CharField(max_length=100, unique=True)  # Unique automatically creates an index
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    
    # ✅ FIXED: Added db_index=True to status (you query this constantly)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            # 🚀 OPTIMIZATION: Fetch pending transactions quickly (e.g., for retry logic)
            models.Index(fields=['status', 'created_at'], name='pay_stat_created_idx'),
        ]

    def __str__(self):
        return f"TX: {self.tx_ref} - {self.status}"


# =====================================================================
# 🔍 SEARCH & CLICK ANALYTICS (NEW)
# =====================================================================
class SearchQuery(models.Model):
    """
    Records every search performed on the platform, including device and browser info.
    """
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='search_queries')
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True, help_text="For anonymous users")
    query = models.CharField(max_length=255, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, help_text="Raw User-Agent string")
    device_type = models.CharField(max_length=20, blank=True, db_index=True)  # Mobile, Tablet, Desktop
    browser = models.CharField(max_length=50, blank=True, db_index=True)
    os = models.CharField(max_length=50, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Search Query'
        verbose_name_plural = 'Search Queries'

    def __str__(self):
        return f"{self.query} - {self.created_at}"


class ProductClick(models.Model):
    """
    Tracks product clicks (especially detail views) with device analytics.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='clicks')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='product_clicks')
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True, help_text="For anonymous users")
    search_query = models.CharField(max_length=255, null=True, blank=True, db_index=True, help_text="Search query that led to this click")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    referer = models.URLField(max_length=500, null=True, blank=True, help_text="Page URL where the click occurred")
    user_agent = models.TextField(blank=True, help_text="Raw User-Agent string")
    device_type = models.CharField(max_length=20, blank=True, db_index=True)
    browser = models.CharField(max_length=50, blank=True, db_index=True)
    os = models.CharField(max_length=50, blank=True, db_index=True)
    is_detail_view = models.BooleanField(default=True, help_text="True if this click opened the product detail page")
    clicked_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-clicked_at']
        verbose_name = 'Product Click'
        verbose_name_plural = 'Product Clicks'
        indexes = [
            models.Index(fields=['product', 'clicked_at'], name='click_prod_time_idx'),
            models.Index(fields=['search_query', 'clicked_at'], name='click_search_time_idx'),
        ]

    def __str__(self):
        return f"Click on {self.product.title} at {self.clicked_at}"


# =====================================================================
# LEGACY MODELS
# =====================================================================
class Note(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notes")

    def __str__(self):
        return self.title


class SensorReading(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    value = models.FloatField()

    def __str__(self):
        return f"{self.timestamp}: {self.value}"


class StockMarketReading(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    value1 = models.FloatField()
    value2 = models.FloatField()

    def __str__(self):
        return f"{self.timestamp}: {self.value1} / {self.value2}"


# =====================================================================
# ⚙️ SITE CONFIGURATION
# =====================================================================
class SiteConfiguration(models.Model):
    promotion_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=20000.00,
        help_text="Default fee for promoting a product (UGX). This is used for all products."
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Promotion Fee: UGX {self.promotion_fee}"

    class Meta:
        verbose_name = "Site Configuration"
        verbose_name_plural = "Site Configurations"

    @classmethod
    def get_config(cls):
        config, created = cls.objects.get_or_create(id=1)
        return config
