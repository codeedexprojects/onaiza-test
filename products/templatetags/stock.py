from django import template
from django.db.models import Sum

from products.models import ProductVariant

from products.functions import get_all_stock

register = template.Library()


@register.simple_tag
def get_total_stock(product):
    total_stock = get_all_stock(product)
    
    return total_stock
