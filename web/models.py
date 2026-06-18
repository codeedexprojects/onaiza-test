from django.db import models
from django.utils.translation import ugettext_lazy as _
from main.models import BaseModel
from orders.models import Orders, OrderItem
from products.models import Category, SubCategory
from products.models import ProductVariant
from delivery_agent.models import DeliveryAgents
from versatileimagefield.fields import VersatileImageField

RATING_CHOICES = (
    (1, 1),
    (2, 2),
    (3, 3),
    (4, 4),
    (5, 5),
)

RETURN_CHOICES = (
    ("product_damage","Product Damage"),
    ("size_not_fit", "Size Not Fit"),
    ("others", "Others"),
)
OFFER_TYPE = (
    ("product","Product"),
    ("category", "Category"),
    ("brand", "Brand"),
)


STATUS_CHOICES = (
    ("pending", "Pending"),
    ("accepted", "Accepted"),
    ("delivery_boy_collected","Delivery Boy Collected"),
    ("onaiza_received", "Onaiza Received the product"),
    ("rejected", "Rejected"),
)

class FeauturedCategory(BaseModel):
    category = models.ForeignKey(Category, limit_choices_to={
        'is_deleted': False}, on_delete=models.CASCADE)

    class Meta:
        db_table = 'web_FeauturedCategory'
        verbose_name = _('Feautured Category')
        verbose_name_plural = _('Feautured Categories')

    def __unicode__(self):
        return self.category.name

    def get_subcategory(self):
        return SubCategory.objects.filter(is_deleted=False, category=self)

    def get_products(self):
        return ProductVariant.objects.filter(is_deleted=False, product__category=self.category)


class TrendingCategory(BaseModel):
    category = models.ForeignKey(Category, limit_choices_to={
        'is_deleted': False}, on_delete=models.CASCADE)

    class Meta:
        db_table = 'web_TrendingCategory'
        verbose_name = _('Trending Category')
        verbose_name_plural = _('Trending Categories')

    def __unicode__(self):
        return self.category.name

    def get_subcategory(self):
        return SubCategory.objects.filter(is_deleted=False, category=self)


class ProductReview(BaseModel):
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    review = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = _('review')
        verbose_name_plural = _('reviews')

    def __str__(self):
        return f'{self.product_variant.title} - {self.rating}'


class ProductReturn(BaseModel):
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE)
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    reason_for_return = models.CharField(max_length=256,choices=RETURN_CHOICES)
    return_specification = models.TextField(null=True,blank=True)
    status = models.CharField(choices=STATUS_CHOICES,default="pending",max_length=100)
    rejected_reason = models.TextField(blank=True,null=True)
    delivery_boy = models.ForeignKey(DeliveryAgents,on_delete=models.CASCADE,null=True,blank=True)

    class Meta:
        verbose_name = _('product return')
        verbose_name_plural = _('product returns')

    def __str__(self):
        return f'{self.order_item.product_variant.title} - {self.order.customer.name}'


class SpotlightBanner(BaseModel):
    BANNER_TYPE = (
        ("primary", "Primary"),
        ("secondary", "Secondary"),
        ("tertiary", "Tertiary"),
    )
    product_variant = models.ForeignKey("products.ProductVariant", limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE,null=True,blank=True)
    offer_type = models.CharField(choices=OFFER_TYPE,null=True,blank=True,max_length=100)
    image = VersatileImageField(upload_to="media/", blank=True, null=True)
    banner_type = models.CharField(choices=BANNER_TYPE,null=True,blank=True,max_length=100)
    category = models.ForeignKey("products.Category", limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE,null=True,blank=True)
    brand = models.ForeignKey("products.Brand", limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE,null=True,blank=True)

    class Meta:
        verbose_name = _('spotlight banner')
        verbose_name_plural = _('spotlight banner')

    def __str__(self):
        return str(self.auto_id)