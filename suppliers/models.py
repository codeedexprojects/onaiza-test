from __future__ import unicode_literals
from django.db import models
from django.utils.translation import ugettext_lazy as _
from main.models import BaseModel
from decimal import Decimal
from django.core.validators import MinValueValidator


OPENING_TYPE = (
    ('debit', 'Debit'),
    ('credit', 'Credit')
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


class Supplier(BaseModel):
    name = models.CharField(max_length=128)
    address = models.TextField()
    phone = models.CharField(max_length=128)
    email = models.EmailField(null=True, blank=True)

    bank_name = models.CharField(max_length=128, blank=True, null=True)
    bank_account_name = models.CharField(max_length=128, blank=True, null=True)
    branch = models.CharField(max_length=128, blank=True, null=True)
    ifsc_code = models.CharField(max_length=128, blank=True, null=True)
    account_num = models.CharField(max_length=128, blank=True, null=True)
    opening_type = models.CharField(
        max_length=128, choices=OPENING_TYPE, default="debit")
    opening_balance = models.DecimalField(default=0, decimal_places=2, max_digits=15, validators=[
                                          MinValueValidator(Decimal('0.00'))])
    credit_limit = models.DecimalField(default=0, decimal_places=2, max_digits=15, validators=[
                                          MinValueValidator(Decimal('0.00'))])
    debit_limit = models.DecimalField(default=0, decimal_places=2, max_digits=15, validators=[
                                          MinValueValidator(Decimal('0.00'))])
    user = models.OneToOneField(
        "auth.User", on_delete=models.CASCADE, blank=True, null=True)
    state = models.CharField(choices=STATE, default="Kerala", max_length=128)
    gst_number = models.CharField(max_length=128, blank=True, null=True)

    district = models.CharField(max_length=128)
    country = models.CharField(max_length=128)
    current_balance = models.DecimalField(
        default=0, decimal_places=2, max_digits=15)

    class Meta:
        db_table = 'suppliers_supplier'
        verbose_name = _('supplier')
        verbose_name_plural = _('suppliers')

    def __str__(self):
        return str(self.name)

    def get_balance_data(self):
        if self.current_balance < 0:
            return {'balance_type': 'Credit',
                    'balance': abs(self.current_balance), }
        else:
            return {'balance_type': 'Debit',
                    'balance': self.current_balance, }
