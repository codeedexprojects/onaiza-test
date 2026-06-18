import sys

import datetime
import traceback

from api.v1.general.functions import generate_serializer_errors, get_user_token, is_pincode_exists, get_pincode
from api.v1.users.functions import *
from api.v1.users.serializers import *
from customers.models import Customer, UserOtpData, Ticket, CustomerAddress
from django.contrib.auth.models import User, Group
from django.db.models import Q, Max
from general.models import Batch
from main.functions import get_auto_id, sendSMS
from offers.models import VoucherCode
from orders.models import *
from products.models import ProductVariant
from rest_framework import status
from rest_framework.decorators import (api_view, permission_classes, renderer_classes)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from users.models import Wishlistitem
from web.models import ProductReturn
from web.functions import check_stock_availability



@api_view(['POST'])
@permission_classes((AllowAny,))
@renderer_classes((JSONRenderer,))
def send_otp(request):
    data = request.data
    phone = data['phone']
    new_otp = get_otp()

    response_data = {}

    if UserOtpData.objects.filter(phone=phone).exists():
        UserOtpData.objects.filter(phone=phone).update(otp=new_otp)

    else:
        UserOtpData.objects.create(
            phone=phone,
            name=phone,
            otp=new_otp,
        )

    message = f"Dear customer, {new_otp} is your OTP from ONAIZA. Don't share your OTP with anyone."
    msg = sendSMS('otp', phone, [new_otp])

    print('\n\n-------------', new_otp, '-------------\n\n')

    user_data = {
        "otp": new_otp,
        "phone": phone
    }

    response_data = {
        "StatusCode": 6000,
        "data": user_data,
        "message": "OTP Send Sucessfully"
    }
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((AllowAny,))
@renderer_classes((JSONRenderer,))
def verify_otp(request):
    data = request.data
    phone = data['phone']
    otp = data['otp']
    is_new_customer = True
    user_token = None

    response_data = {}

    user_data = {
        "otp": otp,
        "phone": phone
    }

    if UserOtpData.objects.filter(phone=phone, otp=otp).exists():

        # check if it is a new customer
        if Customer.objects.filter(phone=phone).exists():
            is_new_customer = False
            user_token = get_user_token(request, phone, phone)
            customer_instance = Customer.objects.get(phone=phone)

            if customer_instance.image:
                image_url = customer_instance.image.url
                user_data = {
                    "phone": phone,
                    "name": customer_instance.name,
                    "image": request.build_absolute_uri(image_url),
                }
            else:
                user_data = {
                    "phone": phone,
                    "name": customer_instance.name,
                    "image": None,
                }
            response_data = {
                "StatusCode": 6000,
                "data": user_data,
                "is_new": is_new_customer,
                "token": user_token.json(),
                "message": "OTP Verified"
            }

        if is_new_customer:
            response_data = {
                "StatusCode": 6000,
                "data": user_data,
                "is_new": is_new_customer,
                "message": "OTP Verified"
            }
    else:
        response_data = {
            "StatusCode": 6001,
            "message": "Invalid OTP"
        }
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((AllowAny,))
@renderer_classes((JSONRenderer,))
def create_customer(request):
    serialized = CustomerRegisterSerializer(data=request.data, context={"request": request})

    response_data = {}

    if serialized.is_valid():
        name = serialized.validated_data['name']
        phone = serialized.validated_data['phone']

        data = User.objects.create_user(
            username=phone,
            password=phone,
            is_active=True,
        )

        if Group.objects.filter(name="customer_user").exists():
            group = Group.objects.get(name="customer_user")
        else:
            group = Group.objects.create(name="customer_user")

        data.groups.add(group)

        uploaded_file_url = None
        if 'image' in request.FILES:
            uploaded_file_url = request.data["image"]

        auto_id = get_auto_id(Customer)

        serialized.save(
            auto_id = auto_id,
            customer_type = 'b2c',
            user = data,
            creator = data,
            updater = data,
            image = uploaded_file_url,
        )

        UserOtpData.objects.filter(phone=phone).update(
            password=encrypt_message(phone)
        )

        response = get_user_token(request, phone, phone)

        response_data = {
            "StatusCode": 6000,
            "data": serialized.data,
            "token": response.json(),
            "message": "Successfully Registered"
        }

    else:
        response_data = {
            "StatusCode": 6001,
            "message": generate_serializer_errors(serialized._errors)
        }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def add_or_remove_from_wishlist(request, pk):
    product_pk = pk
    product_variant = ProductVariant.objects.get(pk=product_pk)
    customer = Customer.objects.get(user=request.user)

    response_data = {}

    if Wishlistitem.objects.filter(product_variant_id=product_pk, customer__user=request.user).exists():
        instance = Wishlistitem.objects.filter(product_variant_id=product_pk, customer__user=request.user)
        instance.delete()

        response_data = {
            "StatusCode": 6000,
            "message": "removed"
        }
    else:
        Wishlistitem.objects.create(
            product_variant=product_variant,
            customer=customer
        )

        response_data = {
            "StatusCode": 6000,
            "message": "added"
        }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def view_wishlist(request):
    instances = Wishlistitem.objects.filter(customer__user=request.user)

    serialized = WishlistSerializer(instances, context={"request": request}, many=True)

    response_data = {
        "StatusCode": 6000,
        "data": serialized.data,
    }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def add_address(request):
    serialized = CustomerAddressSerializer(data=request.data)

    is_default = None
    response_data = {}

    if serialized.is_valid():
        isTrue = serialized.validated_data['is_default']
        customer = request.user

        user = Customer.objects.get(phone=customer)
        is_default = CustomerAddress.objects.filter(customer=user)

        if is_default and isTrue == True:
            CustomerAddress.objects.filter(customer=user).update(is_default=False)

        serialized.save(
            customer=user
        )

        response_data = {
            "StatusCode": 6000,
            "message": serialized.data,
        }

    else:
        response_data = {
            "StatusCode": 6001,
            "message": generate_serializer_errors(serialized._errors)
        }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def view_address(request):
    instances = CustomerAddress.objects.filter(customer__user=request.user, is_deleted=False)
    serialized = CustomerAddressSerializer(instances, many=True, context={"request": request})

    response_data = {
        "StatusCode": 6000,
        "data": serialized.data
    }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def set_default_address(request, pk):
    user = request.user
    response_data = {}
    instances = None

    if CustomerAddress.objects.filter(customer__user=user, is_deleted=False).exists():
        CustomerAddress.objects.filter(is_default=True, customer__user=user, is_deleted=False).update(is_default=False)
        instances = CustomerAddress.objects.filter(pk=pk).update(is_default=True)

        response_data = {
            "StatusCode": 6000,
            "message": "Updated Sucessfully"
        }

    else:
        response_data = {
            "StatusCode": 6001,
            "data": "not found"
        }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def get_default_address(request):
    instances = None

    if CustomerAddress.objects.filter(customer__user=request.user, is_deleted=False, is_default=True):
        instances = CustomerAddress.objects.get(customer__user=request.user, is_deleted=False, is_default=True)

        if instances:
            serialized = CustomerAddressSerializer(instances, context={"request": request})

            response_data = {
                "StatusCode": 6000,
                "data": serialized.data
            }
    else:
        response_data = {
            "StatusCode": 6001,
            "message": "No Default Address Found"
        }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST', "PUT"])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def update_address(request, view_type, pk):
    user = request.user
    instances = None
    response_data = {}

    if CustomerAddress.objects.filter(pk=pk).exists():
        instance = CustomerAddress.objects.get(pk=pk)

        if request.method == "PUT":
            serialized = CustomerAddressSerializer(instance, data=request.data, context={'request': request}, partial=True)

            if serialized.is_valid():
                data = serialized.save(
                    is_default=True
                )

                CustomerAddress.objects.filter(customer__user=user).exclude(pk=pk).update(is_default=False)

                response_data = {
                    "StatusCode": 6000,
                    "message": "Address successfully updated"
                }
            else:
                response_data = {
                    "StatusCode": 6001,
                    'data': {
                        "title": "Validation error",
                        "message": generate_serializer_errors(serialized._errors)
                    }
                }
        else:
            CustomerAddress.objects.filter(pk=pk).update(is_deleted=True)

            response_data = {
                "StatusCode": 6000,
                "message": "Deleted Sucessfully"
            }

    else:
        response_data = {
            "StatusCode": 6001,
            "data": "Something Went Wrong !"
        }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def cart(request):
    try:
        today = datetime.datetime.now()

        cart_item_price = get_cart_item_price(request)
        wallet = get_privliged_points(request)
        grand_total = get_grand_total(cart_item_price, request)

        coupon_session_amt = request.session.get('coupon_amt', 0)
        wallet_session_amt = request.session.get('wallet', 0)

        applied_amount_in_cash = wallet["applied_value_to_cash"]

        cart_instances = CartItem.objects.filter(customer__user=request.user, is_deleted=False)
        voucher_instances = VoucherCode.objects.filter(is_deleted=False, start_time__lte=today, end_time__gte=today, minimum_order_amount__gte=0)

        serialized = CartItemSerializer(cart_instances, many=True, context={"request": request})
        voucher_serialized = VoucherSerializer(voucher_instances, many=True, context={"request": request})

        response_data = {
            "StatusCode": 6000,
            "cart_data": serialized.data,
            "gift_voucher_data": voucher_serialized.data,
            "wallet_data": wallet,
            "item_price": str(cart_item_price),
            "delivery_charge": "22",
            "tax": "11",
            "gift_voucher": str(f"-{coupon_session_amt}"),
            "wallet_amt": str(applied_amount_in_cash),
            "grand_total": str(grand_total),
        }

    except Exception as e:
        print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
        response_data = {
            "StatusCode": 6001,
            "message": "Something Went Wrong!",
            "error": str(e),
            "error_line": str(['Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e])
        }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def add_to_cart(request):
    product_variant = request.data.get('product_variant')
    pincode = None

    product_instance = ProductVariant.objects.get(pk=product_variant)
    customer = get_user(request.user)

    response_data = {}
    cart_items = CartItem.objects.filter(customer=customer, is_deleted=False)

    if not cart_items.filter(product_variant=product_variant).exists():
        if is_pincode_exists(request):
            pincode = get_pincode(request)
            location = Location.objects.filter(pincode = pincode).first()
            warehouse = Warehouse.objects.filter(location=location)

            is_ok = True

            if cart_items.exists():
                if not cart_items.filter(warehouse__in=warehouse).exists():
                    is_ok = False

            # check the product is avail in selected pincode
            if is_ok and Batch.objects.filter(product_variant=product_variant, warehouse__in=warehouse).exists():
                batch_instance = Batch.objects.filter(product_variant=product_variant, warehouse__in=warehouse).order_by('-date_added').first()

                # check for stock
                if batch_instance.stock != 0:
                    cart_instances = CartItem.objects.create(
                        product_variant=product_instance,
                        customer=customer,
                        warehouse=warehouse.first(),
                    )

                    response_data = {
                        "StatusCode": 6000,
                        "data": "Product added to cart"
                    }
                else:
                    response_data = {
                        "StatusCode": 6001,
                        "data": "Out Of Stock"
                    }

            elif is_ok == False:
                response_data = {
                    "StatusCode": 6001,
                    "status": "different-location",
                    "data": f"Since you are adding {product_instance} from different location either you can remove current items in your cart and add the current product or you can check out your current cart items with {cart_items.count()} item(s) and proceed to add {product_instance} to your cart"
                }
            else:
                response_data = {
                    "StatusCode": 6001,
                    "data": "Product is not available in your location"
                }

        else:
            response_data = {
                "StatusCode": 6001,
                "data": "Please Confirm Your Location"
            }
    else:
        response_data = {
            "StatusCode": 6001,
            "data": "Product Alredy in cart"
        }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def cart_increment(request, pk):
    response_data = {}

    try:
        cart_instances = CartItem.objects.get(pk=pk)
        product_variant = cart_instances.product_variant

        pincode = None
        if is_pincode_exists(request):
            pincode = get_pincode(request)

        if Batch.objects.filter(product_variant=product_variant, warehouse__location__pincode=pincode).exists():
            batch_instance = Batch.objects.filter(product_variant=product_variant, warehouse__location__pincode=pincode).order_by('-date_added').first()

            old_qty = cart_instances.qty
            new_qty = old_qty + 1

            batch_qty = batch_instance.stock
            new_batch_qty = batch_qty - new_qty

            if new_batch_qty <= 0:
                response_data = {
                    "StatusCode": 6001,
                    "message": "Stock Exceeded"
                }
            else:

                cart_instances.qty = new_qty
                cart_instances.save()
                response_data = {
                    "StatusCode": 6000,
                    "message": "Added",
                    "data": str(new_qty)
                }
        else:
            response_data = {
                "StatusCode": 6001,
                "message": "Product Not avail in your area"
            }

    except Exception as e:
        response_data = {
            "StatusCode": 6001,
            "message": str(e)
        }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def cart_decrement(request, pk):
    response_data = {}

    try:
        cart_instances = CartItem.objects.get(pk=pk)
        product_variant = cart_instances.product_variant

        pincode = None
        if is_pincode_exists(request):
            pincode = get_pincode(request)

        if Batch.objects.filter(product_variant=product_variant, warehouse__location__pincode=pincode).exists():
            batch_instance = Batch.objects.filter(product_variant=product_variant, warehouse__location__pincode=pincode).order_by('-date_added').first()

            old_qty = cart_instances.qty
            new_qty = old_qty - 1

            if new_qty == 0:
                cart_instances.delete()

                response_data = {
                    "StatusCode": 6000,
                    "message": "Product removed from Cart"
                }
            else:

                cart_instances.qty = new_qty
                cart_instances.save()
                response_data = {
                    "StatusCode": 6000,
                    "message": "Reduced",
                    "data": str(new_qty)
                }
        else:
            response_data = {
                "StatusCode": 6001,
                "message": "Product Not avail in your area"
            }

    except Exception as e:
        response_data = {
            "StatusCode": 6001,
            "message": str(e)
        }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def cart_remove(request, pk):
    response_data = {}

    try:
        cart_instances = CartItem.objects.filter(pk=pk)
        if cart_instances.exists():
            cart_instances.delete()

        if CartItem.objects.filter(is_deleted=False, customer__user=request.user).count() == 0:
            if 'coupon_amt' in request.session:
                del request.session['coupon_amt']
            if 'wallet' in request.session:
                del request.session['wallet']
            if 'coupon_id' in request.session:
                del request.session['coupon_id']

            response_data = {
                "StatusCode": 6000,
                "message": "Product Removed From Cart",
            }
        else:
            response_data = {
                "StatusCode": 6000,
                "message": "Item Not Found !",
            }

    except Exception as e:
        response_data = {
            "StatusCode": 6001,
            "message": str(e)
        }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def cart_remove_all(request):

    response_data = {}
    try:
        cart_instances = CartItem.objects.filter(customer__user=request.user)
        print(cart_instances.count())
        if cart_instances.count() > 0:
            for i in cart_instances:
                print("deleting user of ==>>",request.user)
                i.delete()

        if CartItem.objects.filter(is_deleted=False).count() == 0:
            if 'coupon_amt' in request.session:
                del request.session['coupon_amt']
            if 'wallet' in request.session:
                del request.session['wallet']
            if 'coupon_id' in request.session:
                del request.session['coupon_id']

        response_data = {
            "StatusCode": 6000,
            "message": "Cart Cleared !",
        }

    except Exception as e:
        response_data = {
            "StatusCode": 6001,
            "message": str(e)
        }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def apply_coupon(request, pk):
    response_data = {}
    try:
        # if any coupon exists clear existing and replace new one
        if request.session.get('coupon_amt', ''):
            request.session['coupon_id'] = None
            request.session['coupon_amt'] = None

        if VoucherCode.objects.filter(pk=pk).exists():
            voucher_code_instance = VoucherCode.objects.get(pk=pk)

            # store the coupon id for checking cart
            code_pk = voucher_code_instance.pk
            request.session['coupon_id'] = str(code_pk)

            # store the percent amount to session
            cart_item_price = get_cart_item_price(request)
            percent_amt = cart_item_price * voucher_code_instance.percentage / 100
            limit_percent_amt = cart_item_price * voucher_code_instance.upto_limit / 100


            if percent_amt > limit_percent_amt:
                diff_amt = cart_item_price - limit_percent_amt
                stored_amt = limit_percent_amt
            else:
                diff_amt = cart_item_price - percent_amt
                stored_amt = percent_amt

            request.session['coupon_amt'] = str(round(stored_amt, 2))

            response_data = {
                "StatusCode": 6000,
                "message": "Coupon Applied Successfully",
            }

        else:
            response_data = {
                "StatusCode": 6001,
                "message": "Invalid Voucher Code",
            }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        response_data = {
            "StatusCode": 6001,
            "message": "Something went wrong",
            "error": str(traceback.format_exc()),
        }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def view_profile(request):
    response_data = {}

    try:
        instances = Customer.objects.get(user=request.user)
        serialized = CustomerSerializer(instances, context={"request": request})

        response_data = {
            "StatusCode": 6000,
            "data": serialized.data,
        }

    except Exception as e:
        response_data = {
            "StatusCode": 6001,
            "message": "Something went wrong",
            "error": str(e),
        }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def update_profile(request):
    response_data = {}

    try:
        serialized = CustomerProfileUpdateSerializer(data=request.data)
        instances = Customer.objects.get(user=request.user)

        if instances:
            if serialized.is_valid():
                serialized.update(instances, serialized.data)

                response = {
                    "profile_datas": serialized.data,
                    "profile_image": None,
                }

                if 'image' in request.FILES:
                    uploaded_file_url = request.data["image"]
                    instances.image = uploaded_file_url
                    instances.save()

                    image_url = instances.image.url
                    response = {
                        "profile_datas": serialized.data,
                        "profile_image": request.build_absolute_uri(image_url),
                    }

                response_data = {
                    "StatusCode": 6000,
                    "data": response,
                    "message": "Sucessfully Updated"
                }

            else:
                response_data = {
                    "StatusCode": 6001,
                    "message": "Data Breach",
                }
        else:
            response_data = {
                "StatusCode": 6001,
                "message": "Something went wrong, Customer not found",
            }

    except Exception as e:
        response_data = {
            "StatusCode": 6001,
            "message": "Something went wrong",
            "error": str(e),
        }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def apply_wallet_amount(request):
    response_data = {}

    # if True:
    try:

        if 'wallet' in request.session:
            request.session['wallet'] = None

        customer_instance = Customer.objects.get(user=request.user)

        # points = request.POST.get('points')
        points = request.data.get('points')
        if not points:
            points = 0

        wallet = get_privliged_points(request)

        available_points = wallet['available_points']
        wallet_balance = wallet['wallet_balance']
        wallet_point = wallet['points']
        # conversion of entered points in cash
        entered_points_cash_value = float(points) * float(wallet_point)

        if points > available_points:
            print("Points==>",points)
            print("Available Points", available_points)
            response_data = {
                "StatusCode": 6001,
                "available_points": available_points,
                "message": "Not enough points in Wallet"
            }
            return Response(response_data, status=status.HTTP_200_OK)

        cart_item_price = get_cart_item_price(request)

        if entered_points_cash_value > cart_item_price:
            response_data = {
                "StatusCode": 6001,
                "message": "Wallet amount greater than cart item price"
            }
            return Response(response_data, status=status.HTTP_200_OK)

        difference_amt = float(wallet_balance) - float(cart_item_price)
        request.session['wallet'] = str(points)

        # if difference_amt > 0:
        #     request.session['wallet'] = str(cart_item_price)
        #     customer_instance.current_privilege_points = difference_amt
        #     customer_instance.save()
        # else:
        #     customer_instance.current_privilege_points = 0
        #     request.session['wallet'] = str(wallet_balance)
        #     customer_instance.save()

        response_data = {
            "StatusCode": 6000,
            "value": str(entered_points_cash_value),
            "message": "Wallet Balance Applied Successfully"
        }

    except Exception as e:
        response_data = {
            "StatusCode": 6001,
            "message": "Something went wrong",
            "error": str(e),
        }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def checkout(request):
    response_data = {}

    try:
        address_instances = None
        address_serialized = None

        cart_item_price = get_cart_item_price(request)
        grand_total = get_grand_total(cart_item_price, request)

        coupon_session_amt = request.session.get('coupon_amt', 0)
        wallet_session_amt = request.session.get('wallet', 0)

        if CustomerAddress.objects.filter(customer__user=request.user, is_deleted=False, is_default=True):
            address_instances = CustomerAddress.objects.get(customer__user=request.user, is_deleted=False, is_default=True)

            if address_instances:
                address_serialized = CustomerAddressSerializer(address_instances, context={"request": request})

        response_data = {
            "StatusCode": 6000,
            "address": address_serialized.data,
            "item_price": str(cart_item_price),
            "delivery_charge": "22",
            "tax": "11",
            "git_voucher": str(f"-{coupon_session_amt}"),
            "wallet_amt": str(wallet_session_amt),
            "grand_total": str(grand_total),
        }
    except Exception as e:
        response_data = {
            "StatusCode": 6001,
            "message": "Something went wrong",
            "error": str(e),
        }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def payment(request):
    """
    place order, wallet amt processing, order id generation and clear cart are done by this function
    :param request:
    :return:
    """
    response_data = {}
    try:
        serialized = OrderSerializer(data=request.data)

        if serialized.is_valid():
            stock_ok, stock_data = check_stock_availability(request)

            if stock_ok:
                warehouse_id = stock_data
                user = request.user

                pincodes_of_warehouse = Warehouse.objects.get(id=warehouse_id).location.all()

                customer_instance = Customer.objects.get(user=user)
                address_instance = CustomerAddress.objects.get(customer__user=user, is_default=True, is_deleted=False)

                if address_instance.pincode in pincodes_of_warehouse:
                    auto_id = get_auto_id(Orders)

                    cart_item_price = get_cart_item_price(request)
                    grand_total = get_grand_total(cart_item_price, request)

                    order_id = get_order_prefix()
                    order_no = 0
                    prefix = None

                    if InvoicePrefix.objects.filter(is_active=True, is_deleted=False, financial_year__is_active=True).exists():
                        prefix = InvoicePrefix.objects.filter(is_active=True, is_deleted=False, financial_year__is_active=True).first()
                        pr_orders = Orders.objects.filter(prefix=prefix)

                        if pr_orders.filter(prefix=prefix).exists():
                            order_no = pr_orders.filter(prefix=prefix).aggregate(Max('order_no'))['order_no__max']

                        order_no += 1
                        order_id = f"{prefix.order}{str(order_no).zfill(6)}"

                    # reduce the used amount and update to the new amount in current privileges in customer model
                    if 'wallet' in request.session:
                        wallet_point_in_session = request.session['wallet']

                        current_privilege_point = customer_instance.current_privilege_points
                        new_privilege_point = int(current_privilege_point) - int(wallet_point_in_session)

                        customer_instance.current_privilege_points = new_privilege_point

                        customer_instance.save()

                    # save to order model
                    serialized.save(
                        customer=customer_instance,
                        warehouse_id = warehouse_id,
                        auto_id=auto_id,
                        creator=user,
                        updater=user,

                        billing_name=address_instance.name,
                        billing_phone=address_instance.phone,
                        billing_address=address_instance.house_name,
                        billing_street=address_instance.street,
                        billing_landmark=address_instance.landmark,
                        billing_city=address_instance.city,
                        billing_state=address_instance.state,
                        total_amt=grand_total,
                        payment_status="10",
                        order_status="10",
                        order_id = order_id,
                        order_no = order_no,
                        prefix = prefix
                    )

                    order = Orders.objects.get(auto_id=auto_id)
                    clear_cart(customer_instance, order, request)

                    # message = f"Dear ONAIZA customer, your order {order_id} is placed and expected delivered by {order.delivery_date}."
                    msg = sendSMS('placed', customer_instance.phone, [order_id, str(order.delivery_date)])
                    print('\n\n-------------', msg, '-------------\n\n')

                    response_data = {
                        "StatusCode": 6000,
                        "data": {
                            "auto_id": auto_id,
                            "order_id": order_id,
                        }
                    }

                else:
                    response_data = {
                        "StatusCode": 6001,
                        "message": "The selected address's pincode doesn't match with the pincode of the products in your cart."
                    }

            else:
                response_data = {
                    "StatusCode": 6001,
                    "message": stock_data
                }
        else:
            response_data = {
                "StatusCode": 6001,
                "message": generate_serializer_errors(serialized._errors)
            }

    except Exception as e:
        response_data = {
            "StatusCode": 6001,
            "message": "Something went wrong",
            "error": str(e),
        }
        print(str(e))

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def orders(request):
    query = request.GET.get('query').replace('/', '')

    instances = OrderItem.objects.filter(is_deleted=False, order__customer__user=request.user)

    if query == '10':
        instances = instances.filter(order__order_status=query)

    if query == '30':
        instances = instances.filter(order__order_status=query)

    if query == '40':
        instances = instances.filter(order__order_status=query)

    serialized = OrderItemSerializer(instances, context={"request": request}, many=True)

    response_data = {
        "StatusCode": 6000,
        "data": serialized.data
    }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def order_cancel(request, pk):
    response_data = {}

    try:
        if Orders.objects.filter(pk=pk).exists():
            order_instance = Orders.objects.get(pk=pk)
            order_instance.order_status = '40'
            order_instance.save()
            response_data = {
                "StatusCode": 6000,
                "message": "Order Cancelled Sucessfully",
            }
        else:
            response_data = {
                "StatusCode": 6001,
                "message": "Order with associcating id is not available",
            }
    except Exception as e:
        response_data = {
            "StatusCode": 6001,
            "message": "Something went wrong",
            "error": str(e),
        }
        print(str(e))

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def book_now(request, pk):
    response_data = {}
    try:
        if ProductVariant.objects.filter(pk=pk, is_deleted=False).exists():
            product_instance = ProductVariant.objects.get(pk=pk, is_deleted=False)

            if Booking.objects.filter(product_variant=product_instance, customer__user=request.user,
                                      status='pending').exists():
                response_data = {
                    "StatusCode": 6001,
                    "message": "Product Already Booked & Still waiting for approval",
                }
            else:
                Booking.objects.create(
                    product_variant=product_instance,
                    customer=get_user(request.user),
                    message="",
                    status='pending',
                )

                response_data = {
                    "StatusCode": 6000,
                    "message": "Booked Successfully",
                }
        else:
            response_data = {
                "StatusCode": 6001,
                "message": "Product Not Found",
            }
    except Exception as e:
        response_data = {
            "StatusCode": 6001,
            "message": "Something went wrong",
            "error": str(e),
        }
        print(str(e))

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def bookings(request):
    query = request.GET.get('query').replace('/', '')

    instances = Booking.objects.filter(customer__user=request.user)

    if query == 'pending':
        instances = instances.filter(status='pending')

    if query == 'approved':
        instances = instances.filter(status='approved')

    serialized = BookingSerializer(instances, context={"request": request}, many=True)

    response_data = {
        "StatusCode": 6000,
        "data": serialized.data
    }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def new_issue(request):
    response_data = {}

    try:
        serialized = TicketPostSerializer(data=request.data)
        if serialized.is_valid():
            serialized.save(
                auto_id=get_auto_id(Ticket),
                creator=request.user,
                updater=request.user,
                customer=get_user(request.user),
                status="pending",
            )

            response_data = {
                "StatusCode": 6000,
                "data": serialized.data,
                "message": "Issue Posted Successfully !",
            }
        else:
            response_data = {
                "StatusCode": 6001,
                "message": generate_serializer_errors(serialized._errors)
            }

    except Exception as e:
        response_data = {
            "StatusCode": 6001,
            "message": "Something went wrong",
            "error": str(e),
        }
        print(str(e))

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def active_issue(request):
    instances = Ticket.objects.filter(customer__user=request.user, status__in=["pending", "in_progress"])

    serialized = TicketsViewSerializer(instances, context={"request": request}, many=True)

    response_data = {
        "StatusCode": 6000,
        "data": serialized.data
    }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def resolved_issue(request):
    instances = Ticket.objects.filter(customer__user=request.user, status="solved")

    serialized = TicketsViewSerializer(instances, context={"request": request}, many=True)

    response_data = {
        "StatusCode": 6000,
        "data": serialized.data
    }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def ratings(request):
    query = request.GET.get('query').replace('/', '')

    variant_instance = OrderItem.objects.filter(is_deleted=False, order__customer__user=request.user)
    rated_instance = ProductReview.objects.filter(is_deleted=False, creator=request.user)

    # check for ratings models
    variant_pk = []
    for v in variant_instance:
        if ProductReview.objects.filter(product_variant=v.product_variant, creator=request.user):
            variant_pk.append(v.product_variant.pk)

    # test purpose
    all_order = OrderItem.objects.filter(is_deleted=False, order__customer__user=request.user)
    completes_orders = OrderItem.objects.filter(order__customer__user=request.user, order__order_status="30")
    unrated = OrderItem.objects.filter(order__customer__user=request.user, order__order_status="30").exclude(product_variant__pk__in=variant_pk)
    rated = ProductReview.objects.filter(creator=request.user, )
    instances = OrderItem.objects.filter(order__customer__user=request.user, order__order_status="30").exclude(product_variant__pk__in=variant_pk)

    if query:
        if query == 'rated':
            instances = OrderItem.objects.filter(order__customer__user=request.user, order__order_status="30",
                                                 product_variant__pk__in=variant_pk)

        if query == 'unrated':
            instances = OrderItem.objects.filter(order__customer__user=request.user, order__order_status="30").exclude(
                product_variant__pk__in=variant_pk)

    serialized = OrderItemRatingSerializer(instances, context={"request": request}, many=True)

    response_data = {
        "StatusCode": 6000,
        "data": serialized.data
    }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def post_ratings(request):
    response_data = {}
    try:
        product_pk = request.data['product_pk']
        order_pk = request.data['order_pk']

        product_rating = request.data['product_rating']
        delivery_rating = request.data['delivery_rating']
        review = request.data['review']

        if product_pk:
            product_variant_instance = ProductVariant.objects.get(pk=product_pk)

            if review:
                ProductReview.objects.create(
                    product_variant=product_variant_instance,
                    rating=product_rating,
                    creator=request.user,
                    updater=request.user,
                    auto_id=get_auto_id(ProductReview),
                    review=review,
                )
            else:
                ProductReview.objects.create(
                    product_variant=product_variant_instance,
                    rating=product_rating,
                    creator=request.user,
                    updater=request.user,
                    auto_id=get_auto_id(ProductReview)
                )

            update_current_rating(product_variant_instance)

        if order_pk:
            order = Orders.objects.get(pk=order_pk)

            DeliveryRating.objects.create(
                order=order,
                customer=get_user(request.user),
                delivery_agent=order.delivery_agent,
                rating=delivery_rating,
            )

        response_data = {
            "StatusCode": 6000,
            "message": "Rated Successfully",
        }

    except Exception as e:
        response_data = {
            "StatusCode": 6001,
            "message": "Something went wrong",
            "error": str(e),
        }
        print(str(e))

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def get_time_slots(request):
    date = request.GET.get('delivery_date')
    response_data = {}

    if date:
        today = datetime.datetime.now()

        date = date.replace('/', '')
        date_format = datetime.datetime.strptime(date, "%d-%m-%Y")

        week_number = date_format.isoweekday()
        timeslot_instances = TimeSlot.objects.filter(is_deleted=False, day=week_number)

        if date_format == today.date():
            timeslot_instances = timeslot_instances.filter(
                Q(start_time__gte=today.time()),
                Q(start_time__lte=today.time(), end_time__gte=today.time()),
            )

        if date_format.date() == today.date():
            timeslot_instances = timeslot_instances.filter(start_time__gt=today.time())

        timeslot_serialized = TimeSlotSerializer(timeslot_instances, many=True, context={"request": request})

        response_data = {
            "StatusCode": 6000,
            "data": timeslot_serialized.data
        }

    else:
        response_data = {
            "StatusCode": 6000,
            "message": "Please input date"
        }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def product_return(request):
    response_data = {}

    try:
        data = request.data
        product_variant = data['product_variant']
        order_id = data['order_id']
        reason_for_return = data['reason_for_return']
        return_specification = data['return_specification']

        customer = request.user

        order_item_instances = OrderItem.objects.filter(product_variant__pk=product_variant, order__pk=order_id)

        if order_item_instances.exists():
            order_item_instances = order_item_instances.get(product_variant__pk=product_variant, order__pk=order_id)
            order_instances = Orders.objects.get(pk=order_id)
            product_variant = order_item_instances.product_variant

            eligibility = is_eligible_for_return(product_variant.pk, order_id)

            if eligibility:
                if return_specification != '':
                    ProductReturn.objects.create(
                        auto_id=get_auto_id(ProductReturn),
                        creator=request.user,
                        updater=request.user,
                        order_item=order_item_instances,
                        order=order_instances,
                        reason_for_return=reason_for_return,
                        return_specification=return_specification,
                    )
                else:
                    ProductReturn.objects.create(
                        auto_id=get_auto_id(ProductReturn),
                        creator=request.user,
                        updater=request.user,
                        order_item=order_item_instances,
                        order=order_instances,
                        reason_for_return=reason_for_return,
                    )
                response_data = {
                    "StatusCode": 6000,
                    "message": "Product Return Request Sucessfully"
                }
            else:
                response_data = {
                    "StatusCode": 6001,
                    "message": "Product Return Period Was Over"
                }
        else:
            response_data = {
                "StatusCode": 600,
                "message": "Order Or Product Not Available"
            }

    except Exception as e:
        response_data = {
            "StatusCode": 6001,
            "message": str(e),
        }

    return Response(response_data, status=status.HTTP_200_OK)
