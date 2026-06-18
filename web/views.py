# Standard libraries
import re
import datetime
import json
import requests

from api.v1.general.functions import is_pincode_exists, get_pincode
from api.v1.users.functions import decrypt_message, update_current_rating
# django libraries
from django.conf import settings as SETTINGS
from django.contrib.auth import login, authenticate
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.core import serializers
from django.db.models import Count, Q, F, Max
from django.http.response import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
# local libraries
from finance.models import InvoicePrefix
from general.models import Batch
from main.decorators import role_required
from main.functions import generate_form_errors, get_auto_id, get_otp, sendSMS
from offers.models import Offers, DealOfDay, VoucherCode
from customers.models import UserOtpData, Customer, CustomerAddress
from orders.models import OrderItem, Orders, TimeSlot, Booking
from products.models import Category, SubCategory, ProductVariant, ProductImages
from users.forms import *
from users.functions import get_user
from users.models import *
from vendors.models import Vendor
from warehouses.models import Location
from web.forms import ProfileForm, SpotlightBannerForm
from web.functions import get_cart_total, clear_cart, get_order_prefix, get_shop_category_instances, save_return, \
    is_eligible_for_cancel, get_queried_params, check_stock_availability
from web.models import *

from api.v1.users.functions import encrypt_message



class PincodeAutoComplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Location.objects.none()

        items = Location.objects.filter(is_deleted=False)

        if self.q:
            query = self.q
            items = items.filter(Q(pincode__icontains=query))

        return items


def about_us(request):
    title = "About us"

    context = {
        "title": title,
    }

    return render(request, 'web/informations/about-us.html', context)


def delivery_info(request):
    title = "Delivery Information"

    context = {
        "title": title,
    }

    return render(request, 'web/informations/delivery-info.html', context)


def privacy_policy(request):
    title = "Privacy policy"

    context = {
        "title": title,
    }

    return render(request, 'web/informations/privacy-policy.html', context)


def terms_and_contition(request):
    title = "Terms And Condition"

    context = {
        "title": title,
    }

    return render(request, 'web/informations/tac.html', context)


def index(request):
    pincode_session = request.session.get('pincode', '')
    now_time = datetime.datetime.now()

    spotlight_banners = SpotlightBanner.objects.filter(is_deleted=False)
    shop_instances = Vendor.objects.filter(is_deleted=False)
    category_instances = Category.objects.filter(is_deleted=False)
    offer_instances = Offers.objects.filter(start_time__lte=now_time, end_time__gte=now_time, is_deleted=False)

    featured_cat_instances = category_instances.filter(is_featured=True, product__isnull=False).distinct()

    offer_instance = None
    if offer_instances:
        offer_instance = offer_instances.order_by('-date_added').first()
        offer_instances = offer_instances.exclude(pk=offer_instance.pk)

    if pincode_session:
        shop_instances = shop_instances.filter(location__pincode=pincode_session)
        offer_instances = Offers.objects.filter(warehouse__location__pincode=pincode_session)

    variants = ProductVariant.objects.filter(is_deleted=False, is_admin_approved=True, product__is_active=True).order_by("?")

    # get the best sellers item on the basis of order+sale count
    best_sellers = variants.annotate(
        order_count=Count('orderitem'),
        sale_count=Count('saleitem'),
        total_count=F('sale_count') + F('order_count')
    ).order_by('-total_count')[:8]  # to get only 8 variants

    query = request.GET.get("q")

    if query:
        variants = variants.filter(
            Q(title__icontains=query) |
            Q(product__name__icontains=query)
        )
    context = {
        "title": "Home",
        "search_title": "products",
        "is_index": True,
        "featured_cat_instances": featured_cat_instances,
        "variants": variants,
        "shops": shop_instances,
        "categories": category_instances,
        "offer_instances": offer_instances,
        "offer_instance": offer_instance,
        "best_sellers": best_sellers,
        "lang": request,
        "spotlight_banners": spotlight_banners,
    }
    return render(request, "web/index.html", context)


