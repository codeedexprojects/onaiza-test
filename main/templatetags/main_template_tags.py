# from web.models import Wishlist,Cart
from django.template import Library
from django.template.defaultfilters import stringfilter

register = Library()


@register.filter
def check_default(value):
    result = value
    if value == "default":
        result = "-"
    return result


@register.filter
@stringfilter
def underscore_smallletter(value):
    value = value.replace(" ", "_")
    return value


@register.filter
def to_fixed_two(value):
    return "{:10.2f}".format(value)


@register.filter
def tax_devide(value):
    return value / 2


@register.filter
def to_positive(value):
    return (value * -1)


# @register.filter
# def get_cart_total(instance):
#     amount = 0
#     qty = instance.qty
#     total = instance.product.get_dicount()
#     amount = total * float(qty)
#     return (amount)


# @register.filter
# def get_cart_sub_total(request):
#     amount = 0
#     total = 0
#     user = request.user
#     carts = Cart.objects.filter(user=user,is_purchased=False)

#     for cart in carts:
#         qty = cart.qty
#         amount = cart.product.get_dicount()
#         total += amount * float(qty)

#     return (total)


# @register.filter
# def wish_list(product,request):
#     if Wishlist.objects.filter(user=request.user, product=product).exists():
#         return True
#     else:
#         return False


# @register.filter
# def no_of_items(value):
#     if Cart.objects.filter(is_deleted=False,is_purchased=False,user=value).exists():
#         return Cart.objects.filter(is_deleted=False,is_purchased=False,user=value).count()
#     else:
#         return 0


@register.filter
def partition_horizontal(thelist):
    try:
        count = thelist.count()
        if count % 2 == 1:
            count += 1
        n = count / 2
        n = int(n)
        thelist = list(thelist)
    except (ValueError, TypeError):
        return [thelist]
    newlists = [list() for i in range(n)]
    for i, val in enumerate(thelist):
        newlists[i % n].append(val)
    return newlists


@register.simple_tag
def get_filtered_url(url):
    splitted = url.split("?")

    if len(splitted) > 1:
        return splitted[1]
    else:
        return ""
