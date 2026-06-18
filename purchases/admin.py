from django.contrib import admin

from purchases.models import *

admin.site.register(Purchase)
admin.site.register(PurchaseItem)