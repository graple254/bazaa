from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import *
from .decorators import *
import random
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError

from .utils import *

User = get_user_model()



def index_view(request):
    return render(request, 'files/index.html')


def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")
        email = request.POST.get("email")
        role = request.POST.get("role", "shop_manager")

        # Basic validation
        if not username or not password or not email:
            return render(request, "files/signup.html", {"error": "All fields are required."})

        if User.objects.filter(username=username).exists():
            return render(request, "files/signup.html", {"error": "Username already taken."})

        if User.objects.filter(email=email).exists():
            return render(request, "files/signup.html", {"error": "Email already registered."})

        # Create inactive user
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            role=role,
            is_active=False
        )

        # Generate OTP
        otp_code = generate_verification_code()

        # Save OTP to DB
        OTP.objects.create(user=user, code=otp_code)

        # Send verification email
        send_verification_email(email, otp_code)

        # Redirect to verify page and pass email as GET param
        return redirect(f"/verify?email={email}")

    return render(request, "files/signup.html")







# ---------------------------
# VERIFY OTP
# ---------------------------
def verify_view(request):
    email = request.GET.get("email") or request.POST.get("email")
    if not email:
        messages.error(request, "No email provided.")
        return redirect("signup")

    user = get_object_or_404(User, email=email)

    if request.method == 'POST':
        input_code = request.POST.get("otp")

        # Fetch latest unused OTP for this user
        try:
            otp_entry = OTP.objects.filter(user=user, is_used=False).latest('created_at')
        except OTP.DoesNotExist:
            messages.error(request, "No OTP found. Please sign up again.")
            return redirect("signup")

        if otp_entry.code != input_code:
            messages.error(request, "Invalid verification code.")
            return render(request, "files/verify.html", {"email": email})

        # OTP correct → activate user
        user.is_active = True
        user.save()

        # Mark OTP as used
        otp_entry.is_used = True
        otp_entry.save()

        # Auto-login
        login(request, user)
        return redirect("dashboard")

    return render(request, "files/verify.html", {"email": email})







# ---------------------------
# LOGIN
# ---------------------------
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, "Invalid login credentials.")
            return render(request, "files/login.html")

        if not user.is_active:
            messages.error(request, "Account not verified.")
            return render(request, "files/login.html")

        login(request, user)
        return redirect("dashboard")

    return render(request, "files/login.html")



@login_required
def logout_view(request):
    """
    Handle user logout.
    """
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")




@login_required
@shop_manager_required
def shop_manager_dashboard_view(request):
    # Ensure store exists
    if not hasattr(request.user, 'store'):
        messages.info(request, "Please create your store profile first.")
        return redirect('create_store_profile')

    store = request.user.store
    # Fetch 5 most recent products
    recent_products = store.products.order_by('-created_at')[:5]

    context = {
        "store": store,
        "recent_products": recent_products,
    }
    return render(request, 'files/shop_manager_dashboard.html', context)



@login_required
@shop_manager_required
def product_management_view(request):
    store = request.user.store

    # -----------------------------
    # HANDLE PRODUCT CREATION
    # -----------------------------
    if request.method == "POST" and request.POST.get("action") == "create":
        title = request.POST.get("title")
        caption = request.POST.get("caption")
        price = request.POST.get("price")
        was_price = request.POST.get("was_price")
        available_stock = request.POST.get("available_stock")
        images = request.FILES.getlist("images")

        product = Product.objects.create(
            store=store,
            title=title,
            caption=caption,
            price=price or None,
            was_price=was_price or None,
            available_stock=available_stock or 0
        )
        product.calculate_discount()
        product.save()

        for img in images:
            ProductImage.objects.create(product=product, image=img)

        messages.success(request, "Product created successfully.")

    # -----------------------------
    # HANDLE PRODUCT UPDATE
    # -----------------------------
    if request.method == "POST" and request.POST.get("action") == "edit":
        product_id = request.POST.get("product_id")
        product = get_object_or_404(Product, id=product_id, store=store)

        # basic field updates
        product.title = request.POST.get("title")
        product.caption = request.POST.get("caption")
        product.price = request.POST.get("price") or None
        product.was_price = request.POST.get("was_price") or None
        product.available_stock = request.POST.get("available_stock") or 0
        product.is_active = True if request.POST.get("is_active") == "on" else False

        product.calculate_discount()
        product.save()

        # -----------------------------
        # REMOVE SELECTED IMAGES
        # -----------------------------
        images_to_delete = request.POST.getlist("delete_images")
        if images_to_delete:
            ProductImage.objects.filter(id__in=images_to_delete, product=product).delete()

        # -----------------------------
        # ADD NEW IMAGES
        # -----------------------------
        new_images = request.FILES.getlist("images")
        for img in new_images:
            ProductImage.objects.create(product=product, image=img)

        messages.success(request, "Product updated successfully.")

    # -----------------------------
    # HANDLE PRODUCT DELETE
    # -----------------------------
    if request.method == "POST" and request.POST.get("action") == "delete":
        product_id = request.POST.get("product_id")
        product = get_object_or_404(Product, id=product_id, store=store)
        product.delete()
        messages.success(request, "Product deleted.")

    # -----------------------------
    # DEFAULT: SHOW PRODUCTS + STATS
    # -----------------------------
    products = store.products.order_by('-created_at')

    stats = {
        "total": products.count(),
        "active": products.filter(is_active=True).count(),
        "inactive": products.filter(is_active=False).count(),
        "recent": products[:5],
    }

    return render(request, 'files/product_management.html', {
        "products": products,
        "store": store,
        "stats": stats,
    })




@login_required
@shop_manager_required
def create_store_profile(request):
    # Prevent creation if store already exists
    if hasattr(request.user, 'store'):
        messages.warning(request, "You already have a store profile.")
        return redirect('dashboard')

    if request.method == 'POST':
        name = request.POST.get('name')
        subdomain = request.POST.get('subdomain')
        description = request.POST.get('description')
        whatsapp_number = request.POST.get('whatsapp_number')
        logo = request.FILES.get('logo')

        if not name or not subdomain or not whatsapp_number or not logo:
            messages.error(request, "All fields are required.")
            return render(request, 'files/create_store_profile.html')

        try:
            store = Store.objects.create(
                owner=request.user,
                name=name,
                subdomain=subdomain,
                description=description,
                whatsapp_number=whatsapp_number,
                logo=logo
            )
            messages.success(request, "Store profile created successfully!")
            return redirect('dashboard')
        except IntegrityError:
            messages.error(request, "Subdomain already taken. Choose another one.")

    return render(request, 'files/create_store_profile.html')
