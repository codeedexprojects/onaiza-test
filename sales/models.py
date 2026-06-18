# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from main.models import BaseModel
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.db.models import Sum, Avg, Count
from main.functions import truncate

SALE_CATEGORY = (
    ('inter_state', 'Inter State'),
    ('intra_state', 'Intra State')
)
SALE_APPROVAL_STATUS = (
    ('pending', 'Pending'),
    ('rejected', 'Rejected'),
    ('approved', 'Approved')
)
CATEGORY = (
    ('b2b', 'B2B'),
    ('b2c', 'B2C')
)
STATUS_SALE_RETURN = (('returnable', 'Returnable'), ('damaged', 'Damaged'))


class Sale(BaseModel):
    receipt_voucher = models.OneToOneField('finance.ReceiptVoucher', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE, null=True)
    warehouse = models.ForeignKey("warehouses.Warehouse", null=True, blank=True, limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    sale_prifix = models.ForeignKey("finance.InvoicePrefix", null=True, blank=True, limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)

    a_id = models.PositiveIntegerField()
    sale_no = models.PositiveIntegerField( blank=True, null=True)
    tracking_no = models.PositiveIntegerField(unique=True, blank=True, null=True)
    sale_id = models.CharField(max_length=128, blank=True, null=True)
    tracking_id = models.CharField(max_length=128, blank=True, null=True)

    sale_date = models.DateTimeField()
    shipment_date = models.DateField(blank=True, null=True)
    customer = models.ForeignKey('customers.Customer', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE, blank=True, null=True)
    customer_address = models.TextField(blank=True, null=True)
    payment_method = models.CharField(max_length=123, blank=True, null=True)
    approval_status = models.CharField(max_length=128, choices=SALE_APPROVAL_STATUS, blank=True, default='pending')
    sale_category = models.CharField(max_length=128, choices=SALE_CATEGORY, default="intra_state")
    sale_type = models.CharField(max_length=128, choices=CATEGORY, default="b2b")

    transporter = models.CharField(max_length=128, blank=True, null=True)
    subtotal = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    round_off = models.DecimalField(decimal_places=3, default=0.00, max_digits=30)
    total = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    paid = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    discount_rate = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    discount = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    special_discount = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    cgst = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    sgst = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    igst = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])

    privilege_point_used = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    privilege_point_amnt = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    use_privilege_point = models.BooleanField(default=False)

    # ===========
    total_gst_amount = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    # ===========

    customer_balance_type = models.CharField(max_length=128, default='Debit', blank=True, null=True)
    customer_balance = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])

    sale_taxable_amount = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    purchase_taxable_amount = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])

    total_commission = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    total_outstanding = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    privilege_points = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    add_gst = models.BooleanField(default=False)
    is_updated = models.BooleanField(default=False)

    class Meta:
        db_table = 'sales'
        verbose_name = _('sale')
        verbose_name_plural = _('sales')
        ordering = ('auto_id',)

    def __str__(self):
        # return str(self.sale_id)
        return 'sale: %s' % (self.sale_id)

    def gross_amount(self):
        amount = 0
        sale_items = SaleItem.objects.filter(sale=self)
        for item in sale_items:
            amount += item.sub_total
        print(amount, "amount")
        return(amount)

    def total_tax(self):
        amount = 0
        sale_items = SaleItem.objects.filter(sale=self)
        for item in sale_items:
            # amount += item.gst_amount
            amount += item.cgst
            amount += item.sgst
            amount += item.igst
        return(amount)

    def total_discount(self):
        amount = self.discount
        sale_items = SaleItem.objects.filter(sale=self)
        for item in sale_items:
            amount += item.discount
        return(amount)

    def sale_item_total_discount(self):
        amount = 0
        sale_items = SaleItem.objects.filter(sale=self)
        for item in sale_items:
            amount += item.discount
        return(amount)

    def sale_items_cost(self):
        sale_items = SaleItem.objects.filter(sale=self, sale__is_deleted=False)
        cost, total_cost = 0, 0

        for sale_item in sale_items:
            if sale_item.batch:
                cost = sale_item.batch.cost * sale_item.quantity

            elif sale_item.product_variant:
                cost = sale_item.product_variant.cost * sale_item.quantity
            else:
                cost = sale_item.product.cost * sale_item.quantity
            total_cost += cost
        return total_cost

    def total_net_rate(self):
        sale_items = SaleItem.objects.filter(sale=self, sale__is_deleted=False)
        total_net_rate = 0
        for sale_item in sale_items:
            total_net_rate += sale_item.net_rate
        return total_net_rate

    def profit(self):
        sale_items = SaleItem.objects.filter(sale=self, sale__is_deleted=False)
        profit = 0

        for sale_item in sale_items:
            profit += (sale_item.sale_taxable_amount - sale_item.purchase_taxable_amount) * \
                (sale_item.quantity - sale_item.return_qty)

        return truncate(profit, 2)

    def total_purchase_taxable_amount(self):
        sale_items = SaleItem.objects.filter(sale=self, sale__is_deleted=False)
        total_purchase = 0

        for sale_item in sale_items:
            total_purchase += sale_item.purchase_taxable_amount * \
                (sale_item.quantity - sale_item.return_qty)

        return round(total_purchase, 2)

    def total_sale_taxable_amount(self):
        sale_items = SaleItem.objects.filter(sale=self, sale__is_deleted=False)
        total_sale = 0
        for sale_item in sale_items:
            total_sale += sale_item.sale_taxable_amount * \
                (sale_item.quantity - sale_item.return_qty)

        return round(total_sale, 2)

    def gst_excluded_price(self):
        sale_items = SaleItem.objects.filter(sale=self, sale__is_deleted=False)
        cost, total_amount = 0, 0

        for sale_item in sale_items:
            if sale_item.product_variant:
                gst = sale_item.product_variant.product.gst
                cess = sale_item.product_variant.product.cess
                amount = sale_item.amount * sale_item.quantity
            else:
                gst = sale_item.product.gst
                cess = sale_item.product.cess
                amount = sale_item.amount * sale_item.quantity

            percent = gst + cess
            total_amount += amount / (1 + (percent/100))

        return total_amount

    def total_gst(self):
        sale_items = SaleItem.objects.filter(sale=self, sale__is_deleted=False)
        sale_total, cost, total_amount = 0, 0, 0

        for sale_item in sale_items:
            if sale_item.product_variant:
                gst = sale_item.product_variant.product.gst
                amount = sale_item.amount * sale_item.quantity
            else:
                gst = sale_item.product.gst
                amount = sale_item.amount * sale_item.quantity

            sale_total += amount
            total_amount += amount / (1 + (gst/100))

        return round((sale_total - total_amount), 2)

    def gst_excluded_cost(self):
        sale_items = SaleItem.objects.filter(sale=self, sale__is_deleted=False)
        cost, total_amount = 0, 0

        for sale_item in sale_items:
            if sale_item.product_variant:
                gst = sale_item.product_variant.product.gst
                cost = sale_item.product_variant.cost * sale_item.quantity
            else:
                gst = sale_item.product.gst
                cost = sale_item.product.cost * sale_item.quantity

            total_amount += cost / (1 + (gst/100))

        return total_amount


