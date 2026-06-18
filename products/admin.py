from django.contrib import admin

from products.models import *


admin.site.register(ProductVariant)
admin.site.register(UnitOfMeasurement)
admin.site.register(Unit)
admin.site.register(HsnCodes)
admin.site.register(Category)
admin.site.register(SubCategory)
admin.site.register(Product)
admin.site.register(Brand)