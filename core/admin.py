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


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('store', 'name', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)


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


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('product', 'user_name', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('product__title', 'user_name', 'text')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('product', 'user_ip', 'created_at')
    search_fields = ('product__title', 'user_ip')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


@admin.register(Announcement_Store)
class AnnouncementStoreAdmin(admin.ModelAdmin):
    list_display = ("title", "store", "is_active", "created_at")
    list_filter = ("is_active", "store")
    search_fields = ("title", "message", "store__name")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)


@admin.register(Announcement_Global_For_All_Store)
class GlobalAnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("title", "message")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)


@admin.register(index_Content)
class IndexContentAdmin(admin.ModelAdmin):
    list_display = ("heading_1", "heading_2", "section_heading_mission", "pricing_heading")
    search_fields = ("heading_1", "heading_2", "section_heading_mission", "fact_heading", "pricing_heading")

    fieldsets = (
        ("Hero Section", {
            "fields": (
                "heading_1",
                "heading_2",
                "subheading_1",
                "image_1",
                "image_2",
            )
        }),

        ("Mission Section", {
            "fields": (
                "section_heading_mission",
                "image_3",
                "image_4",
                "image_5",
            )
        }),

        ("Facts Section", {
            "fields": (
                "fact_heading",
                "fact_subheading",
                "fact_statement_1",
                "fact_statement_2",
                "fact_statement_3",
                "fact_image_1",
                "fact_image_2",
                "fact_image_3",
            )
        }),

        ("Pricing Section", {
            "fields": (
                "pricing_heading",
                "pricing_subheading",
                "monthly_price",
                "annual_price",
            )
        }),
    )


@admin.register(PasswordReset)
class PasswordResetAdmin(admin.ModelAdmin):
    list_display = ("user", "token", "is_used", "created_at")
    list_filter = ("is_used", "created_at")
    search_fields = ("user__username", "user__email", "token")
    readonly_fields = ("user", "token", "created_at", "is_used")

    ordering = ("-created_at",)    


@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'session_key', 'url_path', 'method', 'visit_date', 'location')
    list_filter = ('method', 'visit_date', 'location')
    search_fields = ('ip_address', 'session_key', 'url_path', 'referrer', 'user_agent')
    readonly_fields = ('visit_date',)
    ordering = ('-visit_date',)