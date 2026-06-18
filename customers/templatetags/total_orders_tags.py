from django.template import Library
from django.contrib.auth.models import User
register = Library()
from orders.models import Orders

@register.simple_tag
def get_total_orders(customer):
    count = Orders.objects.filter(customer=customer).count()
    return count
