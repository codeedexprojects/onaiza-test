from django.db import models
from django.db import models
from decimal import Decimal
from django.db.models import Sum, manager
from django.core.validators import MinValueValidator
from django.utils.translation import ugettext_lazy as _
from main.models import BaseModel
from versatileimagefield.fields import VersatileImageField
import datetime


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


class Warehouse(BaseModel):
    name = models.CharField(max_length=128)
    # location = models.CharField(max_length=128)
    location = models.ManyToManyField('warehouses.Location', blank=True)
    manager = models.ForeignKey("staffs.Staff", null=True, blank=True, limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE, related_name='manager')

    phone = models.CharField(max_length=128)
    address = models.TextField()
    district = models.CharField(max_length=128)
    state = models.CharField(choices=STATE, default="Kerala", max_length=128)
    country = models.CharField(max_length=128)

    class Meta:
        db_table = 'warehouse'
        verbose_name = _('Warehouse')
        verbose_name_plural = _('Warehouse')
        ordering = ('auto_id',)

    def __str__(self):
        return str(self.name)


class Location(BaseModel):
    name = models.CharField(max_length=128)
    malayalam_name = models.CharField(max_length=128,null=True,blank=True)
    pincode = models.CharField(max_length=128)
    latitude = models.CharField(max_length=128,blank=True,null=True)
    longitude = models.CharField(max_length=128,blank=True,null=True)

    class Meta:
        db_table = 'location'
        verbose_name = _('Location')
        verbose_name_plural = _('Location')
        ordering = ('auto_id',)

    def __str__(self):
        return f'{self.name} - {self.pincode}'
