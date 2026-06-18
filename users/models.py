from __future__ import unicode_literals
from django.db import models
from django.utils.translation import ugettext_lazy as _
from main.models import BaseModel
import uuid
from django.core.validators import RegexValidator
from django.core.validators import MinValueValidator
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.models import User
# from versatileimagefield.fields import VersatileImageField
from products.models import *
from customers.models import *
from warehouses.models import Warehouse

STATUS_CHOICES = (
    ("pending", "Pending"),
    ("logged_in", "Logged in"),
    ("failed", "Failed")
)


class RegistrationProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    auto_id = models.PositiveIntegerField(db_index=True, unique=True)
    phone = models.CharField(
        unique=True,
        max_length=16,
        validators=[
            RegexValidator(r'^\d{1,10}$')
        ]
    )
    date_added = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    user = models.OneToOneField(
        User,
        related_name="%(class)s_tarriff",
        on_delete=models.CASCADE
    )

    class Meta:
        db_table = 'students_registration_profile'
        verbose_name = _('Registration Profile')
        verbose_name_plural = _('Registration Profiles')

    def __unicode__(self):
        return self.phone


class UserLogin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    auto_id = models.PositiveIntegerField(db_index=True, unique=True)
    date_added = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField()
    user = models.ForeignKey(
        User,
        related_name="%(class)s_tarriff",
        on_delete=models.CASCADE
    )
    otp = models.CharField(max_length=4)
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default="pending"
    )
    failed_attempts = models.PositiveIntegerField(default=0)
    is_activated = models.BooleanField(default=False)

    class Meta:
        db_table = 'users_user_login'
        verbose_name = _('user login')
        verbose_name_plural = _('user logins')
        ordering = ('-date_added',)

    def __unicode__(self):
        return self.user


class Permission(models.Model):
    name = models.CharField(max_length=128)
    code = models.CharField(max_length=128)
    app = models.CharField(max_length=128)

    class Meta:
        db_table = 'permission'
        verbose_name = _('permission')
        verbose_name_plural = _('permissions')
        ordering = ('app',)

    class Admin:
        list_display = ('id', 'name', 'code', 'app')

    def __unicode__(self):
        return self.name + ' - ' + self.app


class Wishlistitem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date_added = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('wishlist item')
        verbose_name_plural = _('wishlist items')
        ordering = ('-date_added',)

    def __unicode__(self):
        return self.customer.name


class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date_added = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, null=True, blank=True)

    qty = models.IntegerField(default=1)

    class Meta:
        verbose_name = _('cart item')
        verbose_name_plural = _('cart items')
        ordering = ('-date_added',)

    def __unicode__(self):
        return self.customer.name

    def product_name(self):
        return self.product_variant.title


class Notification(models.Model):
    user = models.ForeignKey("auth.User", blank=True, null=True, related_name="user_%(class)s_objects", on_delete=models.CASCADE)
    who = models.ForeignKey("auth.User", blank=True, null=True, related_name="who_%(class)s_objects", on_delete=models.CASCADE)
    subject = models.ForeignKey("users.NotificationSubject", on_delete=models.CASCADE, blank=True, null=True)
    customer = models.ForeignKey("customers.Customer", null=True, blank=True, on_delete=models.CASCADE)

    message = models.CharField(max_length=128, null=True)
    time = models.DateTimeField(auto_now_add=True)

    is_read = models.BooleanField(default=False)
    is_visited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    class Meta:
        db_table = 'users_notification'
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        ordering = ('-time',)

    class Admin:
        list_display = ('subject',)

    def __str__(self):
        return self.message


class NotificationSubject(models.Model):
    code = models.CharField(max_length=128)
    name = models.CharField(max_length=128)

    class Meta:
        db_table = 'users_notification_subject'
        verbose_name = _('notification subject')
        verbose_name_plural = _('notification subjects')
        ordering = ('name',)

    class Admin:
        list_display = ('name',)

    def __str__(self):
        return self.name
