from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *

# -------------------------
# User admin
# -------------------------
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ('username', 'email', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email')
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'is_active', 'is_staff')}
        ),
    )


admin.site.register(User, UserAdmin)


# -------------------------
# OTP admin
# -------------------------
class OTPAdmin(admin.ModelAdmin):
    model = OTP
    list_display = ('user', 'code', 'created_at', 'is_used')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__username', 'code')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


admin.site.register(OTP, OTPAdmin)


# -----------------------------
# Store Admin
# -----------------------------
@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'subdomain', 'whatsapp_number', 'created_at')
    search_fields = ('name', 'subdomain', 'owner__username', 'whatsapp_number')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)




# -----------------------------
# Product Image Inline
# -----------------------------
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1  # Number of extra blank image forms
    readonly_fields = ('created_at',)
    fields = ('image', 'is_primary', 'created_at')


# -----------------------------
# Product Admin
# -----------------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'store', 'price', 'was_price', 'percent_discount', 'available_stock', 'is_active', 'created_at')
    search_fields = ('title', 'store__name')
    list_filter = ('is_active', 'created_at', 'store')
    readonly_fields = ('percent_discount', 'created_at')
    ordering = ('-created_at',)
    inlines = [ProductImageInline]

    def save_model(self, request, obj, form, change):
        """Calculate discount before saving."""
        obj.calculate_discount()
        super().save_model(request, obj, form, change)


# -----------------------------
# ProductImage Admin (optional)
# -----------------------------
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'is_primary', 'created_at')
    list_filter = ('is_primary', 'created_at')
    readonly_fields = ('created_at',)
    search_fields = ('product__title',)
    ordering = ('-created_at',)