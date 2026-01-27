from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import Vendor, PasswordResetOTP
from .forms import RegisterForm, LoginForm
from django.contrib.auth.decorators import login_required
from .models import Product, ProductImage
from .forms import ProductForm
from django.http import JsonResponse
from django.contrib import messages
from datetime import datetime
from django.shortcuts import get_object_or_404
from urllib.parse import quote
from django.views.decorators.csrf import csrf_exempt
import random
from django.contrib.auth.hashers import make_password
import json
from django.core.paginator import Paginator



def normalize_phone(phone):
    if not phone:
        return ""
    phone = phone.replace(" ", "").replace("+", "")
    if phone.startswith("0"):
        phone = "234" + phone[1:]
    return phone





def home(request):
    return render(request, 'home.html')


def register(request):
    form = RegisterForm()

    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if not form.is_valid():
            messages.error(request, "Please correct the errors below.")
            return render(request, 'register.html', {'form': form})

        phone = form.cleaned_data['phone']
        username = form.cleaned_data['username']

        if Vendor.objects.filter(phone=phone).exists():
            messages.error(
                request,
                "An account with this phone number already exists."
            )
            return render(request, 'register.html', {'form': form})

        if User.objects.filter(username=username).exists():
            messages.error(
                request,
                "This username is already taken."
            )
            return render(request, 'register.html', {'form': form})

        user = User.objects.create_user(
            username=username,
            password=form.cleaned_data['password']
        )

        Vendor.objects.create(
            user=user,
            phone=phone,
            business_name=form.cleaned_data['business_name'],
            address=form.cleaned_data['address'],
            country=form.cleaned_data['country']
        )

        login(request, user)
        messages.success(
            request,
            "Your account has been created successfully!"
        )
        return redirect('dashboard')

    return render(request, 'register.html', {'form': form})



def login_view(request):
    form = LoginForm()

    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        try:
            vendor = Vendor.objects.get(phone=phone)
        except Vendor.DoesNotExist:
            messages.error(
                request,
                "We couldn’t find an account with that phone number."
            )
            return render(request, 'login.html', {'form': form})

        user = authenticate(
            request,
            username=vendor.user.username,
            password=password
        )

        if user is None:
            messages.error(
                request,
                "Incorrect password. Please try again."
            )
            return render(request, 'login.html', {'form': form})

        login(request, user)
        messages.success(request, "Welcome back!")
        return redirect('dashboard')

    return render(request, 'login.html', {'form': form})



# -------------------------------
# Dashboard View
# -------------------------------
@login_required
def dashboard(request):
    vendor = Vendor.objects.get(user=request.user)


    # Search / filter
    query = request.GET.get('q')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')


    product_qs = Product.objects.filter(vendor=vendor)


    if query:
        product_qs = product_qs.filter(name__icontains=query)
    if start_date:
        product_qs = product_qs.filter(created_at__gte=start_date)
    if end_date:
        product_qs = product_qs.filter(created_at__lte=end_date)


    # 🔹 Stats MUST use QuerySet
    total_products = product_qs.count()
    available_count = product_qs.filter(status='available').count()
    sold_count = product_qs.filter(status='sold').count()


    # 🔹 Pagination (display only)
    paginator = Paginator(product_qs.order_by('-created_at'), 5)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)


    context = {
    'vendor': vendor,
    'products': products, # paginated
    'total_products': total_products,
    'available_count': available_count,
    'sold_count': sold_count,
    'subscription': vendor.subscription,
    'current_year': datetime.now().year,
    }


    return render(request, 'dashboard.html', context)

# -------------------------------
# Update Vendor Info
# -------------------------------
@login_required
def update_vendor(request):
    if request.method == "POST":
        vendor = Vendor.objects.get(user=request.user)

        vendor.business_name = request.POST.get('business_name')
        vendor.address = request.POST.get('address')
        vendor.country = request.POST.get('country')

        # Logo upload
        if 'logo' in request.FILES:
            vendor.logo.save(request.FILES['logo'].name, request.FILES['logo'], save=False)
        vendor.save()

        # Password change
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if new_password and new_password == confirm_password:
            request.user.set_password(new_password)
            request.user.save()

        vendor.save()
        messages.success(request, "Account updated successfully!")
        return redirect('dashboard')
    return redirect('dashboard')

# -------------------------------
# Get Product Data (for Edit Modal)
# -------------------------------
from django.http import JsonResponse

