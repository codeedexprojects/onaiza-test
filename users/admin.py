from django.contrib import admin

from users.models import *


admin.site.register(Wishlistitem)
admin.site.register(CartItem)
admin.site.register(Notification)