from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
import uuid
from datetime import timedelta
from django.utils import timezone
from cloudinary_storage.storage import MediaCloudinaryStorage



class Vendor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    phone = models.CharField(max_length=20, unique=True)
    business_name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True, blank=True)
    address = models.CharField(max_length=200)
    country = models.CharField(max_length=60)
    logo = models.ImageField(
        upload_to='logos/',
        storage=MediaCloudinaryStorage(),
        blank=True,
        null=True
    )
    
    SUBSCRIPTION_CHOICES = (
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('pro', 'Pro'),
    )

    subscription = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_CHOICES,
        default='free'
    )
    
    subscription_started_at = models.DateTimeField(null=True, blank=True)
    subscription_expires_at = models.DateTimeField(null=True, blank=True)


    is_early_vendor = models.BooleanField(default=False) # for badge


    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            # ensure uniqueness by appending user ID if needed
            base_slug = slugify(self.business_name)
            slug = base_slug
            counter = 1
            while Vendor.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.business_name

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)

    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=180, blank=True, db_index=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    views = models.PositiveIntegerField(default=0)

    STATUS = (
        ('available', 'Available'),
        ('sold', 'Sold'),
    )

    status = models.CharField(max_length=20, choices=STATUS, default='available')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(
                vendor=self.vendor,
                slug=slug
            ).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )

    image = models.ImageField(
        upload_to='products/',
        storage=MediaCloudinaryStorage()
    )

    def __str__(self):
        return f"Image for {self.product.name}"


class PasswordResetOTP(models.Model):
    vendor = models.ForeignKey('Vendor', on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    token = models.UUIDField(default=uuid.uuid4, unique=True)  # For URL-based reset
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.used and timezone.now() < self.expires_at

    def mark_used(self):
        self.used = True
        self.save()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        if not self.otp_code:
            import random
            self.otp_code = f"{random.randint(100000, 999999)}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.vendor.business_name} OTP ({self.otp_code})"