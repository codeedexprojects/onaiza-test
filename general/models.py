from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
from main.models import BaseModel
from versatileimagefield.fields import VersatileImageField
import uuid
from products.models import *


STOCK_UPDATE_TYPE_STATUS = (
    ('inward', 'Inward'),
    ('outward', 'Outward'),
)


class Batch(BaseModel):
    product = models.ForeignKey("products.Product", limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    product_variant = models.ForeignKey('products.ProductVariant', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    warehouse = models.ForeignKey("warehouses.Warehouse", limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)

    batch_number = models.CharField(max_length=128, blank=True)
    stock = models.DecimalField(default=0.0, decimal_places=3, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])

    mrp = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    retail_price = models.DecimalField(default=0, decimal_places=3, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    whole_sale_price = models.DecimalField(default=0, decimal_places=3, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    cost = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    manufacturing_date = models.DateField(null=True, blank=True)
    expire_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'general_batch'
        verbose_name = _('general_batch')
        verbose_name_plural = _('general_batchs')
        ordering = ('expire_date', 'mrp', )

    def __str__(self):
        return f'{self.batch_number}'

    # def save(self, *args, **kwargs):
    #     for field_name in ['batch_number']:
    #         val = getattr(self, field_name, False)
    #     super(Batch, self).save(*args, **kwargs)

    # def get_variant(self):


class DamagedProducts(BaseModel):
    date = models.DateTimeField()
    product_variant = models.ForeignKey("products.ProductVariant", limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    quantity = models.DecimalField(default=0.0, decimal_places=3, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    amount = models.DecimalField(default=0.0, decimal_places=3, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    description = models.TextField(blank=True, null=True)
    warehouse = models.ForeignKey("warehouses.Warehouse", null=True, blank=True, limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    batch = models.ForeignKey('general.Batch', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        db_table = 'general_damaged_product'
        verbose_name = _('Damaged Product')
        verbose_name_plural = _('Damaged Products')
        ordering = ('-auto_id',)

    def __str__(self):
        return f'{self.product_variant} - {self.quantity}'


class UserBaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date_added = models.DateTimeField(db_index=True, auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True


class StockTransfer(BaseModel):
    warehouse = models.ForeignKey("warehouses.Warehouse", limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE, related_name='warehouses')
    to_warehouse = models.ForeignKey("warehouses.Warehouse", limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE, related_name="to_warehouses")
    date = models.DateTimeField()

    class Meta:
        db_table = 'stock_transfer'
        verbose_name = _('stock_transfer')
        verbose_name_plural = _('stock_transfers')

    def __str__(self):
        return str(self.date)


class StockTransferItem(BaseModel):
    stock_transfer = models.ForeignKey("general.StockTransfer", null=True, blank=True, limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    product_variant = models.ForeignKey("products.ProductVariant", null=True, blank=True, limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    batch = models.ForeignKey('general.Batch', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE, blank=True, null=True)

    retail_price = models.DecimalField(default=0, decimal_places=3, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    whole_sale_price = models.DecimalField(default=0, decimal_places=3, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    cost = models.DecimalField(decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    mrp = models.DecimalField(decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    quantity = models.DecimalField(decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])

    manufacturing_date = models.DateField()
    expire_date = models.DateField()

    class Meta:
        db_table = 'stock_transfer_items'
        verbose_name = _('stock_transfer_item')
        verbose_name_plural = _('stock_transfer_items')
        ordering = ('auto_id',)

    def __str__(self):
        return str(self.product_variant)

class ChargePerKilometer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    charge = models.DecimalField(default=0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])

    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'general_charge_per_kilometer'
        verbose_name = _('charge per kilometer')
        verbose_name_plural = _('charges per kilometer')

    def __unicode__(self):
        return str(self.id)


class InvoiceDesign(BaseModel):
    warehouse = models.ForeignKey("warehouses.Warehouse",  limit_choices_to={
        'is_deleted': False}, on_delete=models.CASCADE)
    title = models.CharField(max_length=128)
    image = VersatileImageField(upload_to="media/", blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
 

    class Meta:
        db_table = 'invoice_design'
        verbose_name = _('Invoice Design')
        verbose_name_plural = _('Invoice Designs')
        ordering = ('title',)

    def __str__(self):
        return str(self.title)


class StockUpdate(BaseModel):
    warehouse = models.ForeignKey("warehouses.Warehouse",  limit_choices_to={
        'is_deleted': False}, on_delete=models.CASCADE)
    date = models.DateTimeField()
    description = models.CharField(max_length=128,blank=True)
    update_type = models.CharField(max_length=128, choices=STOCK_UPDATE_TYPE_STATUS, default="inward")

    class Meta:
        db_table = 'stock_update'
        verbose_name = _('stock_update')
        verbose_name_plural = _('stock_updates')

    def __str__(self):
        return f'#{self.auto_id}'


class StockUpdateItem(models.Model):
    stockupdate = models.ForeignKey("general.StockUpdate", limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    # product = models.ForeignKey("products.Product", limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    product_variant = models.ForeignKey('products.ProductVariant', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE, blank=True, null=True)
    batch = models.ForeignKey('general.Batch', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE, blank=True, null=True)

    add_new_batch = models.BooleanField(default=False)
    batch_number = models.CharField(max_length=128, blank=True, null=True)
    expire_date = models.DateField()
    manufacturing_date = models.DateField(blank=True, null=True)

    stock = models.DecimalField(default=0.0, decimal_places=3, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    mrp = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    cost = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    taxable_amount = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    retail_price = models.DecimalField(default=0, decimal_places=3, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    whole_sale_price = models.DecimalField(default=0, decimal_places=3, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])    
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'stock_update_item'
        verbose_name = _('stock_update_item')
        verbose_name_plural = _('stock_update_items')

    def __str__(self):
        return f'{self.batch_number}'

    def save(self, *args, **kwargs):
        for field_name in ['batch_number']:
            val = getattr(self, field_name, False)
            # if val:
            #     setattr(self, field_name, val.upper())
        super(StockUpdateItem, self).save(*args, **kwargs)

