from __future__ import unicode_literals
from django.db import models
from decimal import Decimal
from django.db.models import Sum
from django.core.validators import MinValueValidator
from django.utils.translation import ugettext_lazy as _
from main.models import BaseModel
from versatileimagefield.fields import VersatileImageField
# from general.models import Batch
import datetime
from django.utils import timezone


STATUS_PURCHASE_RETURN = (('returnable', 'Returnable'), ('damaged', 'Damaged'))


class Purchase(BaseModel):
    payment_voucher = models.OneToOneField('finance.PaymentVoucher', null=True, blank=True, limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    purchase_prifix = models.ForeignKey("finance.InvoicePrefix", null=True, blank=True, limit_choices_to={'is_deleted': False},related_name="purchase_prifix", on_delete=models.CASCADE)

    warehouse = models.ForeignKey("warehouses.Warehouse", null=True, blank=True, limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    supplier = models.ForeignKey('suppliers.Supplier', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    # user = models.OneToOneField("auth.user", blank=True, null=True, on_delete=models.CASCADE)
    # purchase_order = models.ForeignKey('purchases.PurchaseOrder', blank=True, null=True, on_delete=models.CASCADE)

    date = models.DateTimeField()
    purchase_no = models.PositiveIntegerField(unique=True, blank=True, null=True)
    purchase_id = models.CharField(max_length=128, blank=True, null=True)

    product_total = models.DecimalField(default=0, decimal_places=3, max_digits=30, validators=[MinValueValidator(Decimal('0.00'))])
    round_off = models.DecimalField(default=0, decimal_places=3, max_digits=30)
    discount = models.DecimalField(default=0, decimal_places=3, max_digits=30, validators=[MinValueValidator(Decimal('0.00'))])
    subtotal = models.DecimalField(default=0, decimal_places=3, max_digits=30, validators=[MinValueValidator(Decimal('0.00'))])
    paid = models.DecimalField(default=0, decimal_places=3, max_digits=30, validators=[MinValueValidator(Decimal('0.00'))])
    balance = models.DecimalField(default=0, decimal_places=3, blank=True, null=True, max_digits=30)

    add_gst = models.BooleanField(default=True)
    payment_method = models.CharField(max_length=123, blank=True, null=True)
    is_updated = models.BooleanField(default=False)

    class Meta:
        db_table = 'purchase'
        verbose_name = _('purchase')
        verbose_name_plural = _('purchases')
        ordering = ('-purchase_no', 'date',)

    def __str__(self):
        # return str(self.auto_id)
        return '%s - %s' % (self.purchase_id, self.date.date())

    def discount_amount(self):
        discount_amount = 0
        if self.discount > 0:
            discount_amount = (self.product_total * self.discount) / 100

        return round(discount_amount, 2)


class PurchaseItem(models.Model):
    purchase = models.ForeignKey('purchases.Purchase', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    product_variant = models.ForeignKey('products.ProductVariant', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE, blank=True, null=True)
    batch = models.ForeignKey('general.Batch', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE, blank=True, null=True)
    # product = models.ForeignKey('products.Product', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE, blank=True, null=True)

    add_new_batch = models.BooleanField(default=False)
    batch_number = models.CharField(max_length=128, blank=True, null=True)

    quantity = models.DecimalField(decimal_places=3, default=1.00, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    return_qty = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    expire_date = models.DateTimeField()
    manufacturing_date = models.DateField()
    discount = models.DecimalField(decimal_places=2, default=0.00, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    tax_amount = models.DecimalField(decimal_places=2, default=0.00, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    net_rate = models.DecimalField(decimal_places=2, default=0.00, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])

    mrp = models.DecimalField(decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    retail_price = models.DecimalField(default=0, decimal_places=3, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    whole_sale_price = models.DecimalField(default=0, decimal_places=3, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    amount = models.DecimalField(decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])

    hsn = models.CharField(max_length=128, blank=True, null=True)
    tax = models.DecimalField(decimal_places=3, default=0.00, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    comments = models.CharField(max_length=128, blank=True, null=True)
    unit_type = models.CharField(max_length=128, blank=True, null=True)

    total = models.DecimalField(decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    cgst_amount = models.DecimalField(decimal_places=2, default=0.00, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    sgst_amount = models.DecimalField(decimal_places=2, default=0.00, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    igst_amount = models.DecimalField(decimal_places=2, default=0.00, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    gross_amount = models.DecimalField(decimal_places=2, default=0.00, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])

    def subtotal(self):
        return (self.quantity * self.amount)

    class Meta:
        db_table = 'purchase_item'
        verbose_name = _('purchase_item')
        verbose_name_plural = _('purchase_items')
        ordering = ('id',)

    def __str__(self):
        return str(self.product_variant)


class PurchaseReturn(BaseModel):
    date = models.DateField()
    supplier = models.ForeignKey('suppliers.Supplier', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    purchase = models.ForeignKey('purchases.Purchase', blank=True, null=True,on_delete=models.CASCADE, limit_choices_to={"is_deleted": False})
    total = models.DecimalField(default=0.0, max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.0'))])
    amount_returned = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])

    is_updated = models.BooleanField(default=False)

    class Meta:
        db_table = 'purchase_return'
        verbose_name = ('Purchase Return')
        verbose_name_plural = ('Purchase Returns')
        ordering = ('-date_added', 'supplier')

    def __str__(self):
        return f"Purchase Return {self.auto_id} of {self.purchase}"


class PurchaseReturnItem(models.Model):
    purchase_return = models.ForeignKey('purchases.PurchaseReturn', blank=True,null=True, on_delete=models.CASCADE, limit_choices_to={"is_deleted": False})
    batch = models.ForeignKey('general.Batch', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE, blank=True, null=True)
    product = models.ForeignKey("products.Product", limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    purchase_item = models.ForeignKey("purchases.PurchaseItem", limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    product_variant = models.ForeignKey('products.ProductVariant', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE, blank=True, null=True)

    quantity = models.DecimalField(default=0.0, max_digits=15, decimal_places=3, validators=[MinValueValidator(Decimal('0.0'))])
    amount = models.DecimalField(default=0.0, max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.0'))])
    total = models.DecimalField(default=0.0, max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.0'))])

    status = models.CharField(
        max_length=128, choices=STATUS_PURCHASE_RETURN, default="returnable")
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'purchase_return_item'
        verbose_name = ('Purchase Return Item')
        verbose_name_plural = ('Purchase Return Items')

    def subtotal(self):
        return (self.quantity * self.amount)

    def __str__(self):
        return str(self.id)



class PurchaseOrder(BaseModel):
    # payment_voucher = models.ForeignKey('finance.PaymentVoucher', null=True, blank=True, limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    # purchase_prifix = models.ForeignKey("finance.InvoicePrefix", null=True, blank=True, limit_choices_to={'is_deleted': False},related_name="purchase_order_prifix", on_delete=models.CASCADE)

    warehouse = models.ForeignKey("warehouses.Warehouse", null=True, blank=True, limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    supplier = models.ForeignKey('suppliers.Supplier', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    user = models.OneToOneField("auth.user", blank=True, null=True, on_delete=models.CASCADE)
    purchase_order = models.ForeignKey('purchases.PurchaseOrder', blank=True, null=True, on_delete=models.CASCADE)

    date = models.DateTimeField()
    order_no = models.PositiveIntegerField(unique=True, blank=True, null=True)
    order_id = models.CharField(max_length=128, blank=True, null=True)

    product_total = models.DecimalField(default=0, decimal_places=3, max_digits=30, validators=[MinValueValidator(Decimal('0.00'))])
    round_off = models.DecimalField(default=0, decimal_places=3, max_digits=30)
    discount = models.DecimalField(default=0, decimal_places=3, max_digits=30, validators=[MinValueValidator(Decimal('0.00'))])
    subtotal = models.DecimalField(default=0, decimal_places=3, max_digits=30, validators=[MinValueValidator(Decimal('0.00'))])
    # paid = models.DecimalField(default=0, decimal_places=3, max_digits=30, validators=[MinValueValidator(Decimal('0.00'))])
    # balance = models.DecimalField(default=0, decimal_places=3, blank=True, null=True, max_digits=30)

    add_gst = models.BooleanField(default=True)
    # payment_method = models.CharField(max_length=123, blank=True, null=True)
    is_updated = models.BooleanField(default=False)
    is_partial = models.BooleanField(default=False)
    is_purchased = models.BooleanField(default=False)

    class Meta:
        db_table = 'purchase_order'
        verbose_name = _('purchase_order')
        verbose_name_plural = _('purchase_orders')
        ordering = ('-order_no', 'date',)

    def __str__(self):
        # return str(self.auto_id)
        return '%s - %s' % (self.order_id, self.date.date())

    def discount_amount(self):
        discount_amount = 0
        if self.discount > 0:
            discount_amount = (self.product_total * self.discount) / 100

        return round(discount_amount, 2)


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey('purchases.PurchaseOrder', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    product_variant = models.ForeignKey('products.ProductVariant', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE, blank=True, null=True)
    batch = models.ForeignKey('general.Batch', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE, blank=True, null=True)
    # product = models.ForeignKey('products.Product', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE, blank=True, null=True)

    add_new_batch = models.BooleanField(default=False)
    batch_number = models.CharField(max_length=128, blank=True, null=True)

    quantity = models.DecimalField(decimal_places=3, default=1.00, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    # return_qty = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    expire_date = models.DateTimeField()
    manufacturing_date = models.DateField()
    discount = models.DecimalField(decimal_places=2, default=0.00, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    tax_amount = models.DecimalField(decimal_places=2, default=0.00, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    net_rate = models.DecimalField(decimal_places=2, default=0.00, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])

    mrp = models.DecimalField(decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    retail_price = models.DecimalField(default=0, decimal_places=3, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    whole_sale_price = models.DecimalField(default=0, decimal_places=3, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    amount = models.DecimalField(decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])

    hsn = models.CharField(max_length=128, blank=True, null=True)
    tax = models.DecimalField(decimal_places=3, default=0.00, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    comments = models.CharField(max_length=128, blank=True, null=True)
    unit_type = models.CharField(max_length=128, blank=True, null=True)

    total = models.DecimalField(decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    cgst_amount = models.DecimalField(decimal_places=2, default=0.00, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    sgst_amount = models.DecimalField(decimal_places=2, default=0.00, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    igst_amount = models.DecimalField(decimal_places=2, default=0.00, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    gross_amount = models.DecimalField(decimal_places=2, default=0.00, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    is_purchased = models.BooleanField(default=False)

    def subtotal(self):
        return (self.quantity * self.amount)

    class Meta:
        db_table = 'purchase_order_item'
        verbose_name = _('purchase_order_item')
        verbose_name_plural = _('purchase_order_items')
        ordering = ('id',)

    def __str__(self):
        return str(self.product_variant)