@login_required
def get_product(request, id):
    product = Product.objects.get(id=id)
    if product.vendor.user != request.user:
        return JsonResponse({"error": "Sorry, you’re not allowed to access this product."}, status=403)
    data = {
        "id": product.id,
        "name": product.name,
        "price": float(product.price),
        "description": product.description,
        "status": product.status,
    }
    return JsonResponse(data)

# -------------------------------
# Update Product
# -------------------------------
@login_required
def update_product(request):
    if request.method != "POST":
        messages.error(request, "Invalid request.")
        return redirect('dashboard')

    product_id = request.POST.get('product_id')
    product = get_object_or_404(Product, id=product_id)

    if product.vendor.user != request.user:
        messages.error(request, "Sorry, that product doesn’t belong to you.")
        return redirect('dashboard')

    product.name = request.POST.get('name')
    product.price = request.POST.get('price')
    product.description = request.POST.get('description')
    product.status = request.POST.get('status')
    product.save()

    messages.success(request, "Product updated successfully!")
    return redirect('dashboard')


# -------------------------------
# Toggle Sold/Available
# -------------------------------
@login_required
def toggle_product(request, id):
    if request.method != "POST":
        messages.error(request, "Invalid request.")
        return redirect('dashboard')

    product = get_object_or_404(Product, id=id)

    if product.vendor.user != request.user:
        messages.error(request, "Sorry, you can’t modify this product.")
        return redirect('dashboard')

    product.status = 'sold' if product.status == 'available' else 'available'
    product.save()

    messages.success(request, "Product status updated.")
    return redirect('dashboard')


# -------------------------------
# Delete Product
# -------------------------------
@login_required
def delete_product(request, id):
    if request.method != "POST":
        messages.error(request, "Invalid request.")
        return redirect('dashboard')

    product = get_object_or_404(Product, id=id)

    if product.vendor.user != request.user:
        messages.error(request, "Sorry, you can’t delete this product.")
        return redirect('dashboard')

    product.delete()
    messages.success(request, "Product deleted successfully!")
    return redirect('dashboard')


# -------------------------------
# Manage Images
# -------------------------------
@login_required
def product_images(request, id):
    product = get_object_or_404(Product, id=id)

    if product.vendor.user != request.user:
        return JsonResponse(
            {"error": "Sorry, you’re not allowed to view these images."},
            status=403
        )

    images = [{"id": img.id, "url": img.image.url} for img in product.images.all()]
    return JsonResponse({"images": images})


@login_required
def add_product_images(request):
    if request.method != "POST":
        messages.error(request, "Invalid request.")
        return redirect('dashboard')

    product_id = request.POST.get('product_id')
    product = get_object_or_404(Product, id=product_id)

    if product.vendor.user != request.user:
        messages.error(request, "Sorry, you can’t add images to this product.")
        return redirect('dashboard')

    files = request.FILES.getlist('images')
    if not files:
        messages.error(request, "Please select at least one image.")
        return redirect('dashboard')

    for f in files:
        ProductImage.objects.create(product=product, image=f)

    messages.success(request, "Images added successfully!")
    return redirect('dashboard')


@login_required
def delete_image(request, id):
    img = get_object_or_404(ProductImage, id=id)

    if img.product.vendor.user != request.user:
        return JsonResponse(
            {"error": "Sorry, you can’t delete this image."},
            status=403
        )

    img.delete()
    return JsonResponse({"success": True})

    

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def add_product(request):
    vendor = Vendor.objects.get(user=request.user)
    product_count = Product.objects.filter(vendor=vendor).count()

    if vendor.subscription == 'free' and product_count >= 5:
        messages.error(request, "You’ve reached your product limit. Please upgrade.")
        return redirect('upgrade')

    if vendor.subscription == 'basic' and product_count >= 100:
        messages.error(request, "You’ve reached your product limit. Please upgrade.")
        return redirect('upgrade')

    form = ProductForm()

    if request.method == 'POST':
        form = ProductForm(request.POST)
        files = request.FILES.getlist('images')

        if form.is_valid():
            product = form.save(commit=False)
            product.vendor = vendor
            product.save()

            for f in files:
                ProductImage.objects.create(product=product, image=f)

            messages.success(request, "Product added successfully!")
            return redirect('my_products')

        messages.error(request, "Please fix the errors below.")

    return render(request, 'add_product.html', {'form': form})



@login_required
def my_products(request):
    vendor = Vendor.objects.get(user=request.user)

    product_list = Product.objects.filter(vendor=vendor).order_by('-created_at')
    paginator = Paginator(product_list, 6)

    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    return render(request, 'my_products.html', {
        'products': products
    })

