from django.contrib import admin
from django.contrib.sessions.models import Session

from customers.models import *


class UserOtpDataAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'phone', 'otp', 'resend_otp_index' , 'attempts']
admin.site.register(UserOtpData, UserOtpDataAdmin)

admin.site.register(Customer)
admin.site.register(PrivilegePoint)
admin.site.register(Session)
admin.site.register(Ticket)
admin.site.register(CustomerAddress)
