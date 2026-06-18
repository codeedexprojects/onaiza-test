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
from general.models import Batch
from offers.models import Offers

DAY_TYPE_CHOICES = (
    ("day", 'Day'),
    ("hours", 'Hours'),
)


class Category(BaseModel):
    name = models.CharField(max_length=128)
    image = VersatileImageField(upload_to="media/", blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    malayalam_name = models.CharField(max_length=128,null=True,blank=True)

    # for vendors
    vendor_created = models.BooleanField(default=False)
    is_admin_approved = models.BooleanField(null=True)

    class Meta:
        db_table = 'products_category'
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        ordering = ('name',)

    def __str__(self):
        return str(self.name)

    def sub_category_names(self):
        names = SubCategory.objects.filter(is_deleted=False, category=self).values_list('name', flat=True)
        return ', '.join(names)

    def get_subcategory(self):
        return SubCategory.objects.filter(is_deleted=False, category=self)

    def get_products(self):
        return ProductVariant.objects.filter(product__category=self, is_admin_approved=True, is_deleted=False,is_default=True).order_by("?")


class SubCategory(BaseModel):
    category = models.ForeignKey("products.Category", limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    malayalam_name = models.CharField(max_length=128,null=True,blank=True)

    # for vendors
    vendor_created = models.BooleanField(default=False)
    is_admin_approved = models.BooleanField(null=True)

    class Meta:
        db_table = 'products_sub_category'
        verbose_name = _('Sub category')
        verbose_name_plural = _('Sub categories')
        ordering = ('name',)

    def __str__(self):
        return str(self.name)


class Brand(BaseModel):
    name = models.CharField(max_length=128)
    malayalam_name = models.CharField(max_length=128,null=True,blank=True)

    # for vendors
    vendor_created = models.BooleanField(default=False)
    is_admin_approved = models.BooleanField(null=True)

    class Meta:
        db_table = 'products_brand'
        verbose_name = _('brand')
        verbose_name_plural = _('brands')
        ordering = ('name',)

    def __str__(self):
        return str(self.name)


class UnitOfMeasurement(BaseModel):
    unit_of_measurement = models.CharField(max_length=128)

    # for vendors
    vendor_created = models.BooleanField(default=False)
    is_admin_approved = models.BooleanField(null=True)

    class Meta:
        db_table = 'products_unit_measurement'
        verbose_name = _('Unit measurement')
        verbose_name_plural = _('Unit measurements')
        ordering = ('auto_id',)

    def __str__(self):
        return str(self.unit_of_measurement)


class Unit(BaseModel):
    unit_of_measurement = models.ForeignKey("products.UnitOfMeasurement", limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    unit = models.CharField(max_length=128)

    # for vendors
    vendor_created = models.BooleanField(default=False)
    is_admin_approved = models.BooleanField(null=True)

    class Meta:
        db_table = 'products_unit'
        verbose_name = _('Proudct unit')
        verbose_name_plural = _('Proudct unit')
        ordering = ('unit',)

    def __str__(self):
        return str(self.unit)


class HsnCodes(BaseModel):
    unit = models.ForeignKey("products.Unit", limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    hsn_number = models.CharField(max_length=128)
    description = models.CharField(max_length=30, blank=True, null=True)

    igst_rate = models.DecimalField(default=0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    sgst_rate = models.DecimalField(default=0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    cgst_rate = models.DecimalField(default=0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])

    # for vendors
    vendor_created = models.BooleanField(default=False)
    is_admin_approved = models.BooleanField(null=True)

    class Meta:
        db_table = 'product_hsn_code'
        verbose_name = _('product_hsn_code')
        verbose_name_plural = _('product_hsn_codes')
        ordering = ('name',)

    def __str__(self):
        return f"{self.hsn_number} - {self.name}"


class Product(BaseModel):
    brand = models.ForeignKey("products.Brand", null=True, blank=True, limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    category = models.ForeignKey("products.Category", null=True, blank=True, limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    subcategory = models.ForeignKey("products.SubCategory", null=True, blank=True, limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    hsn = models.ForeignKey('products.HsnCodes', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE, blank=True, null=True)
    vendor = models.ForeignKey("vendors.Vendor", null=True, blank=True, limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    unit_of_measurement = models.ForeignKey("products.UnitOfMeasurement",null=True, limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)

    name = models.CharField(max_length=128)
    malayalam_name = models.CharField(max_length=128,null=True,blank=True)
    image = VersatileImageField(upload_to="media/", blank=True, null=True)

    description = models.TextField(blank=True, null=True)
    malayalam_description = models.TextField(blank=True, null=True)
    meta_description = models.CharField(max_length=128)

    is_varying_price = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    cancellable_duration = models.DecimalField(default=0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    cancellable_duration_type = models.CharField(max_length=7,choices=DAY_TYPE_CHOICES)
    returnable_duration = models.DecimalField(default=0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    returnable_duration_type = models.CharField(max_length=7,choices=DAY_TYPE_CHOICES)
    password = models.BooleanField(null=True,blank=True,editable=False)

    # for vendors
    vendor_created = models.BooleanField(default=False)
    is_admin_approved = models.BooleanField(null=True)

    class Meta:
        db_table = 'products_product'
        verbose_name = _('product')
        verbose_name_plural = _('products')
        ordering = ('name',)

    def __str__(self):
        return str(self.name)

    def get_variant_names(self):
        names = ProductVariant.objects.filter(is_deleted=False, is_admin_approved=True, product_id=self.pk).values_list('title', flat=True)
        return ', '.join(names)

    def get_product_name(self):
        if self.brand:
            return str(self.brand.name + " - " + self.name)
        else:
            return str(self.name)


class ProductVariant(BaseModel):
    product = models.ForeignKey("products.Product", limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    unit = models.ForeignKey("products.Unit", limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    warehouse = models.ForeignKey("warehouses.Warehouse", limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE, null=True, blank=True)

    title = models.CharField(max_length=120)
    product_code = models.CharField(max_length=128, unique=True)
    image = VersatileImageField(upload_to="media/product_variant/", blank=True, null=True)
    current_rating = models.DecimalField(default=0, decimal_places=1, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    stock = models.DecimalField(default=0, decimal_places=3, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])

    discount_limit = models.DecimalField(default=0, decimal_places=3, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    low_stock_limit = models.PositiveIntegerField(default=1)
    igst = models.DecimalField(default=0, decimal_places=3, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    sgst = models.DecimalField(default=0, decimal_places=3, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    cgst = models.DecimalField(default=0, decimal_places=3, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])

    first_time_stock = models.DecimalField(default=0, decimal_places=3, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    batch_number = models.CharField(max_length=128, blank=True, null=True)
    manufacturing_date = models.DateField()
    expire_date = models.DateField()
    retail_price = models.DecimalField(default=0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    whole_sale_price = models.DecimalField(default=0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    cost = models.DecimalField(decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    mrp = models.DecimalField(decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    commission_percentage = models.DecimalField(decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))], blank=True,null=True)

    gst_included = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)

    # for vendors
    vendor_created = models.BooleanField(default=False)
    is_admin_approved = models.BooleanField(null=True)

    class Meta:
        db_table = 'products_product_variant'
        verbose_name = _('product_variant')
        verbose_name_plural = _('product_variants')
        ordering = ('auto_id',)

    def __str__(self):
        if self.product.brand:
            return f'{self.product.brand} - {self.product.name} - {self.title}'
        else:
            return f'{self.product.name} - {self.title}'

    def get_malayalam_name(self):
        if self.product.brand:
            if self.product.brand.malayalam_name:
                return f'{self.product.brand.malayalam_name} - {self.product.malayalam_name if self.product.malayalam_name else self.product.name} - {self.title}'
            else:
                return f'{self.product.brand.name} - {self.product.malayalam_name if self.product.malayalam_name else self.product.name} - {self.title}'
        else:
            return f'{self.product.malayalam_name if self.product.malayalam_name else self.product.name} - {self.title}'

    def total_stock(self):
        stock = 0
        if Batch.objects.filter(product_variant=self).exists():
            stock = Batch.objects.filter(product_variant=self).aggregate(stock=Sum('stock')).get('stock', 0)
            self.stock = stock
            self.save()
        return stock

    def get_category(self):
        category = Category.objects.get(pk=self.product.category.pk)
        return category.name

    def get_fullname(self):
        if self.product.brand:
            return f'{self.product.brand} - {self.product.name} - {self.title}'
        else:
            return f'{self.product.name} - {self.title}'

    def offer_price(self):
        now = datetime.datetime.now()
        offer = Offers.objects.filter(product_variant=self, start_time__lte=now, end_time__gte=now, is_deleted=False).order_by('offer_percentage').last()
        if offer:
            return self.retail_price - (self.retail_price * offer.offer_percentage / 100)
        else:
            return None


class ProductImages(BaseModel):
    product_variant = models.ForeignKey("products.ProductVariant", limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE,null=True,blank=True)
    image = VersatileImageField(upload_to="media/", blank=True, null=True)

    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'products_product_image'
        verbose_name = _('product_image')
        verbose_name_plural = _('product_images')
        ordering = ('auto_id',)

    def __str__(self):
        return str(self.auto_id)


class ProductStock(models.Model):
    product_variant = models.ForeignKey("products.ProductVariant", null=True, blank=True, limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    batch = models.ForeignKey('general.Batch', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE, blank=True, null=True)
    warehouse = models.ForeignKey("warehouses.Warehouse", null=True, blank=True, limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    category = models.CharField(max_length=128)
    date = models.DateField()
    increment = models.DecimalField(default=0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    decrement = models.DecimalField(default=0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])

    class Meta:
        db_table = 'product_stock'
        verbose_name = _('product_stock')
        verbose_name_plural = _('product_stocks')
        ordering = ('date',)

    def __str__(self):
        return str(self.product.name)