# ----------------------------
# WhatsApp Phone Normalizer
# ----------------------------
def normalize_whatsapp_phone(phone):
    """
    Normalize phone number for wa.me links:
    - Remove '+', spaces, dashes, parentheses
    - Ensure only digits remain
    """
    phone = ''.join(c for c in phone if c.isdigit())
    return phone


# ----------------------------
# Storefront view
# ----------------------------
def storefront(request, vendor_slug):
    vendor = get_object_or_404(Vendor, slug=vendor_slug)
    products = Product.objects.filter(
        vendor=vendor,
        status='available'
    ).order_by('-created_at')

    # Filters
    q = request.GET.get('q')
    if q:
        products = products.filter(name__icontains=q)
    min_price = request.GET.get('min_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    max_price = request.GET.get('max_price')
    if max_price:
        products = products.filter(price__lte=max_price)
    start_date = request.GET.get('start_date')
    if start_date:
        products = products.filter(created_at__date__gte=start_date)
    end_date = request.GET.get('end_date')
    if end_date:
        products = products.filter(created_at__date__lte=end_date)

    # WhatsApp phone normalization
    vendor_phone_digits = normalize_whatsapp_phone(vendor.phone)

    # Prefilled message
    prefill_msg = f"Hello, I am interested in your store: {vendor.business_name}. Please share details."
    prefill_msg_encoded = quote(prefill_msg)  # URL encode properly
    
    paginator = Paginator(products, 6) # storefront grid
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    return render(request, 'storefront.html', {
        'vendor': vendor,
        'products': products,
        'current_year': datetime.now().year,
        'prefill_msg_encoded': prefill_msg_encoded,
        'vendor_phone_digits': vendor_phone_digits
    })


@login_required
def upgrade(request):
    vendor = Vendor.objects.get(user=request.user)

    base_message = f"""
Hello, I want to upgrade my WACatalog plan.

Business Name: {vendor.business_name}
Phone: {vendor.phone}
Current Plan: {vendor.subscription}

Please send account details.
"""

    context = {
        'vendor': vendor,
        'message_basic': quote(base_message + "\nPlan: BASIC"),
        'message_pro': quote(base_message + "\nPlan: PRO"),
    }

    return render(request, 'upgrade.html', context)


# -----------------------------
# Forgot Password
# -----------------------------


@csrf_exempt
def verify_otp(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    try:
        data = json.loads(request.body)
        username = data.get("username")
        phone = data.get("phone")
        otp_code = data.get("otp")
        new_password = data.get("new_password")
    except:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not all([username, phone, otp_code, new_password]):
        return JsonResponse({"error": "Missing fields"}, status=400)

    try:
        vendor = Vendor.objects.get(user__username=username, phone=phone)
    except Vendor.DoesNotExist:
        return JsonResponse({"error": "Vendor not found"}, status=404)

    try:
        otp = PasswordResetOTP.objects.get(vendor=vendor, otp_code=otp_code, used=False)
    except PasswordResetOTP.DoesNotExist:
        return JsonResponse({"error": "Invalid or used OTP"}, status=403)

    if not otp.is_valid():
        return JsonResponse({"error": "OTP expired"}, status=403)

    # Reset password
    vendor.user.set_password(new_password)
    vendor.user.save()
    otp.mark_used()

    return JsonResponse({"status": "ok", "message": "Password successfully reset"})


def otp_confirm_view(request, token):
    otp = get_object_or_404(PasswordResetOTP, token=token)

    if not otp.is_valid():
        return render(request, 'otp_invalid.html')

    # OTP is valid, redirect to reset password page
    return redirect('reset_password', token=otp.token)


def reset_password_page(request, token):
    otp = get_object_or_404(PasswordResetOTP, token=token)

    if not otp.is_valid():
        return render(request, 'otp_invalid.html')

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            return render(request, 'reset_password.html', {
                'error': "Passwords do not match",
                'token': token
            })

        # Reset password
        user = otp.vendor.user
        user.set_password(new_password)
        user.save()

        # Mark OTP as used
        otp.mark_used()

        return redirect('login')  # Redirect to login page

    return render(request, 'reset_password.html', {'token': token})


def product_detail(request, vendor_slug, product_slug):
    vendor = get_object_or_404(Vendor, slug=vendor_slug)
    product = get_object_or_404(
        Product,
        vendor=vendor,
        slug=product_slug
    )

    return render(request, 'product_detail.html', {
        'vendor': vendor,
        'product': product
    })