class SaleItem(models.Model):
    sale = models.ForeignKey('sales.Sale', limit_choices_to={
                             'is_deleted': False}, on_delete=models.CASCADE)
    # product = models.ForeignKey('products.Product', limit_choices_to={
    #                             'is_deleted': False}, on_delete=models.CASCADE)
    product_variant = models.ForeignKey('products.ProductVariant', limit_choices_to={
                                        'is_deleted': False}, on_delete=models.CASCADE, blank=True, null=True)
    batch = models.ForeignKey('general.Batch', limit_choices_to={
                              'is_deleted': False}, on_delete=models.CASCADE, blank=True, null=True)
    # ====
    comments = models.CharField(max_length=128, blank=True, null=True)
    # ===
    hsn = models.CharField(max_length=128, blank=True, null=True)
    return_qty = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[
                                     MinValueValidator(Decimal('0.00'))])
    quantity = models.DecimalField(default=0.0, decimal_places=3, max_digits=15, validators=[
                                   MinValueValidator(Decimal('.01'))])

    amount = models.DecimalField(default=0.0, decimal_places=3, max_digits=15, validators=[
                                 MinValueValidator(Decimal('0.00'))])
    price = models.DecimalField(default=0.0, decimal_places=3, max_digits=15, validators=[
                                MinValueValidator(Decimal('0.00'))])
    mrp = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[
                              MinValueValidator(Decimal('0.00'))])
    total = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[
                                MinValueValidator(Decimal('0.00'))])
    sub_total = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[
                                    MinValueValidator(Decimal('0.00'))])
    net_rate = models.DecimalField(decimal_places=2, default=0.00, max_digits=15, validators=[
                                   MinValueValidator(Decimal('0.00'))])
    discount_rate = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[
                                        MinValueValidator(Decimal('0.00'))])
    discount = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[
                                   MinValueValidator(Decimal('0.00'))])

    gst = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[
                              MinValueValidator(Decimal('0.00'))])
    cgst = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[
                               MinValueValidator(Decimal('0.00'))])
    sgst = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[
                               MinValueValidator(Decimal('0.00'))])
    igst = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[
                               MinValueValidator(Decimal('0.00'))])
    gst_amount = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[
                                     MinValueValidator(Decimal('0.00'))])

    commission_amount = models.DecimalField(
        default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    total_com = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[
                                    MinValueValidator(Decimal('0.00'))])

    purchase_taxable_amount = models.DecimalField(
        default=0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    sale_taxable_amount = models.DecimalField(
        default=0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])

    class Meta:
        db_table = 'sales_sale_item'
        verbose_name = _('sale item')
        verbose_name_plural = _('sale items')
        ordering = ('id',)

    def get_product_name(self):
        if self.product_variant:
            return f'{self.product_variant.product.get_product_name()} - {self.product_variant.title}'
        else:
            return f'{self.product.get_product_name()} - {self.product.unit_type}'

    def __str__(self):
        return str(self.hsn)


