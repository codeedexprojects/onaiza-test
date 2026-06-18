from django.contrib import admin

from offers.models import *

admin.site.register(Offers)
admin.site.register(VoucherCode)
admin.site.register(DealOfDay)