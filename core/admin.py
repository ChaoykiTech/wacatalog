from django.contrib import admin
from django.urls import path
from django.template.response import TemplateResponse
from datetime import datetime

from .models import Vendor, Product, ProductImage, PasswordResetOTP

from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django import forms
from django.utils.html import format_html
from django.urls import reverse
from .models import Category


# ----------------------------
# PRODUCT IMAGE INLINE
# ----------------------------
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


# ----------------------------
# PRODUCT ADMIN
# ----------------------------
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'vendor', 'price', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'vendor__business_name')
    inlines = [ProductImageInline]


# ----------------------------
# VENDOR ADMIN
# ----------------------------
class VendorAdmin(admin.ModelAdmin):

    list_display = (
        'business_name',
        'phone',
        'country',
        'product_count',
        'subscription',
        'created_at'
    )

    search_fields = ('business_name', 'phone', 'country')

    list_filter = ('country', 'subscription', 'created_at')

    readonly_fields = ('created_at',)

    def product_count(self, obj):
        return obj.product_set.count()

    product_count.short_description = "Total Products"


# ----------------------------
# CUSTOM ADMIN SITE
# ----------------------------
class WacatalogAdminSite(admin.AdminSite):
    site_header = "WACatalog Admin"
    site_title = "WACatalog Control Panel"
    index_title = "Platform Management"

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path('stats/', self.admin_view(self.stats_view), name="stats"),
        ]

        return custom_urls + urls

    # ------------------------
    # STATS VIEW
    # ------------------------
    def stats_view(self, request):

        context = dict(
            self.each_context(request),

            total_vendors=Vendor.objects.count(),
            total_products=Product.objects.count(),

            new_today=Vendor.objects.filter(
                created_at__date=datetime.now().date()
            ).count(),

            free=Vendor.objects.filter(subscription='free').count(),
            basic=Vendor.objects.filter(subscription='basic').count(),
            pro=Vendor.objects.filter(subscription='pro').count(),

            current_year=datetime.now().year,
        )

        return TemplateResponse(request, "admin/stats.html", context)


class PasswordResetOTPForm(forms.ModelForm):
    username = forms.CharField(label="Username", required=True)
    phone = forms.CharField(label="Phone number", required=True)

    class Meta:
        model = PasswordResetOTP
        fields = ['username', 'phone']

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        phone = cleaned_data.get("phone")

        try:
            vendor = Vendor.objects.get(user__username=username, phone=phone)
            cleaned_data['vendor'] = vendor
        except Vendor.DoesNotExist:
            raise forms.ValidationError("No vendor found with this username and phone number.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.vendor = self.cleaned_data['vendor']
        if commit:
            instance.save()
        return instance
    

@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
    form = PasswordResetOTPForm
    list_display = ('vendor', 'otp_code', 'reset_link', 'created_at', 'expires_at', 'used')
    readonly_fields = ('otp_code', 'token', 'created_at', 'expires_at', 'reset_link')

    def reset_link(self, obj):
        if obj.token:
            url = reverse('otp_confirm', args=[obj.token])
            full_url = f"http://127.0.0.1:8000{url}"
            return format_html('<a href="{}" target="_blank">{}</a>', full_url, full_url)
        return "-"
    reset_link.short_description = "Password Reset URL"
    
    
# ----------------------------
# ACTIVATE CUSTOM ADMIN
# ----------------------------
admin_site = WacatalogAdminSite(name='wacatalog')

admin_site.register(Product, ProductAdmin)
admin_site.register(Vendor, VendorAdmin)
admin_site.register(User, UserAdmin)
admin_site.register(PasswordResetOTP, PasswordResetOTPAdmin)
admin_site.register(Category)