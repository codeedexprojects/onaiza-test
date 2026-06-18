import datetime
import decimal
import random
import string
from datetime import datetime, timezone
from decimal import Decimal

from cryptography.fernet import Fernet
from customers.models import Customer, PrivilegePoint
from django.conf import settings
from django.db.models import Q, Avg
from finance.models import InvoicePrefix
from general.models import Batch
from orders.models import OrderItem, Orders
from products.models import ProductVariant
from users.models import CartItem
from web.models import ProductReview


def get_otp(size=4, chars=string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def load_key():
    key = getattr(settings, "PASSWORD_ENCRYPTION_KEY", None)
    if key:
        return key
    else:
        raise ImproperlyConfigured("No configuration  found in your PASSWORD_ENCRYPTION_KEY setting.")


def encrypt_message(message):
    key = load_key()
    encoded_message = message.encode()
    f = Fernet(key)
    encrypted_message = f.encrypt(encoded_message)
    return (encrypted_message.decode("utf-8"))


def decrypt_message(encrypted_message):
    key = load_key()
    f = Fernet(key)
    decrypted_message = f.decrypt(encrypted_message.encode())
    return decrypted_message.decode()


def get_user(user):
    user = Customer.objects.get(user=user)
    return user


def get_cart_item_price(request):
    try:
        user = request.user
        pincode_session = request.session.get('pincode', '')
        today = datetime.now()

        cart = CartItem.objects.filter(customer__user=user, is_deleted=False)

        total = 0
        for i in cart:
            if Batch.objects.filter(is_deleted=False, product_variant=i.product_variant,warehouse__location__pincode=pincode_session,expire_date__gt=today).exists():
                batch_instance = Batch.objects.filter(is_deleted=False, product_variant=i.product_variant,warehouse__location__pincode=pincode_session,expire_date__gt=today).order_by('-date_added').first()
                total = total + i.qty * batch_instance.mrp
            else:
                total = total + i.qty * i.product_variant.mrp

        return total
    except Exception as e:

        return str(e)


def get_privliged_points(request):
    try:
        customer_instance = Customer.objects.get(user=request.user)
        print("The user is ===>",request.user)

        point = PrivilegePoint.objects.filter(is_deleted=False).first()
        value_of_point = point.value_of_point

        customer_available_points = customer_instance.current_privilege_points
        customer_available_points_to_cash = float(customer_available_points) * float(value_of_point)

        wallet_amount = float(point.value_of_point) * float(customer_available_points)

        print("avail points", customer_available_points)
        print("Cirremt cash ",customer_available_points_to_cash)
        print("Value Of Point",value_of_point)
        print("wallet amojunt", wallet_amount)
        print("Csutomer available points", customer_available_points)

        is_applied = False
        applied_value = 0
        applied_value_to_cash = 0

        if 'wallet' in request.session:
            is_applied = True
            applied_value = request.session.get('wallet', 0)
            if not applied_value:
                applied_value = 0
            applied_value_to_cash = float(applied_value) * float(value_of_point)

        response_data = {
            "points": str(value_of_point),
            "available_points": str(customer_available_points),
            "available_points_to_cash": str(customer_available_points_to_cash),
            # wallet balance is converted to cash amount
            "wallet_balance": str(round(wallet_amount, 2)),
            "is_applied": is_applied,
            "applied_value": applied_value,
            "applied_value_to_cash": applied_value_to_cash,
        }

    except Exception as e:
        response_data = {
            "message": "Something Went Wrong!",
            "error": str(e),
        }
    return response_data


def get_grand_total(item_price, request):
    coupon_session_amt = 0
    wallet_session_amt = 0

    # del request.session['wallet']

    # print("The session value is ", request.session['wallet'])

    if 'coupon_amt' in request.session:
        print("inside coupon")
        coupon_session_amt = request.session.get('coupon_amt', 0)

    if 'wallet' in request.session:
        print("Inside wallet")
        wallet_session_amt = request.session.get('wallet', 0)

    print("wallet session amount==>", wallet_session_amt)
    if not coupon_session_amt:
        coupon_session_amt = 0
    if not wallet_session_amt:
        wallet_session_amt = 0

    print(f"{coupon_session_amt} - wallet :-{wallet_session_amt} - {item_price} +. ")

    grand_total = float(item_price) - float(coupon_session_amt) - float(wallet_session_amt)

    return grand_total


def add_privilege_point(request, order):
    customer_instance = Customer.objects.get(user=request.user)
    point_instance = PrivilegePoint.objects.filter(is_deleted=False).first()

    online_order_points = point_instance.point_gained_online

    if order.total_amt >= point_instance.minimum_amount:
        points_gained = (Decimal(order.total_amt) // Decimal(point_instance.minimum_amount)) * online_order_points

        customer_instance.current_privilege_points += points_gained
        customer_instance.privilege_points += points_gained

        customer_instance.save()
        return True
    else:
        return False


def clear_cart(customer, order, request):
    instances = None
    pincode = request.session.get('pincode', '')

    if CartItem.objects.filter(customer=customer):
        instances = CartItem.objects.filter(customer=customer)

        for cart_item in instances:
            if Batch.objects.filter(product_variant=cart_item.product_variant, warehouse__location__pincode=pincode).exists():
                batch_instance = Batch.objects.filter(product_variant=cart_item.product_variant,warehouse__location__pincode=pincode).order_by('-date_added').first()
                OrderItem.objects.create(product_variant=cart_item.product_variant, qty=cart_item.qty, order=order, price=batch_instance.retail_price, batch=batch_instance)

                stock = batch_instance.stock
                if stock > 0:
                    # ProductVariant.objects.filter(id=cart_item.product_variant.id).update(stock=stock - cart_item.qty)
                    batch_instance.stock = stock - cart_item.qty
                    batch_instance.save()
                    cart_item.delete()
                else:
                    return False

        if 'coupon_amt' in request.session:
            del request.session['coupon_amt']
        if 'wallet' in request.session:
            del request.session['wallet']
        if 'coupon_id' in request.session:
            del request.session['coupon_id']

        add_privilege_point(request, order)

        return True
    else:
        return False


def get_order_prefix():
    order_prefix = None
    if InvoicePrefix.objects.filter(is_active=True, is_deleted=False, financial_year__is_active=True).exists():
        prefix = InvoicePrefix.objects.filter(is_active=True, is_deleted=False, financial_year__is_active=True).first()
        prefix_actual_count = Orders.objects.filter(Q(order_id__icontains=prefix.order)).count()
        new_order_prefix_to_string = int(prefix_actual_count) + 1

        return f"{prefix.order}{new_order_prefix_to_string}"
    else:
        return f"NONE"


def update_current_rating(product_instance):
    average = ProductReview.objects.filter(product_variant=product_instance).aggregate(Avg('rating'))
    product_instance.current_rating = decimal.Decimal(average['rating__avg'])
    product_instance.save()
    print(average['rating__avg'])


def is_eligible_for_return(product_variant, order_id):
    try:
        product_variant_instances = ProductVariant.objects.get(pk=product_variant)

        returnable_duration_type = product_variant_instances.product.returnable_duration_type

        order_instances = Orders.objects.get(pk=order_id)

        today_date = datetime.now().replace(tzinfo=None)
        order_date = order_instances.date_added.replace(tzinfo=None)

        if 'day' in returnable_duration_type:
            day_duration = product_variant_instances.product.returnable_duration
            date_differnce = (today_date - order_date).days

            print('\n\n')
            print('day   ', product_variant_instances.product_id, '   ---')
            print('day_duration--------', day_duration)
            print('date_differnce------', date_differnce)
            print('\n\n')

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

    except Exception as e:
        print(e)
        return False
