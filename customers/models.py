from __future__ import unicode_literals
from django.db import models
from django.utils.translation import ugettext_lazy as _
import os
import uuid
from main.models import BaseModel
from decimal import Decimal
from general.models import UserBaseModel
from warehouses.models import Location
from django.core.validators import MinValueValidator
from versatileimagefield.fields import VersatileImageField


OPENING_TYPE = (
    ('debit', 'Debit'),
    ('credit', 'Credit')
)

CATEGORY = (
    ('b2b', 'B2B'),
    ('b2c', 'B2C')
)

STATE = (
    ('Kerala', 'Kerala'),
    ('Tamil Nadu', 'Tamil Nadu'),
    ('Karnataka', 'Karnataka'),
    ('Andaman and Nicobar Islands', 'Andaman and Nicobar Islands'),
    ('Andhra Pradesh', 'Andhra Pradesh'),
    ('Arunachal Pradesh', 'Arunachal Pradesh'),
    ('Assam', 'Assam'),
    ('Bihar', 'Bihar'),
    ('Chandigarh', 'Chandigarh'),
    ('Chhattisgarh', 'Chhattisgarh'),
    ('Dadra and Nagar Haveli ', 'Dadra and Nagar Haveli '),
    ('Daman and Diu', 'Daman and Diu'),
    ('National Capital Territory of Delhi', 'National Capital Territory of Delhi'),
    ('Goa', 'Goa'),
    ('Gujarat', 'Gujarat'),
    ('Haryana', 'Haryana'),
    ('Himachal Pradesh', 'Himachal Pradesh'),
    ('Jammu and Kashmir', 'Jammu and Kashmir'),
    ('Jharkhand', 'Jharkhand'),
    ('Lakshadweep union territory', 'Lakshadweep union territory'),
    ('Madhya Pradesh', 'Madhya Pradesh'),
    ('Maharashtra', 'Maharashtra'),
    ('Manipur', 'Manipur'),
    ('Meghalaya', 'Meghalaya'),
    ('Mizoram', 'Mizoram'),
    ('Nagaland', 'Nagaland'),
    ('Odisha', 'Odisha'),
    ('Puducherry union territory', 'Puducherry union territory'),
    ('Punjab', 'Punjab'),
    ('Rajasthan', 'Rajasthan'),
    ('Sikkim', 'Sikkim'),
    ('Telangana', 'Telangana'),
    ('Tripura', 'Tripura'),
    ('Uttar Pradesh', 'Uttar Pradesh'),
    ('Uttarakhand', 'Uttarakhand'),
    ('West Bengal', 'West Bengal')
)

TICKET_STATUS = (
    ('pending', 'Pending'),
    ('in_progress', 'In Progress'),
    ('rejected', 'Rejected'),
    ('solved', 'Solved'),
)

ADDRESS_TYPE = (
    (10, "Home"),
    (20, "Office"),
)


class Customer(BaseModel):
    user = models.OneToOneField("auth.User", on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=128)
    phone = models.CharField(max_length=128)
    email = models.EmailField(blank=True, null=True)
    customer_type = models.CharField(choices=CATEGORY, default="b2c", max_length=128)
    address = models.TextField(blank=True, null=True)
    gst_number = models.CharField(max_length=128, blank=True, null=True)
    district = models.CharField(max_length=128, blank=True, null=True)
    state = models.CharField(choices=STATE, default="Kerala", max_length=128, blank=True, null=True)
    country = models.CharField(max_length=128, blank=True, null=True)

    opening_type = models.CharField(max_length=128, choices=OPENING_TYPE, default="debit", blank=True, null=True)
    opening_balance = models.DecimalField(default=0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    current_balance = models.DecimalField(default=0, decimal_places=2, max_digits=15)
    current_privilege_points = models.DecimalField(default=0, decimal_places=0, max_digits=15)
    privilege_points = models.DecimalField(default=0, decimal_places=0, max_digits=15)

    image = VersatileImageField(upload_to="customers/images/",null=True,blank=True)

    class Meta:
        db_table = 'customers_customer'
        verbose_name = _('customer')
        verbose_name_plural = _('customers')
        ordering = ('-date_added', 'name')

    def __str__(self):
        if self.address:
            return f'{self.auto_id} - {self.name} - {self.address}'
        else:
            return f'{self.auto_id} - {self.name}'

    def get_balance_data(self):
        if self.current_balance < 0:
            return {'balance_type': 'Credit',
                    'balance': abs(self.current_balance), }
        else:
            return {'balance_type': 'Debit',
                    'balance': self.current_balance, }


class CustomerAddress(UserBaseModel):
    pincode = models.ForeignKey(Location,on_delete=models.CASCADE, limit_choices_to={'is_deleted': False})
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, )
    address_type = models.IntegerField(choices=ADDRESS_TYPE)

    name = models.CharField(max_length=256, null=False)
    phone = models.CharField(max_length=10, null=False)
    email = models.EmailField(null=True, blank=True)

    house_name = models.TextField()
    street = models.CharField(max_length=256, null=False)
    city = models.CharField(max_length=256, null=False)
    landmark = models.CharField(max_length=256, null=False)
    state = models.CharField(max_length=256, null=False)

    is_default = models.BooleanField(default=True)

    class Meta:
        ordering = ('-is_default','name',)
        verbose_name = 'customer adress'
        verbose_name_plural = 'customer addresses'

    def __str__(self):
        return f"{self.house_name}, {self.street}, {self.city}, {self.state}, {self.landmark} - {self.address_type}"


class UserOtpData(models.Model):
    name = models.CharField(max_length=256)
    phone = models.CharField(max_length=16)
    otp = models.PositiveIntegerField()
    attempts = models.PositiveIntegerField(default=1)
    resend_otp_index = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    password = models.CharField(max_length=256, null=True,blank=True)

    class Meta:
        verbose_name = _('OTP Record')
        verbose_name_plural = _('OTP Records')

    def __str__(self):
        return self.phone


class PrivilegePoint(BaseModel):
    minimum_amount = models.DecimalField(decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    value_of_point = models.DecimalField(decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    point_gained_online = models.DecimalField(decimal_places=0, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    point_gained_offline = models.DecimalField(decimal_places=0, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])

    class Meta:
        db_table = 'privilege_points'
        verbose_name = _('privilege_point')
        verbose_name_plural = _('privilege_points')
        ordering = ('date_added', )

    def __str__(self):
        return str(self.value_of_point)



class Ticket(BaseModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, )

    subject = models.CharField(max_length=256, null=True)
    description = models.TextField(null=True,blank=True)

    status = models.CharField(max_length=50,choices=TICKET_STATUS)
    attachment = models.FileField(upload_to="tickets/attachment/",null=True,blank=True)

    reject_reason = models.CharField(max_length=256,null=True,blank=True)
    message = models.CharField(max_length=256,null=True,blank=True)

    class Meta:
        db_table = 'tickets'
        verbose_name = _('ticket')
        verbose_name_plural = _('tickets')
        ordering = ('date_added', )

    def __str__(self):
        return f"{self.customer.name} - {self.subject}"