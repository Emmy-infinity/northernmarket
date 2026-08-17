# import sys  <-- ❌ REMOVED (unused)

from django.db import models
from django.contrib.auth import get_user_model
from cloudinary.models import CloudinaryField
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()

# =====================================================================
# 🌟 USER PROFILE INFRASTRUCTURE (TRACKS THE PERSON'S CONTACTS)
# =====================================================================
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True, help_text="Primary business phone number")
    whatsapp_number = models.CharField(max_length=15, blank=True, help_text="For direct quick-chats")

    def __str__(self):
        return f"Profile for {self.user.username}"

# ✅ OPTIMIZED: Simplified signal using get_or_create (removes redundant try/except)
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    UserProfile.objects.get_or_create(user=instance)


# =====================================================================
# CORE MARKETPLACE LISTINGS BLUEPRINT
# =====================================================================
class Product(models.Model):
    CONDITION_CHOICES = [
        ('NEW', 'Brand New / Sealed'),
        ('REFURB', 'Refurbished / Tested'),
        ('USED', 'Used / Working'),
        ('SCRAP', 'Scrap / For Spare Parts'),
    ]
    
    LOCATION_CHOICES = [
        ('GULU', 'Gulu City'),
        ('LIRA', 'Lira City'),
        ('KLA', 'Kampala Road / Hub'),
        ('ARUA', 'Arua City'),
    ]

    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    # Financials & Inventory
    price = models.DecimalField(max_digits=12, decimal_places=2, db_index=True)  # ✅ Added index
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='USED', db_index=True)  # ✅ Added index
    stock_count = models.PositiveIntegerField(default=1)
    
    # Logistics
    item_location = models.CharField(max_length=10, choices=LOCATION_CHOICES, default='GULU', db_index=True)  # ✅ Added index
    seller_location_details = models.CharField(max_length=255, help_text="e.g., Near Gulu University Main Gate")
    
    # Infrastructure fields
    weight = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        help_text="Weight in Kilograms (KG), e.g., 2.50"
    )
    contact_phone = models.CharField(
        max_length=15, 
        blank=True, 
        help_text="Direct phone number for item inquiries (e.g., 256770000000)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)  # ✅ Added index

    # B2B Premium Ranking Fields
    is_featured = models.BooleanField(default=False, db_index=True)
    featured_until = models.DateTimeField(null=True, blank=True, db_index=True)

    # ✅ OPTIMIZED: Added Meta for default ordering and explicit indexes
    class Meta:
        ordering = ['-created_at']  # Newest products first by default
        indexes = [
            models.Index(fields=['price']),
            models.Index(fields=['condition']),
            models.Index(fields=['item_location']),
            models.Index(fields=['created_at']),
        ]

    def save(self, *args, **kwargs):
        # Auto-expire featured status
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
# PAYMENT LEDGERS & HISTORICAL MODELS
# =====================================================================
class PaymentTransaction(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Payment Prompt'),
        ('SUCCESSFUL', 'Payment Captured Securely'),
        ('FAILED', 'Transaction Declined'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='payments')
    # ✅ OPTIMIZED: Increased max_digits from 10 → 12 to safely match Product.price
    amount = models.DecimalField(max_digits=12, decimal_places=2)  
    phone_number = models.CharField(max_length=15) 
    tx_ref = models.CharField(max_length=100, unique=True) 
    transaction_id = models.CharField(max_length=100, blank=True, null=True) 
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    # ✅ OPTIMIZED: Added Meta for default ordering
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"TX: {self.tx_ref} - {self.status}"


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



# models.py – add at the bottom

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
        """Return the single config instance, creating a default one if it doesn't exist."""
        config, created = cls.objects.get_or_create(id=1)
        return config