def signup(request):
    phone = request.GET.get("phone")
    name = request.GET.get("username")

    response_data = {}

    if phone and name:
        if len(phone) == 10:
            otp = get_otp()

            if not User.objects.filter(username=phone,is_active=True).exists():
                if not UserOtpData.objects.filter(phone=phone).exists():
                    UserOtpData.objects.create(
                        name=name,
                        phone=phone,
                        otp=otp,
                        password=encrypt_message(phone)
                    )

                else:
                    UserOtpData.objects.filter(phone=phone).update(otp=str(otp))

                if User.objects.filter(username=phone).exists():
                    user_data = User.objects.get(username=phone)
                else:
                    user_data = User.objects.create_user(
                        username=phone,
                        password=phone,
                        is_active=False,
                    )

                message = f"Dear customer, {otp} is your OTP from ONAIZA. Don't share your OTP with anyone."
                msg = sendSMS('otp', phone, [otp])
                print('\n\n-------------', otp, '-------------\n\n')

                # message = f"Dear customer, {otp} is your OTP from ONAIZA. Don't share your OTP with anyone."
                # msg = sendSMS(phone, message)
                # print('\n\n-------------', msg, '-------------\n\n')

                if Group.objects.filter(name="customer_user").exists():
                    group = Group.objects.get(name="customer_user")
                else:
                    group = Group.objects.create(name="customer_user")

                user_data.groups.add(group)

                if not Customer.objects.filter(user=user_data).exists():
                    Customer.objects.create(
                        user=user_data,
                        name=name,
                        phone=phone,
                        customer_type='b2c',
                        auto_id=get_auto_id(Customer),
                        creator=user_data,
                        updater=user_data
                    )
                else:
                    Customer.objects.filter(user=user_data).update(name=name)

                response_data = {
                    "status": 'true'
                }

            elif not Customer.objects.filter(user__username=phone).exists():
                password = phone
                if DeliveryAgents.objects.filter(user__username=phone).exists():
                    agent = DeliveryAgents.objects.get(user__username=phone)
                    password = decrypt_message(agent.password)

                if not UserOtpData.objects.filter(phone=phone).exists():
                    UserOtpData.objects.create(
                        name=name,
                        phone=phone,
                        otp=otp,
                        password=encrypt_message(password)
                    )

                else:
                    UserOtpData.objects.filter(phone=phone).update(otp=str(otp))

                if User.objects.filter(username=phone).exists():
                    user_data = User.objects.get(username=phone)
                else:
                    user_data = User.objects.create_user(
                        username=phone,
                        password=phone,
                        is_active=False,
                    )

                message = f"Dear customer, {otp} is your OTP from ONAIZA. Don't share your OTP with anyone."
                msg = sendSMS('otp', phone, [otp])
                print('\n\n-------------', otp, '-------------\n\n')

                # message = f"Dear customer, {otp} is your OTP from ONAIZA. Don't share your OTP with anyone."
                # msg = sendSMS(phone, message)
                # print('\n\n-------------', msg, '-------------\n\n')

                if Group.objects.filter(name="customer_user").exists():
                    group = Group.objects.get(name="customer_user")
                else:
                    group = Group.objects.create(name="customer_user")

                user_data.groups.add(group)

                if not Customer.objects.filter(user=user_data).exists():
                    Customer.objects.create(
                        user=user_data,
                        name=name,
                        phone=phone,
                        customer_type='b2c',
                        auto_id=get_auto_id(Customer),
                        creator=user_data,
                        updater=user_data
                    )
                else:
                    Customer.objects.filter(user=user_data).update(name=name)

                response_data = {
                    "status": 'true'
                }
            else:
                response_data = {
                    "status": '6001',
                    "message": "User already exists"
                }
        else:
            response_data = {
                "status": '6001',
                "message": "Please enter your 10 digit mobile number without space and don't add 91 or 0 or +91 before your number"
            }

    else:
        response_data = {
            "status": 'false'
        }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


