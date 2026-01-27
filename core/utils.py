from django.utils import timezone


def check_and_downgrade_vendor(vendor):
    if vendor.subscription != 'free' and vendor.subscription_expires_at:
        if vendor.subscription_expires_at < timezone.now():
            vendor.subscription = 'free'
            vendor.subscription_started_at = None
            vendor.subscription_expires_at = None
            vendor.save()