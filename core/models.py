from django.contrib.auth.models import AbstractUser
from django.db import models
from decimal import Decimal, InvalidOperation
import uuid
from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image

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


class Category(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='categories', blank=True, null=True)
    name = models.CharField(max_length=120, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = ('store', 'name')  # category name is unique per store

    def __str__(self):
        return self.name




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
    categories = models.ManyToManyField(Category, related_name='products', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.store.name})"

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



def _unique_name(suffix):
    return f"{uuid.uuid4().hex}_{suffix}.jpg"


def _resize_and_save(uploaded_image, size):
    if not uploaded_image:
        return None, None

    uploaded_image.open()
    img = Image.open(uploaded_image).convert("RGB")
    img.thumbnail(size, Image.Resampling.LANCZOS)

    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=88, optimize=True)
    buffer.seek(0)

    return _unique_name(suffix=f"{size[0]}x{size[1]}"), ContentFile(buffer.read())


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")

    # original raw upload
    image = models.ImageField(upload_to="store_products/")

    # derived
    image_large = models.ImageField(upload_to="store_products/", blank=True, null=True)
    image_medium = models.ImageField(upload_to="store_products/", blank=True, null=True)
    image_thumb = models.ImageField(upload_to="store_products/", blank=True, null=True)

    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    LARGE = (1200, 1200)
    MEDIUM = (600, 600)
    THUMB = (300, 300)

    def save(self, *args, **kwargs):
        new_upload = False

        # If object is NEW → we definitely need to process
        if not self.pk:
            new_upload = True
        else:
            # Check if original image changed
            old = ProductImage.objects.get(pk=self.pk)
            if old.image != self.image:
                new_upload = True

        super().save(*args, **kwargs)

        if new_upload:
            self._generate_resized()
            super().save(update_fields=["image_large", "image_medium", "image_thumb"])

    def _generate_resized(self):
        # wipe old derived files if replacing
        if self.image_large:
            self.image_large.delete(save=False)
        if self.image_medium:
            self.image_medium.delete(save=False)
        if self.image_thumb:
            self.image_thumb.delete(save=False)

        # generate fresh
        name, content = _resize_and_save(self.image, self.LARGE)
        self.image_large.save(name, content, save=False)

        name, content = _resize_and_save(self.image, self.MEDIUM)
        self.image_medium.save(name, content, save=False)

        name, content = _resize_and_save(self.image, self.THUMB)
        self.image_thumb.save(name, content, save=False)

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


class Announcement_Store(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=150, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Announcement for {self.store.name}: {self.title}"
    



class Announcement_Global_For_All_Store(models.Model):
    title = models.CharField(max_length=150, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Global Announcement: {self.title}"