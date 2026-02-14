from django.urls import path
from .views import *

from django.conf.urls import handler404, handler500, handler403, handler400

handler404 = 'myapp.views.custom_404'
handler500 = 'myapp.views.custom_500'
handler403 = 'myapp.views.custom_403'
handler400 = 'myapp.views.custom_400'

urlpatterns = [
    path('', home, name='home'),
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('dashboard/', dashboard, name='dashboard'),
    path('store/<slug:vendor_slug>/', storefront, name='storefront'),
    path('update_vendor/', update_vendor, name='update_vendor'),
    path('logout/', logout_view, name='logout'),
    path('products/add/', add_product, name='add_product'),
    path('products/', my_products, name='my_products'),
    path('products/toggle/<int:id>/', toggle_product, name='toggle_product'),
    path('products/get/<int:id>/', get_product, name='get_product'),
    path('products/update/', update_product, name='update_product'),
    path('products/images/<int:id>/', product_images, name='product_images'),
    path('products/images/delete/<int:id>/', delete_image, name='delete_image'),
    path('products/delete/<int:id>/', delete_product, name='delete_product'),
    path('products/images/add/', add_product_images, name='add_product_images'),
    path('store/<int:vendor_id>/', storefront, name='storefront'),
    path('upgrade/', upgrade, name='upgrade'),
    path('api/reset/password/', verify_otp, name='verify_otp'),
    path('otp/confirm/<uuid:token>/', otp_confirm_view, name='otp_confirm'),
    path('reset-password/<uuid:token>/', reset_password_page, name='reset_password'),
    
    path('store/<slug:vendor_slug>/product/<slug:product_slug>/', product_detail, name='product_detail'),

    path('how-it-works/', how_it_works, name='how_it_works'),
    path('about/', about, name='about'),
    path('terms/', terms, name='terms'),
    path('privacy/', privacy, name='privacy'),
    
    path('blog/', blog_list, name='blog_list'),
    path('blog/<slug:slug>/', blog_detail, name='blog_detail'),
    
    
    # marketplace
    path('marketplace/vendors/', marketplace_vendors, name='marketplace_vendors'),
    path('marketplace/products/', marketplace_products, name='marketplace_products'),
    path('marketplace/', marketplace_home, name='marketplace_home'),


]
