from django.contrib import admin
from products.models import *
from main.models import AppUpdate


admin.site.register(ProductImages)

class AppUpdateAdmin(admin.ModelAdmin):
    list_display = ['id', 'version', 'force_update', 'update_recomented']
admin.site.register(AppUpdate, AppUpdateAdmin)
