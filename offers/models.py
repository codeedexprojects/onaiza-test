
from __future__ import unicode_literals
from django.db import models
from django.utils.translation import ugettext_lazy as _
from main.models import BaseModel
from decimal import Decimal
from django.core.validators import MinValueValidator
from customers.models import Customer
from versatileimagefield.fields import VersatileImageField


OFFER_TYPE = (
    ('category', 'Category'),
    ('sub_category', 'Sub Category'),
    ('product', 'Product')
)

class Offers(BaseModel):
    warehouse = models.ForeignKey("warehouses.Warehouse", null=True, blank=True, limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    product_variant = models.ForeignKey("products.ProductVariant", null=True, blank=True, limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    subcategory = models.ForeignKey("products.SubCategory", null=True, blank=True, limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    category = models.ForeignKey("products.Category", null=True, blank=True, limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)

    title = models.CharField(max_length=128)
    offer_type = models.CharField(max_length=128, choices=OFFER_TYPE, default="category")
    # offer_percentage = models.CharField(max_length=128)
    offer_percentage = models.DecimalField(default=0, max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    image = VersatileImageField(upload_to="media/", blank=True, null=True)

    class Meta:
        db_table = 'offers'
        verbose_name = _('offer')
        verbose_name_plural = _('offers')

    def __str__(self):
        return str(self.title)


class DealOfDay(BaseModel):
    warehouse = models.ForeignKey("warehouses.Warehouse", null=True, blank=True, limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    product_variant = models.ForeignKey("products.ProductVariant", null=True, blank=True, limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    # offer_percentage = models.CharField(max_length=128)
    offer_percentage = models.DecimalField(default=0, max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    deal_date = models.DateField()

    class Meta:
        db_table = 'deal_of_day'
        verbose_name = _('deal_of_day')
        verbose_name_plural = _('deal_of_days')

    def __str__(self):
        return str(self.offer_percentage)


class VoucherCode(BaseModel):
    voucher_code = models.CharField(max_length=128)
    title = models.CharField(max_length=128)
    description = models.TextField()

    is_exclusive = models.BooleanField(default=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)

    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    minimum_order_amount = models.DecimalField(default=0, max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    upto_limit = models.DecimalField(default=0, max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    voucher_amount = models.DecimalField(default=0, max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    percentage = models.DecimalField(default=0, max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])

    is_expired = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('voucher code')
        verbose_name_plural = _('voucher codes')

    def __str__(self):
        return str(self.title)
