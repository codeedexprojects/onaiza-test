import datetime
import decimal
from django.db.models import Q, Sum

from api.v1.users.functions import add_privilege_point
from finance.models import InvoicePrefix
from general.models import Batch
from main.functions import get_auto_id
from orders.models import *
from products.models import ProductVariant
from users.models import CartItem
from web.models import ProductReturn


def get_cart_total(request):
    try:
        pincode_session = request.session.get('pincode', '')
        today = datetime.datetime.now()

        cart_items = CartItem.objects.filter(customer__user=request.user, is_deleted=False)

        variant_pks = cart_items.values_list('product_variant_id', flat=True)
        batches = Batch.objects.filter(is_deleted=False, product_variant_id__in=variant_pks, warehouse__location__pincode=pincode_session,expire_date__gt=today)

        total = 0
        for i in cart_items:
            if batches.filter(product_variant=i.product_variant).exists():
                batch_instance = batches.filter(product_variant=i.product_variant).order_by('-date_added').first()
                total = total + (i.qty * batch_instance.retail_price)
            else:
                total = total + (i.qty * i.product_variant.retail_price)

        return total

    except Exception as e:

        return str(e)


def clear_cart(customer, order, pincode, request):
    instances = None

    if CartItem.objects.filter(customer=customer):
        instances = CartItem.objects.filter(customer=customer)

        for cart_item in instances:
            product = cart_item.product_variant

            batch = Batch.objects.filter(product_variant__pk=product.pk, is_deleted=False, warehouse_id=cart_item.warehouse_id).first()

            OrderItem.objects.create(
                order = order,
                product_variant = cart_item.product_variant,
                batch = batch,
                qty = cart_item.qty,
                price = batch.retail_price,
            )

            # get and set batch stock and pk
            stock = batch.stock
            pk = batch.pk
            if stock > 0:
                Batch.objects.filter(pk=pk).update(stock=stock - cart_item.qty)
                cart_item.delete()
            else:
                return False

        add_privilege_point(request, order)

        return True
    else:
        return False


def get_orginal_price(product_variant, request):
    pincode_session = request.session.get('pincode', '')
    today = datetime.datetime.now()

    batch = None
    if Batch.objects.filter(is_deleted=False, product_variant=product_variant,
                            warehouse__location__pincode=pincode_session,
                            product_variant__expire_date__gt=today).exists():
        batch = Batch.objects.filter(is_deleted=False, product_variant=product_variant,
                                     warehouse__location__pincode=pincode_session,
                                     product_variant__expire_date__gt=today).order_by('-date_added').first()
        return batch.retail_price
    else:
        if product_variant.retail_price:
            return product_variant.retail_price


def get_order_prefix():
    order_prefix = None
    if InvoicePrefix.objects.filter(is_active=True, is_deleted=False).exists():
        prefix = InvoicePrefix.objects.get(is_active=True, is_deleted=False)
        prefix_actual_count = Orders.objects.filter(prefix=prefix).count()
        new_order_prefix_to_string = int(prefix_actual_count) + 1

        return f"{prefix.order}{new_order_prefix_to_string}"
    else:
        return f"NONE"


def get_shop_category_instances(product_instances):
    categories = product_instances.values_list('product__category', flat=True).distinct()
    category_instances = Category.objects.filter(pk__in=categories)

    return category_instances


def save_return(order_item, reason, reason_specification, request):
    order_item_instances = OrderItem.objects.get(pk=order_item)
    order_instances = order_item_instances.order

    if reason_specification == "":
        ProductReturn.objects.create(
            auto_id=get_auto_id(ProductReturn),
            creator=request.user,
            updater=request.user,
            order_item=order_item_instances,
            order=order_instances,
            reason_for_return=reason,
        )
    else:
        ProductReturn.objects.create(
            auto_id=get_auto_id(ProductReturn),
            creator=request.user,
            updater=request.user,
            order_item=order_item_instances,
            order=order_instances,
            reason_for_return=reason,
            return_specification=reason_specification,
        )


def is_eligible_for_cancel(order):
    success_count = 0
    fail_count = 0
    is_cancel = False

    order_item_instances = OrderItem.objects.filter(order=order)
    total_count = order_item_instances.count()
    product_variant_pk = order_item_instances.values_list('product_variant_id')

    product_variant_instances = ProductVariant.objects.filter(pk__in=product_variant_pk, is_admin_approved=True)

    for variant in product_variant_instances:
        cancellable_duration_type = variant.product.cancellable_duration_type
        today_date = datetime.datetime.now(timezone.utc)
        today_date = today_date.replace(tzinfo=None)
        order_date = order.date_added

        if 'day' in cancellable_duration_type:
            day_duration = variant.product.cancellable_duration
            date_differnce = (today_date - order_date.replace(tzinfo=None)).days

            if date_differnce >= day_duration:
                fail_count += 1

            else:
                success_count += 1

        elif 'hours' in cancellable_duration_type:
            time_duration = variant.product.cancellable_duration
            seconds = (today_date - order_date.replace(tzinfo=None)).seconds
            # hours = seconds // 3600
            hours = decimal.Decimal(seconds // 3600)

            if hours >= time_duration:
                fail_count += 1
            else:
                success_count += 1

    if total_count == success_count:
        is_cancel = True

    return is_cancel


def get_mrp(product_variant, request):
    """
    get the mrp of a product
    :param product_variant:
    :param request:
    :return:
    """
    pincode_session = request.session.get('pincode', '')
    today = datetime.datetime.now()

    batch = Batch.objects.filter(is_deleted=False, product_variant=product_variant, warehouse__location__pincode=pincode_session, product_variant__expire_date__gt=today)
    if batch.exists():
        batch = batch.order_by('-date_added').first()
        return batch.mrp
    else:
        if product_variant.mrp:
            return product_variant.mrp


def get_queried_params(query, instances):
    if 'product' in query:
        return instances.filter(product_variant__isnull=False)
    elif 'brand' in query:
        return instances.filter(brand__isnull=False)
    elif 'category' in query:
        return instances.filter(category__isnull=False)


def check_stock_availability(request):
    not_available = []

    cart_items = CartItem.objects.filter(customer__user=request.user, is_deleted=False)

    product_ids = list(cart_items.values_list('product_variant_id', flat=True))
    warehouse_id = cart_items.first().warehouse_id

    batches = Batch.objects.filter(product_variant_id__in=product_ids, warehouse_id=warehouse_id, is_deleted=False, stock__gt=0)

    for item in cart_items:
        stocks = batches.filter(product_variant=item.product_variant).order_by("expire_date")
        total_stock = stocks.aggregate(Sum('stock')).get('stock__sum')

        if not stocks.exists():
            not_available.append({
                "id": item.id,
                "stock": 0,
                "qty": item.qty,
                "product_id": item.product_variant_id,
                "name": str(item.product_variant)
            })

        elif stocks.filter(stock__gte=item.qty):
            # stock available
            pass
        elif total_stock < item.qty:
            not_available.append({
                "id": item.id,
                "stock": total_stock,
                "qty": item.qty,
                "product_id": item.product_variant_id,
                "name": str(item.product_variant)
            })

    if len(not_available) > 0:
        return False, not_available

    return True, warehouse_id
