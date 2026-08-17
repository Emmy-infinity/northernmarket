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

from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin
from unfold.forms import UserChangeForm, UserCreationForm

# 1. Unregister the built-in standard User admin layout
admin.site.unregister(User)

# 2. Re-register the User model using Unfold's premium Tailwind layout classes
@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    # This securely overrides the input layouts with Tailwind components
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = UserChangeForm


# admin.py

from .models import SiteConfiguration

@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    fields = ('promotion_fee',)
    readonly_fields = ('updated_at',)
    list_display = ('id', 'promotion_fee', 'updated_at')
