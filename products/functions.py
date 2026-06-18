from decimal import Decimal
import datetime

from django.db.models import Sum
from main.functions import get_auto_id, get_a_id
from products.models import Product, ProductStock, ProductVariant, Category, Brand, SubCategory
from purchases.models import Purchase
from django.core.files.images import get_image_dimensions
from sales.models import Sale


def get_exact_qty(qty, unit):
    is_base = unit.is_base
    if not is_base:
        conversion_factor = unit.conversion_factor
        return qty * conversion_factor
    else:
        return qty


def image_validation(image):
    is_ok = True
    message = ''
    if image:
        w, h = get_image_dimensions(image)
        if w < 215:
            message = "The image is %i pixel wide. It's supposed to be minimum 215px" % w
            is_ok = False
        if h < 241:
            message = "The image is %i pixel high. It's supposed to be minimum 241px" % h
            is_ok = False

    return (is_ok, message)


def update_stock_register(pk, qty, status, category, item_pk, date=datetime.datetime.now()):
    product = Product.objects.get(pk=pk)
    the_cost = product.cost
    stock_value = Decimal(the_cost) * Decimal(qty)

    increment = 0
    decrement = 0
    if status == "increase":
        increment = stock_value
    elif status == "decrease":
        decrement = stock_value

    sale = None
    sale_return = None
    purchase = None
    purchase_return = None

    if category == "sale":
        sale = Sale.objects.get(pk=item_pk)
    # elif category == "sale_return":
    # sale_return = SaleReturn.objects.get(pk=item_pk)
    elif category == "purchase":
        purchase = Purchase.objects.get(pk=item_pk)
    # elif category == "purchase_return":
    #     purchase_return = PurchaseReturn.objects.get(pk=item_pk)
    ProductStock.objects.create(product=product, date=date, increment=increment, decrement=decrement,
                                category=category, sale=sale, sale_return=sale_return, purchase=purchase,
                                purchase_return=purchase_return)


def update_stock_register_edit(pk, status, qty, category, item_pk, date=None):
    product = Product.objects.get(pk=pk)
    the_cost = product.cost
    stock_value = the_cost * qty

    increment = 0
    decrement = 0
    if status == "increase":
        increment = stock_value
    elif status == "decrease":
        decrement = stock_value

    sale = None
    # sale_return = None
    purchase = None
    # purchase_return = None
    if date:
        if category == "sale":
            sale = Sale.objects.get(pk=item_pk)
            ProductStock.objects.filter(product=product, sale=sale).update(
                increment=increment, decrement=decrement, date=date)
        # elif category == "sale_return":
        #     sale_return = SaleReturn.objects.get(pk=item_pk)
        #     ProductStock.objects.filter(product=product,sale_return=sale_return).update(increment=increment,decrement=decrement,date=date)
        elif category == "purchase":
            purchase = Purchase.objects.get(pk=item_pk)
            ProductStock.objects.filter(product=product, purchase=purchase).update(
                increment=increment, decrement=decrement, date=date)
        # elif category == "purchase_return":
        #     purchase_return = PurchaseReturn.objects.get(pk=item_pk)
        #     ProductStock.objects.filter(product=product,purchase_return=purchase_return).update(increment=increment,decrement=decrement,date=date)
        elif category == "opening":
            ProductStock.objects.filter(product=product, category=category).update(
                increment=increment, decrement=decrement, date=date)
    else:
        if category == "sale":
            sale = Sale.objects.get(pk=item_pk)
            ProductStock.objects.filter(product=product, sale=sale).update(
                increment=increment, decrement=decrement)
        # elif category == "sale_return":
        #     sale_return = SaleReturn.objects.get(pk=item_pk)
        #     ProductStock.objects.filter(product=product,sale_return=sale_return).update(increment=increment,decrement=decrement)
        elif category == "purchase":
            purchase = Purchase.objects.get(pk=item_pk)
            ProductStock.objects.filter(product=product, purchase=purchase).update(
                increment=increment, decrement=decrement)
        # elif category == "purchase_return":
        #     purchase_return = PurchaseReturn.objects.get(pk=item_pk)
        #     ProductStock.objects.filter(product=product,purchase_return=purchase_return).update(increment=increment,decrement=decrement)
        elif category == "opening":
            ProductStock.objects.filter(product=product, category=category).update(
                increment=increment, decrement=decrement)


def update_stock_register_delete(pk, category, item_pk):
    product = Product.objects.get(pk=pk)

    sale = None
    # sale_return = None
    purchase = None
    # purchase_return = None
    if category == "sale":
        sale = Sale.objects.get(pk=item_pk)
        ProductStock.objects.filter(
            product=product, sale=sale).update(is_deleted=True)
    # elif category == "sale_return":
    #     sale_return = SaleReturn.objects.get(pk=item_pk)
    #     ProductStock.objects.filter(product=product,sale_return=sale_return).update(is_deleted=True)
    elif category == "purchase":
        purchase = Purchase.objects.get(pk=item_pk)
        ProductStock.objects.filter(
            product=product, purchase=purchase).update(is_deleted=True)
    # elif category == "purchase_return":
    #     purchase_return = PurchaseReturn.objects.get(pk=item_pk)
    #     ProductStock.objects.filter(product=product,purchase_return=purchase_return).update(is_deleted=True)
    elif category == "opening":
        ProductStock.objects.filter(
            product=product, category=category).update(is_deleted=True)


def get_all_stock(product):
    total_stock = ProductVariant.objects.filter(product=product, is_admin_approved=True).aggregate(total_stock=Sum('stock'))['total_stock']
    return total_stock

def get_category_by_pk(pk):
    return Category.objects.get(pk=pk)

def get_vendor_by_pk(pk):
    return Brand.objects.get(pk=pk)

def get_subcategory_by_pk(pk):
    return SubCategory.objects.get(pk=pk)