from django.contrib import admin
from orders.models import *

admin.site.register(Orders)
admin.site.register(OrderItem)
admin.site.register(Booking)