class SaleReturn(BaseModel):
    warehouse = models.ForeignKey("warehouses.Warehouse", null=True, blank=True, limit_choices_to={
    'is_deleted': False}, on_delete=models.CASCADE)

    customer = models.ForeignKey("customers.Customer", blank=True, null=True, limit_choices_to={
                                 'is_deleted': False}, on_delete=models.CASCADE)
    sale = models.ForeignKey("sales.Sale", limit_choices_to={
                             'is_deleted': False}, on_delete=models.CASCADE)
    time = models.DateTimeField()
    a_id = models.PositiveIntegerField()
    amount_returned = models.DecimalField(decimal_places=2, max_digits=15, validators=[
                                          MinValueValidator(Decimal('0.00'))])
    returnable_amount = models.DecimalField(decimal_places=2, max_digits=15, validators=[
                                            MinValueValidator(Decimal('0.00'))], blank=True, null=True)

    is_updated = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'sale_return'
        verbose_name = _('sale return')
        verbose_name_plural = _('sale returns')

    class Admin:
        list_display = ('customer',)

    def __unicode__(self):
        return self.auto_id

    def __str__(self):
        return f"Sale Return {self.auto_id} of sale {self.sale}"

    def t(self):
        items_total = 0
        items = SaleReturnItem.objects.filter(sale_return=self)
        for i in items:
            qty = Decimal(i.qty)
            price = i.price
            sub = qty * price
            items_total += sub

        subtotal = items_total
        total = items_total

        result = {
            "subtotal": subtotal,
            "total": round(total, 2)
        }
        return result

    def get_tax(self):
        tax = 0
        items = SaleReturnItem.objects.filter(sale_return=self)
        for item in items:
            sale_item = SaleItem.objects.get(
                sale=self.sale, product=item.product)
            selling_price = sale_item.amount
            tax += item.price - selling_price
        return tax

    def get_cess(self):
        cess = 0
        items = SaleReturnItem.objects.filter(sale_return=self)
        for item in items:
            sale_item = SaleItem.objects.get(
                sale=self.sale, product=item.product)
            selling_price = sale_item.amount
            cess_rate = item.product.cess
            single_cess = (cess_rate / 100) * selling_price
            cess += single_cess * item.qty
        return cess


class SaleReturnItem(models.Model):
    sale_return = models.ForeignKey("sales.SaleReturn", limit_choices_to={
                                    'is_deleted': False}, on_delete=models.CASCADE)
    sale_item = models.ForeignKey("sales.SaleItem", limit_choices_to={
                                  'is_deleted': False}, on_delete=models.CASCADE)
    product = models.ForeignKey("products.Product", limit_choices_to={
                                'is_deleted': False}, on_delete=models.CASCADE)
    product_variant = models.ForeignKey('products.ProductVariant', limit_choices_to={
                                        'is_deleted': False}, on_delete=models.CASCADE, blank=True, null=True)
    batch = models.ForeignKey('general.Batch', limit_choices_to={
                              'is_deleted': False}, on_delete=models.CASCADE, blank=True, null=True)

    qty = models.DecimalField(default=0, decimal_places=3, max_digits=15, validators=[
                              MinValueValidator(Decimal('0.00'))])
    price = models.DecimalField(decimal_places=2, max_digits=15, validators=[
                                MinValueValidator(Decimal('0.00'))])
    cost = models.DecimalField(decimal_places=2, max_digits=15, validators=[
                               MinValueValidator(Decimal('0.00'))])

    status = models.CharField(
        max_length=128, choices=STATUS_SALE_RETURN, default="returnable")
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'sale_return_item'
        verbose_name = _('sale return item')
        verbose_name_plural = _('sale return items')

    class Admin:
        list_display = ('product',)

    def __unicode__(self):
        return self.product.name

    def t(self):
        return self.qty * self.price
