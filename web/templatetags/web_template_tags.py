from django import template
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from products.models import Category, SubCategory, ProductVariant

register = template.Library()

import decimal
import datetime
from users.models import *
from products.models import *
from general.models import *
from customers.models import Customer, CustomerAddress
from vendors.models import Vendor
from warehouses.models import Location
from orders.models import Orders


@register.filter
def check_wish(product):
    if Wishlistitem.objects.filter(product_variant=product).exists():
        return True
    else:
        return False


@register.simple_tag
def get_cart_count(product, user):
    if CartItem.objects.filter(product_variant__pk=product, customer__user=user,is_deleted=False).exists():
        cart_item_instance = CartItem.objects.get(product_variant__pk=product, customer__user=user,is_deleted=False)
        return cart_item_instance.qty
    else:
        return 1


@register.simple_tag
def get_pv(pincode, category):
    products = Batch.objects.filter(
        is_deleted=False,
        warehouse__location__pincode=pincode,
        product__category__pk=category,
        product_variant__is_default=True,
    )
    return products


@register.simple_tag
def get_pv_by_pincode(pincode):
    products = Batch.objects.filter(is_deleted=False, warehouse__location__pincode=pincode,

                                    product_variant__is_default=True)
    return products


@register.simple_tag
def is_stock(pk, pincode):
    # variant = get_object_or_404(ProductVariant, pk=pk)
    batch = Batch.objects.filter(is_deleted=False, warehouse__location__pincode=pincode, product_variant_id=pk)

    total_stock = batch.aggregate(Sum('stock')).get('stock__sum', 0)
    # for b in batch:
    #     total_stock += b.stock

    if total_stock == 0:
        return False
    else:
        return True


@register.simple_tag
def get_booked_product_price(pk, pincode):
    batch = Batch.objects.filter(is_deleted=False, warehouse__location__pincode=pincode, product_variant__pk=pk).order_by('-date_added').first()

    if batch:
        return {
            "mrp": batch.mrp,
            "retail_price": batch.retail_price
        }
    else:
        product_variant = ProductVariant.objects.get(pk=pk)
        return {
            "mrp": product_variant.mrp,
            "retail_price": product_variant.retail_price
        }


@register.simple_tag
def get_product_by_id(pk):
    product = ProductVariant.objects.get(pk=pk)

    return product


@register.simple_tag
def get_product_price(pk, pincode):
    try:
        if Batch.objects.filter(is_deleted=False, warehouse__location__pincode=pincode,
                                product_variant__pk=pk).exists():
            batch = Batch.objects.filter(is_deleted=False, warehouse__location__pincode=pincode,
                                         product_variant__pk=pk).order_by('-date_added').first()

            return batch.retail_price
        else:
            prod_instance = ProductVariant.objects.get(is_deleted=False, pk=pk)
            return prod_instance.retail_price

    except Exception as e:
        return e


@register.simple_tag
def get_name(user):
    try:
        customer = Customer.objects.get(user__username=user)
        return customer.name
    except Exception as e:
        return e


@register.simple_tag
def get_pro_pic(user):
    try:
        customer = Customer.objects.get(user__username=user)
        if customer.image:
            return customer.image.url
        else:
            return False
    except Exception as e:
        return e


@register.simple_tag
def get_customer_active_address(customer):
    address = None

    # check for default address
    if CustomerAddress.objects.filter(is_deleted=False, is_default=True, customer=customer).exists():
        address = CustomerAddress.objects.filter(is_deleted=False, is_default=True, customer=customer).first()
    # checking for adress if no active address found
    elif CustomerAddress.objects.filter(is_deleted=False, customer=customer).exists():
        address = CustomerAddress.objects.filter(is_deleted=False, customer=customer).first()

    return address


@register.simple_tag
def get_english_or_malayalam(pk, field_type, language_code):
    if 'product' in field_type:
        product_instance = ProductVariant.objects.get(pk=pk)
        if 'en' in language_code:
            dict = {
                "name": product_instance.get_fullname(),
                "description": product_instance.product.description,
            }
            return dict

        elif 'ml' in language_code:
            dict = {
                "name": product_instance.get_malayalam_name(),
                "description": product_instance.product.malayalam_description if product_instance.product.malayalam_description else product_instance.product.description,
            }
            return dict

    elif 'category' in field_type:
        category_instance = Category.objects.get(pk=pk)
        if 'en' in language_code:
            return category_instance.name

        elif 'ml' in language_code:
            return category_instance.malayalam_name if category_instance.malayalam_name else category_instance.name

    elif 'sub_category' in field_type:
        sub_category_instance = SubCategory.objects.get(pk=pk)
        if 'en' in language_code:
            return sub_category_instance.name

        elif 'ml' in language_code:
            return sub_category_instance.malayalam_name if sub_category_instance.malayalam_name else sub_category_instance.name

    elif 'shop' in field_type:
        shop_instance = Vendor.objects.get(pk=pk)
        if 'en' in language_code:
            return shop_instance.name

        elif 'ml' in language_code:
            return shop_instance.malayalam_name if shop_instance.malayalam_name else shop_instance.name

    elif 'location' in field_type:
        if pk:
            location_instance = Location.objects.get(pk=pk)
            if 'en' in language_code:
                return location_instance.name

            elif 'ml' in language_code:
                return location_instance.malayalam_name if location_instance.malayalam_name else location_instance.name


@register.simple_tag
def is_return_button(product_variant, order_id):
    print("===>>>> ",product_variant)
    product_variant_instances = ProductVariant.objects.get(pk=product_variant)

    returnable_duration_type = product_variant_instances.product.returnable_duration_type

    order_instances = Orders.objects.get(pk=order_id)

    today_date = datetime.datetime.now(timezone.utc)
    today_date = today_date.replace(tzinfo=None)
    order_date = order_instances.date_added

    if 'day' in returnable_duration_type:
        day_duration = product_variant_instances.product.returnable_duration
        date_differnce = (today_date - order_date.replace(tzinfo=None)).days

        if date_differnce >= day_duration:
            return False
        else:
            return True

    elif 'hours' in returnable_duration_type:
        time_duration = product_variant_instances.product.returnable_duration
        seconds = (today_date - order_date.replace(tzinfo=None)).seconds
        # hours = seconds // 3600
        hours = decimal.Decimal(seconds // 3600)

        if hours >= time_duration:
            return False

        else:
            return True