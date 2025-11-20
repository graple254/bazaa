from django.http import JsonResponse
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
from django.core.paginator import Paginator
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
        messages.success(request, "Successfully logged in.")
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

    if not hasattr(request.user, 'store'):
        messages.info(request, "Please create your store profile first.")
        return redirect('create_store_profile')

    store = request.user.store

    # ---------------------------------------------------------
    # PRODUCT + CATEGORY STATS
    # ---------------------------------------------------------
    products = store.products.all()
    categories = store.categories.all()

    product_stats = {
        "total": products.count(),
        "active": products.filter(is_active=True).count(),
        "inactive": products.filter(is_active=False).count(),
        "with_stock": products.filter(available_stock__gt=0).count(),
        "low_stock": products.filter(available_stock__lte=3, available_stock__gt=0).count(),
    }

    recent_products = products.order_by('-created_at')[:3]
    category_count = categories.count()

    # ---------------------------------------------------------
    # ANNOUNCEMENTS
    # ---------------------------------------------------------
    announcements = store.announcements.order_by('-created_at')
    paginator = Paginator(announcements, 3)  # At least 3 per page
    page_number = request.GET.get('announcement_page')
    announcements_page_obj = paginator.get_page(page_number)
    announcement_count = announcements.count()
    active_announcements = announcements.filter(is_active=True).count()

    global_announcements = Announcement_Global_For_All_Store.objects.filter(
        is_active=True
    ).order_by('-created_at')

    # ---------------------------------------------------------
    # CREATE STORE ANNOUNCEMENT
    # ---------------------------------------------------------
    if request.method == "POST" and request.POST.get("action") == "create_store_announcement":

        title = request.POST.get("title")
        message_body = request.POST.get("message")
        status = request.POST.get("is_active") == "on"

        if not title or not message_body:
            messages.error(request, "Both fields are required.")
            return redirect("dashboard")

        Announcement_Store.objects.create(
            store=store,
            title=title,
            message=message_body,
            is_active=status
        )

        messages.success(request, "Announcement created.")
        return redirect("dashboard")

    # ---------------------------------------------------------
    # EDIT STORE ANNOUNCEMENT
    # ---------------------------------------------------------
    if request.method == "POST" and request.POST.get("action") == "edit_store_announcement":

        ann_id = request.POST.get("announcement_id")
        ann = get_object_or_404(Announcement_Store, id=ann_id, store=store)

        ann.title = request.POST.get("title")
        ann.message = request.POST.get("message")
        ann.is_active = request.POST.get("is_active") == "on"

        ann.save()

        messages.success(request, "Announcement updated.")
        return redirect("dashboard")

    # ---------------------------------------------------------
    # TOGGLE ACTIVE/INACTIVE
    # ---------------------------------------------------------
    if request.method == "POST" and request.POST.get("action") == "toggle_status":

        ann_id = request.POST.get("announcement_id")
        ann = get_object_or_404(Announcement_Store, id=ann_id, store=store)

        ann.is_active = not ann.is_active
        ann.save()

        messages.success(request, "Status updated.")
        return redirect("dashboard")

    # ---------------------------------------------------------
    # STORE PROFILE UPDATE
    # ---------------------------------------------------------
    if request.method == "POST" and request.POST.get("action") == "update_store":
        new_name = request.POST.get("name")
        new_desc = request.POST.get("description")
        new_whatsapp = request.POST.get("whatsapp_number")
        new_sub = request.POST.get("subdomain")
        new_logo = request.FILES.get("logo")

        if new_sub and new_sub != store.subdomain:
            if Store.objects.filter(subdomain=new_sub).exclude(id=store.id).exists():
                messages.error(request, "Subdomain already in use.")
                return redirect("dashboard")

        store.name = new_name
        store.description = new_desc
        store.whatsapp_number = new_whatsapp
        store.subdomain = new_sub

        if new_logo:
            store.logo = new_logo

        store.save()

        messages.success(request, "Store updated.")
        return redirect("dashboard")

    # ---------------------------------------------------------
    # CONTEXT
    # ---------------------------------------------------------
    context = {
        "store": store,
        "product_stats": product_stats,
        "category_count": category_count,
        "recent_products": recent_products,
        "categories": categories,
        "announcements": announcements,
        "announcement_count": announcement_count,
        "active_announcements": active_announcements,
        "global_announcements": global_announcements,
        "announcements_page_obj": announcements_page_obj,
    }

    return render(request, 'files/shop_manager_dashboard.html', context)





@login_required
@shop_manager_required
def product_management_view(request):
    store = request.user.store

    # -----------------------------
    # CREATE MULTIPLE CATEGORIES
    # -----------------------------
    if request.method == "POST" and request.POST.get("action") == "create_categories":
        names = request.POST.get("names", "")  # comma-separated or list
        raw_list = [n.strip() for n in names.split(",") if n.strip()]

        created_items = []

        for name in raw_list:
            category, created = Category.objects.get_or_create(
                store=store,
                name=name
            )
            created_items.append({"id": category.id, "name": category.name})

        messages.success(request, f"Created {len(created_items)} categories.")
        return redirect('product_management')

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
        category_ids = request.POST.getlist("categories")  # <-- NEW

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

        # assign categories
        if category_ids:
            product.categories.set(category_ids)

        # create images
        for img in images:
            ProductImage.objects.create(product=product, image=img)

        messages.success(request, "Product created successfully.")
        return redirect('product_management')

    # -----------------------------
    # HANDLE PRODUCT UPDATE
    # -----------------------------
    if request.method == "POST" and request.POST.get("action") == "edit":
        product_id = request.POST.get("product_id")
        product = get_object_or_404(Product, id=product_id, store=store)

        product.title = request.POST.get("title")
        product.caption = request.POST.get("caption")
        product.price = request.POST.get("price") or None
        product.was_price = request.POST.get("was_price") or None
        product.available_stock = request.POST.get("available_stock") or 0
        product.is_active = True if request.POST.get("is_active") == "on" else False

        product.calculate_discount()
        product.save()

        # update categories
        category_ids = request.POST.getlist("categories")
        if category_ids:
            product.categories.set(category_ids)
        else:
            product.categories.clear()

        # delete images
        images_to_delete = request.POST.getlist("delete_images")
        if images_to_delete:
            ProductImage.objects.filter(id__in=images_to_delete, product=product).delete()

        # add new images
        new_images = request.FILES.getlist("images")
        for img in new_images:
            ProductImage.objects.create(product=product, image=img)

        messages.success(request, "Product updated successfully.")
        return redirect('product_management')
    # -----------------------------
    # HANDLE PRODUCT DELETE
    # -----------------------------
    if request.method == "POST" and request.POST.get("action") == "delete":
        product_id = request.POST.get("product_id")
        product = get_object_or_404(Product, id=product_id, store=store)
        product.delete()
        messages.success(request, "Product deleted.")
        return redirect('product_management')

    # -----------------------------
    # DEFAULT: SHOW PRODUCTS + STATS
    # -----------------------------
    product_qs = store.products.order_by('-created_at')

    stats = {
        "total": product_qs.count(),
        "active": product_qs.filter(is_active=True).count(),
        "inactive": product_qs.filter(is_active=False).count(),
        "recent": product_qs[:5],
    }

    # -----------------------------
    # PAGINATION
    # -----------------------------
    paginator = Paginator(product_qs, 7)  # 10 per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    
    categories = Category.objects.filter(store=store).order_by("name")

    return render(request, 'files/product_management.html', {
        "products": page_obj,   # send paginated page
        "page_obj": page_obj,   # for template navigation
        "stats": stats,
        "store": store,
        "categories": categories,
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
