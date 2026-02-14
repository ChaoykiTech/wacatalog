from django.db import models

class MarketplaceVendorQuerySet(models.QuerySet):
    def eligible(self):
        return self.filter(subscription__in=['basic', 'pro'])
