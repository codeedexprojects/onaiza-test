import datetime
from products.models import Category
from web.forms import SignUpForm, PincodeForm
from users.models import *
from web.functions import get_cart_total
from warehouses.models import *
from offers.models import VoucherCode
from decimal import Decimal
from customers.models import Customer, Ticket
from api.v1.users.functions import get_privliged_points



def web_context(request):
    categories = Category.objects.filter(is_admin_approved=True, is_deleted=False, )[:7]
    full_categories = Category.objects.filter(is_admin_approved=True, is_deleted=False, )[:7]
    locations = Location.objects.filter(is_deleted=False)
    tickets = None
    tickets_resolved_instances = None
    privilege_points = 0
    privilege_points_amt = 0

    language_code = request.LANGUAGE_CODE

    pincode_session = None
    coupon_session_amt = request.session.get('coupon_amt', 0)
    coupon_pk = request.session.get('coupon_id', 0)

    # if locations not avail
    if 'pincode' in request.session:
        pincode_session = request.session.get('pincode', '')
    else:
        if locations.exists():
            pincode_session = locations.first()
        else:
            pincode_session = 0

    customer_instance = None
    voucher_codes = None
    auth_status = False
    wishlist = None
    cart = None
    cart_total = 0
    cart_items = None
    wishlist_items = None
    cart_grand_total = 0
    is_wallet_applied = False
    wallet_applied_amt = 0
    input_value_point = 0

    today = datetime.datetime.now()

    privilege_instances = PrivilegePoint.objects.filter(is_deleted=False)
    user_notifications = Notification.objects.none()

    if request.user.is_authenticated and not request.user.is_superuser:
        user_notifications = Notification.objects.filter(is_deleted=False, is_active=True, is_read=False, user=request.user)
        wishlist = Wishlistitem.objects.filter(is_deleted=False, customer__user=request.user)

        # wishlist_items = [item.product_variant.pk for item in wishlist]
        wishlist_items = wishlist.values_list('product_variant_id', flat=True)

        all_tickets = Ticket.objects.filter(is_deleted=False, customer__user=request.user)
        tickets = all_tickets.filter(status__in=["pending","in_progress"])
        tickets_resolved_instances = all_tickets.filter(status__in=["solved"])

        voucher_codes = VoucherCode.objects.filter(is_deleted=False, start_time__lte=today, end_time__gte=today)

        if Customer.objects.filter(user=request.user).exists():
            customer_instance = request.user.customer
            privilege_points = customer_instance.current_privilege_points
            auth_status = True

        if privilege_instances.exists():
            value_points = privilege_instances.first().value_of_point
            privilege_points_amt = value_points * privilege_points

        cart = CartItem.objects.filter(customer__user=request.user, is_deleted=False)
        cart_items = cart.values_list('product_variant_id', flat=True)

        cart_total = get_cart_total(request)

        if coupon_session_amt:
            cart_grand_total = cart_total - Decimal(coupon_session_amt)
        else:
            cart_grand_total = cart_total

        input_value_point = privilege_points
        if 'wallet' in request.session:
            amt = request.session.get('wallet', '') or 0
            amt = Decimal(amt)
            wallet_applied_amt  = amt * value_points

            cart_grand_total = cart_grand_total - Decimal(wallet_applied_amt)
            input_value_point = amt

    return {
        "user_notifications": user_notifications,
        "categories": categories,
        "full_categories": full_categories,
        "auth_status": auth_status,
        "wishlist": wishlist,
        "wishlist_items": wishlist_items,
        "cart": cart,
        "is_cart": cart_items,
        "cart_amt": cart_total,
        "cart_grand_total":cart_grand_total,
        "app_title": "Onaiza",
        "pincode": locations,
        "tickets":tickets,
        "ticktes_solved": tickets_resolved_instances,
        "pincode_session": pincode_session,
        "voucher_codes": voucher_codes,
        "coupon_session_amt":coupon_session_amt,
        "privilege_points":privilege_points,
        "privilege_points_amt":privilege_points_amt,
        "coupon_pk":coupon_pk,
        "is_wallet_applied":is_wallet_applied,
        "wallet_applied_amt":wallet_applied_amt,
        "language_code":language_code,
        "input_value_point":input_value_point,
        "customer_instance":customer_instance,
    }