def userlogin(request):
    phone = request.GET.get("phone")
    otp = get_otp()

    response_data = {}

    if phone:
        if User.objects.filter(username=phone,is_active=True).exists():
            if Customer.objects.filter(user__username=phone).exists():
                UserOtpData.objects.filter(phone=phone).update(
                    otp=str(otp),
                )
                otp_data, updated = UserOtpData.objects.update_or_create(phone=phone, defaults={'otp': otp})

                # update user password
                # user = User.objects.get(username=phone)
                # user.set_password(str(otp))
                # user.save()

                message = f"Dear customer, {otp} is your OTP from ONAIZA. Don't share your OTP with anyone."
                msg = sendSMS('otp', phone, [otp])

                print('\n\n-------------', otp, '-------------\n\n')

                response_data = {
                    "status": "true"
                }

            else:
                response_data = {
                    "status": "false"
                }
        else:
            response_data = {
                "status": "false"
            }

    else:
        response_data = {
            "status": "6001"
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


def verify_otp(request):
    otp = request.GET.get("otp")
    phone = request.GET.get("phone")

    response_data = {}
    print(phone,"------------", otp)

    if otp:
        print("First ==> if")
        if UserOtpData.objects.filter(phone=phone).exists():
            print("First if")

            if UserOtpData.objects.filter(phone=phone, otp=otp).exists():
                otp_data = UserOtpData.objects.get(phone=phone, otp=otp)
                print("2nd if")
                user_data = User.objects.get(username=phone)

                username = user_data.username
                password = user_data.password

                user_data.is_active = True
                user_data.save()

                print(password)
                print(username)
                print('-----------------------------')
                password = decrypt_message(otp_data.password)
                print(password)

                user = authenticate(username=username, password=password)

                print(user)

                if user is not None:
                    print("sec if")

                    login(request, user)
                    response_data = {
                        "status": "true"
                    }

                else:
                    # user not found
                    response_data = {
                        "status": "6002"
                    }

            else:
                # otp error
                print("OTP record not found")
                response_data = {
                    "status": "false"
                }
    else:
        # user not registred
        print("phone not found")

        response_data = {
            "status": "6001"
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


def shops(request):
    shop_instance = Vendor.objects.filter(is_deleted=False)
    context = {
        "title": "Shops",
        "search_title": "products",
        'instances': shop_instance,
    }

    return render(request, 'web/shops.html', context)


def add_to_wishlist(request):
    products = request.GET.get('product_variant')
    product_instance = ProductVariant.objects.get(pk=products)

    response_data = {}

    if request.user.is_authenticated:
        customer = get_user(request.user)
        # Wishlistitem check
        if Wishlistitem.objects.filter(product_variant=product_instance, customer=customer, is_deleted=False).exists():
            Wishlistitem.objects.filter(
                product_variant=product_instance,
                customer=customer
            ).update(is_deleted=True)

            response_data = {
                "status": "removed"
            }
        else:
            Wishlistitem.objects.create(
                product_variant=product_instance,
                customer=customer
            )
            response_data = {
                "status": "added"
            }
    else:
        response_data = {
            "status": "null"
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@role_required(['customer_user'])
def view_wishlist(request):
    wishlist = Wishlistitem.objects.filter(is_deleted=False, customer__user=request.user)

    context = {
        "title": "My Wishlist",
        'instances': wishlist
    }

    return render(request, 'web/whishlist.html', context)


def product(request, pk):
    pincode_session = request.session.get('pincode', '')

    instance = get_object_or_404(ProductVariant.objects.filter(pk=pk, is_deleted=False))

    batch = Batch.objects.filter(product_variant__pk=pk, is_deleted=False, stock__gt=0, warehouse__location__pincode=pincode_session).first()
    images = ProductImages.objects.filter(product_variant_id=pk, is_deleted=False)
    reviews = ProductReview.objects.filter(product_variant_id=pk, is_deleted=False)
    variants = ProductVariant.objects.filter(product_id=instance.product_id, is_admin_approved=True, product__is_active=True, is_deleted=False)

    review_count = reviews.count()

    related_products = ProductVariant.objects.filter(
        Q(product__category_id=instance.product.category_id) |
        Q(product__vendor_id=instance.product.vendor_id) |
        Q(product__brand_id=instance.product.brand_id),
        is_deleted=False, product__is_active=True, is_admin_approved=True
    ).exclude(product_id=instance.product_id).order_by("product_id").distinct("product_id")

    context = {
        "title": instance.title,
        'instance': batch,
        'images': images,
        'variants': variants,
        'product_variant': instance,
        'is_need_datepicker': False,
        "review_instances": reviews,
        "review_count": review_count,
        "related_products": related_products,
    }

    return render(request, 'web/single-product.html', context)


def add_to_cart(request):
    products = request.GET.get('product_variant')
    product_instance = ProductVariant.objects.get(pk=products)

    response_data = {}

    pincode_session = request.session.get('pincode', '')

    if request.user.is_authenticated:
        location = Location.objects.filter(pincode = pincode_session).first()
        warehouse = Warehouse.objects.filter(location=location)

        customer = get_user(request.user)
        cart_items = CartItem.objects.filter(customer=customer, is_deleted=False)

        # Cart item check
        if cart_items.exists():
            if cart_items.filter(product_variant=product_instance).exists():
                CartItem.objects.filter(
                    product_variant=product_instance,
                    customer=customer
                ).delete()

                response_data = {
                    "status": "removed"
                }
            elif not cart_items.filter(warehouse__in=warehouse).exists():
                response_data = {
                    "status": "different-location",
                    "message": f"Since you are adding {product_instance} from different location either you can remove current items in your cart and add the current product or \
                        you can check out your current cart items with {cart_items.count()} item(s) and proceed to add {product_instance} to your cart"
                }
            else:
                # check if the product is avail in that pincode

                if Batch.objects.filter(product_variant=product_instance, warehouse__location__pincode=pincode_session, stock__gt=0).exists():
                    CartItem.objects.create(
                        product_variant=product_instance,
                        customer=customer,
                        warehouse = warehouse.first()
                    )
                    response_data = {
                        "status": "added"
                    }
                else:
                    response_data = {
                        "status": "not_in_batch"
                    }

        else:
            # check if the product is avail in that pincode
            if Batch.objects.filter(product_variant=product_instance, warehouse__location__pincode=pincode_session, stock__gt=0).exists():
                CartItem.objects.create(
                    product_variant=product_instance,
                    warehouse = warehouse.first(),
                    customer=customer
                )

                response_data = {
                    "status": "added"
                }
            else:
                response_data = {
                    "status": "not_in_batch"
                }
    else:
        response_data = {
            "status": "null"
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@role_required(['customer_user'])
def increment_cart(request):
    customer = get_user(request.user)
    products = request.GET.get('product_variant')

    print("============================")

    product_instance = ProductVariant.objects.get(pk=products)

    response_data = {}

    # cart item check
    if CartItem.objects.filter(product_variant=product_instance, customer=customer, is_deleted=False).exists():
        cart_item_instance = CartItem.objects.get(product_variant=product_instance, customer=customer, is_deleted=False)
        cart_item_instance.qty = cart_item_instance.qty + 1
        cart_item_instance.price = cart_item_instance.qty * product_instance.mrp

        cart_item_instance.save()

        new_price = cart_item_instance.price * cart_item_instance.qty

        response_data = {
            "status": "updated",
            "qty": cart_item_instance.qty,
            "total": str(new_price)
        }
    else:

        response_data = {
            "status": "eroor"
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@role_required(['customer_user'])
def decrement_cart(request):
    products = request.GET.get('product_variant')
    customer = get_user(request.user)
    product_instance = ProductVariant.objects.get(pk=products)

    response_data = {}

    # cart item check
    if CartItem.objects.filter(product_variant=product_instance, customer=customer, is_deleted=False).exists():
        cart_item_instance = CartItem.objects.get(product_variant=product_instance, customer=customer, is_deleted=False)
        cart_item_instance.qty = cart_item_instance.qty - 1
        cart_item_instance.price = cart_item_instance.qty * product_instance.mrp

        cart_total = get_cart_total(request)

        if cart_item_instance.qty == 0:
            CartItem.objects.filter(pk=cart_item_instance.pk).delete()

            response_data = {
                "status": "true",
                "qty": 0,
                "total": str(cart_total)
            }

            # response_data = {
            #     "status": "stopped",
            #     "message": "cannot deduct from zero"
            # }
        else:

            cart_item_instance.save()

        response_data = {
            "status": "updated",
            "qty": cart_item_instance.qty,
            "total": str(cart_total)
        }
    else:

        response_data = {
            "status": "eroor"
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


def product_by_category(request, pk):
    now_time = datetime.datetime.now()
    pincode_session = request.session.get('pincode', '')
    instance = Category.objects.get(pk=pk)
    shop_instances = Vendor.objects.filter(is_deleted=False, location__pincode=pincode_session)

    variants = ProductVariant.objects.filter(is_deleted=False, is_admin_approved=True, is_default=True, product__category_id=pk, product__is_active=True)
    offer_instance = Offers.objects.filter(start_time__lte=now_time, end_time__gte=now_time, is_deleted=False).order_by(
        '-date_added').first()

    if pincode_session:
        offer_instance = Offers.objects.filter(start_time__lte=now_time, end_time__gte=now_time,
                                               is_deleted=False, warehouse__location__pincode=pincode_session).order_by(
            '-date_added').first()

    context = {
        "title": instance.name,
        'shop_instances': shop_instances,
        "instance": instance,
        "variants": variants,
        "offer_instance": offer_instance,
    }

    return render(request, 'web/category.html', context)


def product_by_subcategory(request, pk):
    pincode_session = request.session.get('pincode', '')
    subcategory = SubCategory.objects.get(pk=pk)
    variants = ProductVariant.objects.filter(is_deleted=False, is_admin_approved=True, product__is_active=True, is_default=True, product__subcategory=subcategory)
    shop_instances = Vendor.objects.filter(is_deleted=False, location__pincode=pincode_session)

    context = {
        "title": "",
        'shop_instances': shop_instances,
        "variants": variants
    }

    return render(request, 'web/category.html', context)


@role_required(['customer_user'])
def view_profile(request):
    profile_instance = get_object_or_404(Customer.objects.filter(user__username=request.user))

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile_instance)
        if form.is_valid():
            data = form.save(commit=False)
            data.date_updated = datetime.datetime.now()
            data.save()

            return HttpResponseRedirect(reverse('web:view_profile'))

        else:

            return JsonResponse({'error': True, 'errors': form.errors })

    else:

        form = ProfileForm(instance=profile_instance)
        context = {
            'instance': profile_instance,
            'form': form,
            'url': reverse('web:view_profile')
        }

        return render(request, 'web/profile.html', context)


def shops(request):
    now = datetime.datetime.now()
    current_date = now.strftime("%Y-%m-%d")

    pincode_session = request.session.get('pincode', '')

    shop_instance = Vendor.objects.filter(is_deleted=False, location__pincode=pincode_session)
    variants = ProductVariant.objects.filter(is_deleted=False, product__is_active=True, is_admin_approved=True, is_default=True)
    deals_of_day = DealOfDay.objects.filter(deal_date__gte=current_date).first()
    offer_instance = Offers.objects.filter(start_time__lte=now, end_time__gte=now, is_deleted=False).order_by(
        '-date_added').first()

    if pincode_session:
        offer_instance = Offers.objects.filter(start_time__lte=now, end_time__gte=now,
                                               is_deleted=False, warehouse__location__pincode=pincode_session).order_by(
            '-date_added').first()

    query = request.GET.get("q")

    if query:
        shop_instance = shop_instance.filter(
            Q(name__icontains=query) |
            Q(malayalam_name__icontains=query)
        )
        variants = variants.filter(
            Q(title__icontains=query) |
            Q(product__name__icontains=query)
        )
    context = {
        "title": "Shops",
        "search_title": "shops",

        'is_shop': True,
        'instances': shop_instance,
        'variants': variants,
        'deals_of_day': deals_of_day,
        "offer_instance": offer_instance,
    }

    return render(request, 'web/shops.html', context)


@role_required(['customer_user'])
def payment(request):
    cart_instances = CartItem.objects.filter(is_deleted=False, customer__user=request.user)
    address_instances = CustomerAddress.objects.filter(is_deleted=False, customer__user=request.user)
    pin_code_instances = Location.objects.filter(is_deleted=False)
    time_slots = TimeSlot.objects.filter(is_deleted=False)

    address_count = CustomerAddress.objects.filter(is_deleted=False, customer__user=request.user).count()

    # for creating address
    if request.method == "POST":

        is_home_or_office = request.POST.get('homeoroffice')
        is_default = request.POST.get('default')

        print("Is home or office", is_home_or_office)

        form = AddressForm(request.POST)
        if form.is_valid():
            address_data = form.save(commit=False)
            address_data.customer = get_user(request.user)

            if is_home_or_office == 'home':
                address_data.address_type = 10
                print("jome")

            elif is_home_or_office == 'office':
                print("office")
                address_data.address_type = 20

            if is_default:
                if CustomerAddress.objects.filter(customer__user=request.user, is_deleted=False, is_default=True).exists():
                    CustomerAddress.objects.filter(customer__user=request.user, is_deleted=False, is_default=True).update(is_default=False)
                    address_data.is_default = True
                else:
                    address_data.is_default = True
            else:
                address_data.is_default = False

            address_data.save()

            # response_data = {
            #     "status": "true",
            #     "title": "Successfully created address",
            #     "message": " successfully created.",
            #     "redirect": "true",
            #     "redirect_url": reverse('web:payment')
            # }
            #
            # return HttpResponse(json.dumps(response_data), content_type='application/javascript')

            return HttpResponseRedirect(reverse('web:payment'))


        else:

            # return JsonResponse({
            #     "status": "true",
            #     'error': False,
            #     'message': 'Category Updated',
            #     "redirect": 'true',
            #     "redirect_url": reverse('products:category', kwargs={"pk": pk})
            # })

            return HttpResponseRedirect(reverse('web:payment'))

    else:
        address_form = AddressForm()

        context = {
            'title': "Payment",
            'cart_instances': cart_instances,
            'address_instances': address_instances,
            'pin_code_instances': pin_code_instances,
            "time_slots": time_slots,

            'address_count': address_count,
            'address_form': address_form,

            'url': reverse("web:payment"),

            'redirect': True,
            'is_no_need_autocomplete': True,
            'is_need_ui': True,
        }

        return render(request, 'web/payment.html', context)


@role_required(['customer_user'])
def delete_address(request, pk):
    CustomerAddress.objects.filter(pk=pk).update(is_deleted=True)

    response_data = {
        "status": "true",
        "title": "Successfully Deleted",
        "message": "Category Successfully Deleted.",
        "redirect": "true",
        "redirect_url": reverse('web:payment')
    }

    # return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    return HttpResponseRedirect(reverse('web:payment'))


@role_required(['customer_user'])
def get_address_edit_form(request, pk):
    instance = CustomerAddress.objects.get(pk=pk)

    form = AddressForm(instance=instance)

    context = {
        "pk": pk,
        "address_form": form,
        "address_type": instance.address_type,
    }
    html_content = render_to_string('web/includes/address-form.html', context, request=request)

    response_data = {
        "status": "true",
        "html_content": html_content,
    }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@role_required(['customer_user'])
def edit_address(request, pk):
    instance = CustomerAddress.objects.get(pk=pk)
    form = AddressForm(request.POST, instance=instance)

    if form.is_valid():
        is_home_or_office = request.POST.get('homeoroffice')

        data = form.save(commit=False)

        if is_home_or_office == 'home':
            data.address_type = 10
            print("jome")

        elif is_home_or_office == 'office':
            print("office")
            data.address_type = 20

        data.is_default = True
        data.save()

        CustomerAddress.objects.filter(customer__user=request.user).exclude(id=pk).update(is_default=False)

    #     response_data = {
    #         "status": "true",
    #         "title": "Successfully created address",
    #         "message": " successfully created.",
    #         "redirect": "true",
    #         "redirect_url": reverse('web:payment')
    #     }

    # else:
    #     response_data = {
    #         "status": "false",
    #         "title": "Validation error!",
    #         "message": generate_form_errors(form, False)
    #     }

    # return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    return HttpResponseRedirect(reverse('web:payment'))


@role_required(['customer_user'])
def proceed_to_payment(request, pk):

    context = {
        'url': reverse("web:payment"),

        'redirect': True,
        'is_no_need_autocomplete': True
    }

    return render(request, 'web/payment.html', context)


@role_required(['customer_user'])
def set_default_address(request):
    address_pk = request.GET.get('address')

    if CustomerAddress.objects.filter(customer__user=request.user, is_deleted=False,
                                      is_default=True).exists():
        CustomerAddress.objects.filter(customer__user=request.user, is_deleted=False,
                                       is_default=True).update(is_default=False)
    # check adress pk
    response_data = {}
    if CustomerAddress.objects.filter(pk=address_pk).exists():
        CustomerAddress.objects.filter(pk=address_pk).update(is_default=True)

        response_data = {
            "status": "true"
        }
    else:
        response_data = {
            "status": "false"
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@role_required(['customer_user'])
def remove_cart(request):
    cart_pk = request.GET.get('pk')

    CartItem.objects.filter(pk=cart_pk).delete()

    cart_total = get_cart_total(request)

    response_data = {
        "status": "true",
        "total": str(cart_total)
    }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@role_required(['customer_user'])
def place_order(request):
    payment_method = request.GET.get('method')
    time_slot = request.GET.get('time_slot')
    delivery_date = request.GET.get('delivery_date')

    fromatted_date = datetime.datetime.now().date()

    if delivery_date:
        fromatted_date = datetime.datetime.strptime(delivery_date, "%d-%m-%Y")

    # eg: credit card number, upi id, debit card number
    source_number = request.GET.get('number')

    # coupon get from session
    coupon_session_amt = 0
    if 'coupon_amt' in request.session:
        coupon_session_amt = request.session.get('coupon_amt', '')

    wallet = 0
    if 'wallet' in request.session:
        wallet = request.session.get('wallet', '')

    pincode_session = request.session.get('pincode', '')

    # if time slot exists take the instance to the variable
    time_slot_instance = None
    if time_slot:
        time_slot_instance = TimeSlot.objects.get(pk=time_slot)

    customer = Customer.objects.get(user=request.user)
    address_instance = CustomerAddress.objects.get(customer__user=request.user, is_default=True)

    stock_ok, data = check_stock_availability(request)

    if stock_ok:
        warehouse_id = data
        pincodes_of_warehouse = Warehouse.objects.get(id=warehouse_id).location.all()

        if address_instance.pincode in pincodes_of_warehouse:
            total_amt = get_cart_total(request)
            # if coupon and wallet exists will be deducted
            cart_amt = get_cart_total(request)
            total_amt = cart_amt - Decimal(coupon_session_amt) - Decimal(wallet)

            order_id = get_order_prefix()
            order_no = 0

            if InvoicePrefix.objects.filter(is_active=True, is_deleted=False).exists():
                prefix = InvoicePrefix.objects.get(is_active=True, is_deleted=False)
                pr_orders = Orders.objects.filter(prefix=prefix)

                if pr_orders.filter(prefix=prefix).exists():
                    order_no = pr_orders.filter(prefix=prefix).aggregate(Max('order_no'))['order_no__max']

                order_no += 1
                order_id = f"{prefix.order}{str(order_no).zfill(6)}"

            order = Orders.objects.create(
                auto_id=get_auto_id(Orders),
                creator=request.user,
                updater=request.user,
                customer=customer,
                warehouse_id = warehouse_id,

                order_id=order_id,
                order_no=order_no,
                prefix=prefix,

                billing_name=address_instance.name,
                billing_phone=address_instance.phone,
                billing_address=address_instance.house_name,
                billing_street=address_instance.street,
                billing_landmark=address_instance.landmark,
                billing_city=address_instance.city,
                billing_state=address_instance.state,

                payment_method=payment_method,
                payment_status="10",
                card_number=source_number,

                order_status="10",
                total_amt=total_amt,
                time_slot=time_slot_instance,
                delivery_date=fromatted_date,
            )

            message = f"Dear ONAIZA customer, your order {order_id} is placed and expected delivered by {fromatted_date}."

            msg = sendSMS('placed', customer.phone, [order_id, str(fromatted_date)])
            print('\n\n-------------', msg, '-------------\n\n')

            clear_cart(customer, order, pincode_session, request)
            if 'wallet' in request.session:
                point = request.session.get('wallet', '')
                customer.current_privilege_points = customer.current_privilege_points - Decimal(point)
                customer.save()
                del request.session['wallet']

            print("Order is ===>>", order)

            response_data = {
                "status": "true",
                "pk": str(order.pk)
            }
        else:
            response_data = {
                "status": "different-location",
                "message": "The selected address's pincode doesn't match with the pincode of the products in your cart."
            }
    else:
        response_data = {
            "status": "stock-unavailable",
            "data": data
        }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@role_required(['customer_user'])
def view_orders(request):
    instances = Orders.objects.filter(customer__user=request.user)

    context = {
        "title": "Order Confirmed",
        'instances': instances,
    }
    return render(request, 'web/my-orders.html', context)


@role_required(['customer_user'])
def order_confirmed(request):
    order_pk = request.GET.get('order')

    order_instance = Orders.objects.get(pk=order_pk)
    order_item_instances = OrderItem.objects.filter(order=order_instance)

    context = {
        "title": "Order Confirmed",
        'order_instance': order_instance,
        'order_item_instances': order_item_instances,
    }
    return render(request, 'web/order-confirmed.html', context)


def set_pincode(request):
    pincode = request.GET.get('pincode')

    request.session['pincode'] = pincode

    response_data = {
        "status": "true"
    }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@role_required(['customer_user'])
def book_product(request):
    product_variant_pk = request.GET.get('product')

    product_variant = ProductVariant.objects.get(pk=product_variant_pk)

    booked_product = Booking.objects.create(
        customer=get_user(request.user),
        product_variant=product_variant,
        message="",
        status="pending",
    )

    response_data = {
        "status": "true"
    }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@role_required(['customer_user'])
def view_booked_product(request):
    instances = Booking.objects.filter(customer__user=request.user)

    context = {
        "title": "Booked Products",
        'instances': instances,
    }
    return render(request, 'web/my-booking.html', context)


def shop(request, pk):
    pincode_session = request.session.get('pincode', '')
    shop = Vendor.objects.get(pk=pk,is_deleted=False)
    product_variants = ProductVariant.objects.filter(product__vendor__pk=pk, is_admin_approved=True, product__is_active=True, product__is_deleted=False)
    # categories = get_shop_category_instances(product_variants)

    context = {
        "title": shop.name,
        "shop": shop,
        # "categories": categories,
        "product_variants": product_variants,
    }

    return render(request, 'web/shop-single.html', context)


@role_required(['customer_user'])
def apply_coupon(request):
    response_data = {}
    pk = request.GET.get('pk')
    total_amt = get_cart_total(request)

    # clear the seession cookies
    if 'coupon_amt' and 'coupon_id' in request.session:
        request.session['coupon_id'] = None
        request.session['coupon_amt'] = None

    # checking if the voucher exists or not
    if VoucherCode.objects.filter(is_deleted=False, pk=pk).exists():
        voucher_instance = VoucherCode.objects.get(pk=pk)

        percent_amt = total_amt * voucher_instance.percentage / 100

        limit_percent_amt = total_amt * voucher_instance.upto_limit / 100

        print(percent_amt)
        print(limit_percent_amt)

        if percent_amt > limit_percent_amt:
            print("Taken fromm the limit")
            diff_amt = total_amt - limit_percent_amt
            stored_amt = limit_percent_amt
        else:
            diff_amt = total_amt - percent_amt
            stored_amt = percent_amt

        new_amt = total_amt - stored_amt

        if 'wallet' in request.session:
            new_amt = new_amt - Decimal(request.session.get('wallet', ''))

        # store coupon percent amt to session
        request.session['coupon_amt'] = str(stored_amt)
        request.session['coupon_id'] = str(voucher_instance.pk)

        response_data = {
            "status": "true",
            "total_amt": str(new_amt),
            "percent_amt": str(stored_amt),
            "coupon_code": str(voucher_instance.voucher_code),
            "coupon_pk": str(voucher_instance.pk)
        }

    else:
        response_data = {
            "status": "0",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@role_required(['customer_user'])
def order_cancel(request):
    response_data = {}

    pk = request.GET.get('pk')
    reason = request.GET.get('reason')

    # check if order exists
    if Orders.objects.filter(pk=pk).exists():
        Orders.objects.filter(pk=pk).update(order_status='40')
        response_data = {
            "status": "true",
        }
    else:
        response_data = {
            "status": "false",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


def product_variant_switch(request):
    response_data = {}

    try:
        pk = request.GET.get('pk')
        language_code = request.LANGUAGE_CODE

        variant = ProductVariant.objects.get(pk=pk)

        stock = 0
        cart = False
        cart_qty = 0
        pincode = None
        is_wishlist = False

        mrp = variant.mrp
        retail_price = variant.retail_price
        image = variant.image.url if variant.image else variant.product.image.url

        if request.user.is_authenticated:
            cart_instance = CartItem.objects.filter(product_variant__pk=pk, customer__user=request.user, is_deleted=False)
            if cart_instance.exists():
                cart = True
                cart_qty = cart_instance.first().qty

            if is_pincode_exists(request):
                pincode = get_pincode(request)

            batchs = Batch.objects.filter(warehouse__location__pincode=pincode, stock__gt=0, is_deleted=False, product_variant=variant)
            if batchs.exists():
                batch = batchs.order_by('-date_added').first()
                mrp = batch.mrp
                stock = batch.stock
                retail_price = batch.retail_price

            if Wishlistitem.objects.filter(customer__user=request.user, product_variant=variant, is_deleted=False).exists():
                is_wishlist = True

        name = None
        if 'ml' in language_code:
            name = variant.get_malayalam_name()

        elif 'en' in language_code:
            name = variant.get_fullname()

        unit = variant.unit.unit

        response_data = {
            "status": "true",
            "name": name,
            "unit": unit,
            "pk": str(pk),
            "mrp": str(mrp),
            "cart": str(cart),
            "image": str(image),
            "stock": str(stock),
            "cart_qty": str(cart_qty),
            "is_wishlist": str(is_wishlist),
            "retail_price": str(retail_price),
        }
    except Exception as e:
        response_data = {
            "status": "false",
        }
        print("Errorr===:", e)

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


def get_pincode_by_name(request):
    places = []

    name = request.GET.get('name')

    baseurl_1 = f"https://api.postalpincode.in/pincode/691559"
    baseurl_place = f"https://api.postalpincode.in/postoffice/{name}"
    baseurl_2 = f"https://maps.googleapis.com/maps/api/geocode/json?address=691559&key={SETTINGS.PLACES_MAPS_API_KEY}"

    postofficeapi_response = requests.get(baseurl_1).json()
    googleapi_response = requests.get(baseurl_2).json()

    place_name_response = requests.get(baseurl_place).json()

    print(googleapi_response)

    if postofficeapi_response[0]["Status"] == 'Success' and googleapi_response['status'] == 'OK':

        if 'PostOffice' in postofficeapi_response[0] and 'postal_code' in googleapi_response['results'][0]['types']:
            for post_offices in postofficeapi_response[0]['PostOffice']:
                response = post_offices
                print(googleapi_response['results'][0]['geometry']['location']['lng'])

        places = []
        post_office_response = place_name_response[0]["PostOffice"]

        if post_office_response:
            for name in place_name_response[0]["PostOffice"]:
                print(name['Name'])
                data = {
                    "name": name['Name'],
                    "pincode": name['Pincode']
                }
                places.append(data)
        else:
            data = {
                "name": "Not Exists!",
                "pincode": "Place not exists"
            }
            places.append(data)

    response_data = {
        "status": "true",
        "values": json.dumps(places),
    }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@role_required(['customer_user'])
def new_issue(request):
    response_data = {}

    try:
        description = request.GET.get('description')
        customer = get_user(request.user)

        Ticket.objects.create(
            customer=customer,
            description=description,
            auto_id=get_auto_id(Ticket),
            creator=request.user,
            updater=request.user,
            status="pending",
        )

        response_data = {
            "status": True
        }

    except Exception as e:
        print("ERROR ===>>", e)
        response_data = {
            "status": False,
            "message": str(e)
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@role_required(['customer_user'])
def apply_wallet_amount(request):
    point = Decimal(request.GET.get('point'))
    response_data = {}
    points_amt = 0
    try:
        if 'wallet' in request.session:
            request.session['wallet'] = None

        cart_item_price = get_cart_total(request)

        customer_instance = Customer.objects.get(user=request.user)
        wallet = customer_instance.current_privilege_points

        if point <= wallet:
            if PrivilegePoint.objects.filter(is_deleted=False):
                value_points = PrivilegePoint.objects.filter(is_deleted=False).first().value_of_point
                points_amt = value_points * point

            if points_amt > cart_item_price:
                response_data = {
                    "status": False,
                    "state": "exceed",
                }

                return HttpResponse(json.dumps(response_data), content_type='application/javascript')
            else:
                request.session['wallet'] = str(point)
                new_total = cart_item_price - points_amt
                customer_instance.save()

                if 'coupon_amt' in request.session:
                    new_total = new_total - Decimal(request.session.get('coupon_amt', ''))

                response_data = {
                    "status": True,
                    "value": str(points_amt),
                    "total": str(new_total),
                    "message": "Wallet Balance Applied Successfully"
                }

    except Exception as e:
        response_data = {
            "status": False,
            "message": "Something went wrong",
            "error": str(e),
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@role_required(['customer_user'])
def get_time_slots(request):
    response_data = {}
    date = request.GET.get('date')
    today = datetime.datetime.now()

    date_format = datetime.datetime.strptime(date, "%d-%m-%Y")
    date_without_time = date_format.strftime('%d-%m-%Y')

    week_number = date_format.isoweekday()

    time_slot_instances = TimeSlot.objects.filter(is_deleted=False, day=week_number)

    if date_format.date() == today.date():
        time_slot_instances = time_slot_instances.filter(start_time__gt=today.time())

    # response_data = {
    #     "slots": serializers.serialize('json', time_slot_instances),
    # }

    slots = []
    for slot in time_slot_instances:
        slots.append({
            'pk': str(slot.pk),
            'name': str(slot),
        })

    response_data = {
        "slots": slots,
    }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@role_required(['customer_user'])
def post_rating(request):
    rating = request.GET.get('rating')
    review = request.GET.get('review')
    order_id = request.GET.get('order_id')

    order_item_instances = OrderItem.objects.filter(order__pk=order_id)

    for i in order_item_instances:
        if review:
            ProductReview.objects.create(
                product_variant=i.product_variant,
                rating=rating,
                creator=request.user,
                updater=request.user,
                auto_id=get_auto_id(ProductReview),
                review=review,
            )
        else:
            ProductReview.objects.create(
                product_variant=i.product_variant,
                rating=rating,
                creator=request.user,
                updater=request.user,
                auto_id=get_auto_id(ProductReview),
            )

        update_current_rating(i.product_variant)

    response_data = {
        "status": True,
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


def search(request):
    variants = ProductVariant.objects.filter(is_deleted=False, is_admin_approved=True, product__is_active=True)

    query = request.GET.get('query')

    if query:
        variants = variants.filter(
            Q(title__icontains=query) |
            Q(product__name__icontains=query) |
            Q(product__brand__name__icontains=query) |
            Q(product__category__name__icontains=query) |
            Q(product__meta_description__iregex=r'[[:<:]]' + re.escape(query)) |
            Q(product__subcategory__name__icontains=query)
        )

    context = {
        "title": f"",
        "variants": variants,
        "is_search": True,
    }

    return render(request, 'web/category.html', context)


@role_required(['customer_user'])
def clear_sessions(request):
    # clear all the sessions
    if 'coupon_amt' in request.session:
        del request.session['coupon_amt']

    if 'wallet' in request.session:
        del request.session['wallet']

    if 'coupon_id' in request.session:
        del request.session['coupon_id']

    response_data = {
        "status": True,
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


def logout_customer(request):
    logout(request)
    return redirect(reverse('web:index'))


@role_required(['customer_user'])
def product_return(request):
    response_data = {}

    try:
        order_item_id = request.GET.get('order_item_pk')
        reason_for_return = request.GET.get('cancel_reason')
        return_specification = request.GET.get('cancel_review')

        order_item_instances = OrderItem.objects.get(pk=order_item_id)

        save_return(order_item_instances.pk, reason_for_return, return_specification, request)

        response_data = {
            "status": 'accepted',
        }

    except Exception as e:
        response_data = {
            "status": str(e),
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@role_required(['customer_user'])
def get_product_details_from_order_item(request):
    response_data = {}

    try:
        order_item_pk = request.GET.get('order_item_pk')
        order_item_instances = OrderItem.objects.get(pk=order_item_pk)
        product_variant_instance = ProductVariant.objects.get(pk=order_item_instances.product_variant.pk)

        response_data = {
            "status": True,
            "product_name": product_variant_instance.get_fullname(),
            "product_image": request.build_absolute_uri(product_variant_instance.image.url),
            "product_category": product_variant_instance.product.category.name,
            "product_mrp": str(order_item_instances.price),
            "order_item_pk": str(order_item_instances.pk),
        }

    except Exception as e:
        response_data = {
            "status": False,
            "message": str(e),
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@role_required(['customer_user'])
def cancel_order(request):
    response_data = {}

    try:
        order_pk = request.GET.get('order_pk')

        order_instances = Orders.objects.get(pk=order_pk)

        print(is_eligible_for_cancel(order_instances))

        if is_eligible_for_cancel(order_instances):
            response_data = {
                "status": "failed",
            }
            if order_instances.order_status == "10":
                print("Cancel")
                order_instances.order_status = "40"
                order_instances.save()

                response_data = {
                    "status": "cancelled",
                }

        else:
            response_data = {
                "status": "failed",
            }

    except Exception as e:
        print(e)
        response_data = {
            "status": False,
            "message": str(e),
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin'])
def create_spotlight_banner(request):
    if request.method == 'POST':
        form = SpotlightBannerForm(request.POST, request.FILES)
        if form.is_valid():
            auto_id = get_auto_id(SpotlightBanner)

            # create spotlight banner
            data = form.save(commit=False)
            data.creator = request.user
            data.updater = request.user
            data.auto_id = auto_id

            data.save()

            response_data = {
                "status": "true",
                "stable": "false",
                "title": "Successfully Created",
                "message": "Spotlight Banner Created Successfully.",
                "redirect": "true",
                "redirect_url": reverse('web:spotlight_banner', kwargs={'pk': data.pk})
            }

        else:
            message = generate_form_errors(form, formset=False)

            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validatruetion error",
                "message": str(message)
            }
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        print("HLOooooooooo")
        form = SpotlightBannerForm()
        context = {
            "title": "Create Spotlight Banner ",
            "form": form,
            "stable": "true",
            "url": reverse('web:create_spotlight_banner'),

        }
        return render(request, 'web/spotlight_banner/spotlight_banner_entry.html', context)


@login_required
@role_required(['superadmin'])
def spotlight_banners(request):
    instances = SpotlightBanner.objects.filter(is_deleted=False)
    title = "Spotlight Banners"
    query = request.GET.get('query')
    if query:
        instances = get_queried_params(query, instances)

    context = {
        "instances": instances,
        'title': title,
        "query": query,

    }
    return render(request, 'web/spotlight_banner/spotlight_banners.html', context)


@login_required
@role_required(['superadmin'])
def spotlight_banner(request, pk):
    instance = get_object_or_404(
        SpotlightBanner.objects.filter(pk=pk, is_deleted=False))

    context = {
        "instance": instance,
        "title": "Spotlight Banner",
        "single_page": True,

    }
    return render(request, 'web/spotlight_banner/spotlight_banner.html', context)


@login_required
@role_required(['superadmin'])
def edit_spotlight_banner(request, pk):
    instance = get_object_or_404(
        SpotlightBanner.objects.filter(pk=pk, is_deleted=False))

    if request.method == 'POST':
        response_data = {}
        form = SpotlightBannerForm(request.POST, request.FILES, instance=instance)

        if form.is_valid():

            # update spotlight banner
            data = form.save(commit=False)
            data.updater = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            response_data = {
                "status": "true",
                "title": "Successfully Updated",
                "message": "Spotlight Banner Successfully Updated.",
                "redirect": "true",
                "redirect_url": reverse('web:spotlight_banner', kwargs={'pk': data.pk})
            }
        else:
            message = generate_form_errors(form, formset=False)

            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": str(message)
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:

        form = SpotlightBannerForm(instance=instance)

        context = {
            "form": form,
            "title": "Edit Spotlight Banner",
            "instance": instance,
            "url": reverse('web:edit_spotlight_banner', kwargs={'pk': instance.pk}),
            "redirect": True,

        }
        return render(request, 'web/spotlight_banner/edit.html', context)


@login_required
@role_required(['superadmin'])
def delete_spotlight_banner(request, pk):
    reason = request.GET.get('reason')

    SpotlightBanner.objects.filter(pk=pk).update(
        is_deleted=True, deleted_reason=reason)

    response_data = {
        "status": "true",
        "title": "Successfully Deleted",
        "message": "Spotlight Banner Successfully Deleted.",
        "redirect": "true",
        "redirect_url": reverse('web:spotlight_banners')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')
