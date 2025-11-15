from django.contrib.auth.models import AbstractUser
from django.db import models
from decimal import Decimal, InvalidOperation
# -------------------------
# User
# -------------------------
class User(AbstractUser):
    ROLE_CHOICES = [
        ('shop_manager', 'Shop Manager'),
        # Add more as platform evolves
    ]

    role = models.CharField(max_length=30, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.username} - {self.role}"

# -------------------------
# OTP
# -------------------------
class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"OTP for {self.user.username}: {self.code}"

# -------------------------
# Store
# -------------------------
class Store(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='store')
    name = models.CharField(max_length=100)
    subdomain = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='store_logos/')
    whatsapp_number = models.CharField(max_length=20, help_text="Business WhatsApp number with country code")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_whatsapp_link(self, product_title=None):
        """
        Generate WhatsApp link for a product.
        Optionally pre-fill message with product name.
        """
        base_link = f"https://wa.me/{self.whatsapp_number}"
        if product_title:
            message = f"Hi, I'm interested in {product_title}"
            return f"{base_link}?text={message.replace(' ', '%20')}"
        return base_link


# -------------------------
# Product
# -------------------------
class Product(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='products')
    title = models.CharField(max_length=150)
    caption = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    was_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    available_stock = models.PositiveIntegerField(default=0, blank=True, null=True)
    percent_discount = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.store.name})"
    from decimal import Decimal, InvalidOperation

    def calculate_discount(self):
        """Calculate percent discount if was_price and price are set."""

        # Convert to Decimal safely
        try:
            price = Decimal(str(self.price)) if self.price else None
            was_price = Decimal(str(self.was_price)) if self.was_price else None
        except InvalidOperation:
            self.percent_discount = None
            return

        # Real logic
        if was_price and price and was_price > price:
            discount = ((was_price - price) / was_price) * 100
            self.percent_discount = int(discount)
        else:
            self.percent_discount = None



# -------------------------
# Product Images
# -------------------------
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='store_products/')
    is_primary = models.BooleanField(default=False)  # Optional, for default display
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.title}"


# -------------------------
# Comments- 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
# -------------------------
class Comment(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='comments')
    user_name = models.CharField(max_length=100)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user_name} on {self.product.title}"


# -------------------------
# Likes
# -------------------------
class Like(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='likes')
    user_ip = models.GenericIPAddressField()  # Simple anonymous tracking
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user_ip')  # Prevent same IP liking multiple times

    def __str__(self):
        return f"Like on {self.product.title} from {self.user_ip}"
