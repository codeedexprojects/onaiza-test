import math
from datetime import datetime

from api.v1.delivery_agent.delivery_agent_utils import DeliveryAgentUtils
from api.v1.general.functions import generate_serializer_errors, get_user_token
from api.v1.delivery_agent.functions import calculate_distance, get_cash_in_hand, get_delivery_agent
from api.v1.delivery_agent.serializers import *
from delivery_agent.models import *
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Case, When, IntegerField, Value
from main.functions import get_auto_id, sendSMS
from rest_framework import status
from rest_framework.decorators import (api_view, permission_classes, renderer_classes)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from users.models import Notification
from vendors.models import VendorCommission
from web.models import ProductReturn


@api_view(['POST'])
@permission_classes((AllowAny,))
@renderer_classes((JSONRenderer,))
def login_agent(request):
    response_data = {}

    try:
        data = request.data
        phone = data['phone']
        password = data['password']

        if not phone and password:
            response_data = {"StatusCode": 6001, "message": "Phone and password must not be empty", }
        else:
            if User.objects.filter(username=phone).exists():
                instance = User.objects.get(username=phone)
                user_token = get_user_token(request, phone, password)
                response_data = {"StatusCode": 6000, "token": user_token.json(), }
            else:
                response_data = {"StatusCode": 6001, "message": "Phone or password error"}

    except Exception as e:
        response_data = {"StatusCode": 6001, "message": "Something Went Wrong !", "error": str(e), }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def get_orders(request):
    try:
        query = request.GET.get('query')

        # getting orders assigned to me
        instances = Orders.objects.filter(is_deleted=False, delivery_agent__user=request.user)

        # order by undecided first, then accepted lastly rejected
        instances = instances.annotate(ordering=Sum(Case(
            When(delivery_agent_is_accept=False, then=Value(2)),
            When(delivery_agent_is_accept=True, then=Value(1)),
            default = Value(0),
            output_field = IntegerField()
        ))).order_by("ordering")

        if query == 'pending':
            instances = instances.filter(order_status="10", delivery_agent_is_accept=True)

        elif query == 'delivered':
            instances = instances.filter(order_status="30", delivery_agent_is_accept=True)

        elif query == 'cancelled':
            instances = instances.filter(order_status="40", delivery_agent_is_accept=True)

        elif query == 'accepted':
            instances = instances.filter(delivery_agent_is_accept=True)

        elif query == 'declined':
            instances = instances.filter(delivery_agent_is_accept=False)

        serialized = OrderSerializer(instances, context={"request": request}, many=True)

        response_data = {"StatusCode": 6000, "order_data": serialized.data}

    except Exception as e:
        response_data = {"StatusCode": 6001, "error": str(e)}

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def accept_or_reject_order(request, pk):
    """
    accept or reject the order by delivery boy
    :param request:
    :param pk:
    """
    response_data = {}
    try:
        agent_status = request.data['status']
        reason = None
        reason_text = None

        if 'reason' and 'reason_text' in request.data:
            reason = request.data['reason']
            reason_text = request.data['reason_text']

        # get the single order
        instance = Orders.objects.get(pk=pk)

        # check the order status
        if 'accept' in agent_status:
            instance.delivery_agent_is_accept = True
            instance.save()

            latitude = request.data['latitude']
            longitude = request.data['longitude']

            DeliveryAgentTravel.objects.create(order=instance, origin_latitude=latitude, origin_longitude=longitude,
                                               delivery_agent=instance.delivery_agent, )

            response_data = {"StatusCode": 6000, "message": "Order Accepted"}

        elif 'reject' in agent_status:
            if reason and reason_text:
                # saving rejection statues
                instance.delivery_agent_is_accept = False
                instance.delivery_agent_declined_reason = reason
                instance.delivery_agent_declined_reason_text = reason_text
                instance.save()
                response_data = {"StatusCode": 6000, "message": "Order Rejected !"}

            else:
                response_data = {"StatusCode": 6001, "message": "Reason is necessary !"}

    except Exception as e:
        response_data = {"StatusCode": 6001, "message": str(e)}

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def payment_collection(request):
    response_data = {}
    print(request.user, "<<====>>")
    try:
        serialized = PaymentCollectionSerializer(data=request.data)
        if serialized.is_valid():
            order = serialized.validated_data['order']
            delivery_agent = DeliveryAgents.objects.get(user=request.user)
            serialized.save(auto_id=get_auto_id(CollectPayment), creator=request.user, updater=request.user,
                            delivery_agent=delivery_agent, )

            Orders.objects.filter(pk=order.id).update(order_status="30", payment_status="20")

            try:
                latitude = request.data['latitude']
                longitude = request.data['longitude']

                DeliveryAgentTravel.objects.filter(order=order).update(delivery_latitude=latitude,
                                                                       delivery_longitude=longitude, )

                # DeliveryAgentTravel.objects.filter(order=order).update(pickup_latitude=latitude,
                #                                                        pickup_longitude=longitude, )
                travel_data = DeliveryAgentTravel.objects.get(order=order)

                distance_data = calculate_distance(travel_data, status='delivered')

                travel_data.delivery_distance_text = distance_data['distance_text']
                travel_data.delivery_distance = distance_data['distance']
                travel_data.save()
            except:
                print('\n\n\nError occured while calculating distance\n\n\n')

            response_data = {"StatusCode": 6000, "data": serialized.data,
                             "message": "Payment Collected Successfully !", }
        else:
            response_data = {"StatusCode": 6001, "message": generate_serializer_errors(serialized._errors)}

    except Exception as e:
        response_data = {"StatusCode": 6001, "message": "Something went wrong", "error": str(e), }
        print(str(e))

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def collected_payments(request):
    query = request.GET.get('query')

    instances = CollectPayment.objects.filter(is_deleted=False, is_transferred=False)

    if query:
        if 'transferred' in query:
            instances = instances.filter(is_transferred=True)

    serialized = PaymentCollectionSerializer(instances, context={"request": request}, many=True)

    response_data = {"StatusCode": 6000, "data": serialized.data}

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def payment_transfer(request):
    print(request.data, "=======")
    try:
        image = request.data['image']
    except:
        image = None

    payment_medium = request.data['medium']

    response_data = {}

    delivery_agent = get_delivery_agent(request.user)
    delivery_agent_utils = DeliveryAgentUtils(delivery_agent)
    if image:
        amount_to_be_transferred = delivery_agent_utils.transfer_amount(payment_medium, request.user, image=image)
    else:
        amount_to_be_transferred = delivery_agent_utils.transfer_amount(payment_medium, request.user)

    if amount_to_be_transferred['status']:
        response_data['StatusCode'] = 6000
        response_data['message'] = "Successfully paid"
    else:
        response_data['StatusCode'] = 6001
        response_data['message'] = "Nothing to paid"

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def save_location(request):
    try:
        response_data = {}
        data = request.data

        longitude = data['longitude']
        latitude = data['latitude']

        delivery_agent_instance = DeliveryAgents.objects.get(user=request.user)

        if DeliveryAgentTravel.objects.filter(delivery_agent__user=request.user).exists():
            DeliveryAgentTravel.objects.filter(delivery_agent__user=request.user).update(longitude=longitude,
                                                                                         latitude=latitude)

            response_data = {"StatusCode": 6000, "message": "Location Updated !!"}

        else:
            DeliveryAgentTravel.objects.create(delivery_agent=delivery_agent_instance, longitude=longitude,
                                               latitude=latitude)

            response_data = {"StatusCode": 6000, "message": "Location Created"}

    except Exception as e:
        response_data = {"StatusCode": 6001, "error": str(e)}

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def get_location(request):
    instance = DeliveryAgentTravel.objects.get(is_deleted=False, delivery_agent__user=request.user)

    serialized = DeliveryAgentLocationSaveSerializer(instance, context={"request": request})

    response_data = {"StatusCode": 6000, "data": serialized.data}

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def get_returns(request):
    instances = ProductReturn.objects.filter(is_deleted=False, delivery_boy__user=request.user, status="pending")

    serialized = ProductReturnSerializer(instances, context={"request": request}, many=True)

    response_data = {"StatusCode": 6000, "data": serialized.data}

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def accept_return_by_agent(request, pk):
    response_data = {}

    try:
        return_instances = ProductReturn.objects.get(pk=pk)

        return_instances.status = "delivery_boy_collected"
        return_instances.save()

        response_data = {"StatucCode": 6000, "message": "Product Collected !"}

    except Exception as e:
        response_data = {"StatusCode": 6001, "error": str(e)}

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def order(request, pk):
    """
    Single view of order
    :param request:
    :param order_pk:
    """

    response_data = {}

    try:
        order = Orders.objects.get(pk=pk)

    except Exception as e:
        response_data = {"StatusCode": 6001, "error": str(e)}

    else:
        serialized = OrderSerializer(order, context={"request": request})
        response_data = {"StatusCode": 6000, "data": serialized.data}

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def update_duty_status(request):
    """
    Update the duty status of delivery agent
    :param request:
    """

    response_data = {}

    try:
        agent = DeliveryAgents.objects.get(user=request.user)
        current_time = datetime.datetime.now()

    except Exception as e:
        response_data = {"StatusCode": 6001, "error": str(e)}

    else:
        # if agent is off duty set status to false and vice-versa
        if agent.is_active is True:
            agent.is_active = False
            agent.save()

            response_data = {"StatusCode": 6000, "message": "Duty Signed OFF"}

        else:
            agent.is_active = True
            agent.active_time = current_time
            agent.save()
            response_data = {"StatusCode": 6000, "message": "Duty Signed ON"}

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def get_duty_status(request):
    """
    get duty status of a delivery agent using logined user
    :param request:
    """
    response_data = {}
    try:
        user = request.user
        agent_instance = DeliveryAgents.objects.get(user=user)
        is_active = False

        # current time fetch
        current_time = datetime.datetime.now().replace(tzinfo=None)
        diff_in_minutes = 0

        # takes only it has active time
        if agent_instance.active_time:
            logined_time = agent_instance.active_time.replace(tzinfo=None)

            difference = current_time - logined_time

            diff_in_minutes = difference.total_seconds() / 60

    except Exception as e:
        response_data = {"StatusCode": 6001, "message": str(e)}

    else:
        if agent_instance.is_active:
            is_active = True
            response_data = {"StatusCode": 6000, "active_minutes": math.trunc(diff_in_minutes), "is_active": is_active}

        else:
            is_active = False
            response_data = {"StatusCode": 6000, "is_active": is_active, "active_minutes": "Your a off duty"}

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def update_pickup_status(request, pk):
    """
    update pick up status
    :param request:
    """
    try:
        order = Orders.objects.get(pk=pk)
        current_pickup_status = order.pickup_status

        print(current_pickup_status)

    except Exception as e:
        response_data = {"StatusCode": 6001, "message": str(e)}

    else:
        print(current_pickup_status)

        if current_pickup_status == 'reached':
            order.pickup_status = 'picked_up'
            order.save()

            msg = sendSMS('on_delivery', order.customer.phone, [order.order_id])
            print('\n\n-------------', msg, '-------------\n\n')

            try:
                latitude = request.data['latitude']
                longitude = request.data['longitude']

                DeliveryAgentTravel.objects.filter(order=order).update(pickup_latitude=latitude,
                                                                       pickup_longitude=longitude, )
                travel_data = DeliveryAgentTravel.objects.get(order=order)

                distance_data = calculate_distance(travel_data, status='picked_up')

                travel_data.pickup_distance_text = distance_data['distance_text']
                travel_data.pickup_distance = distance_data['distance']
                travel_data.save()

            except:
                print('\n\n\nError occured while calculating distance\n\n\n')

            response_data = {"StatusCode": 6000, "pick up status": "Picked Up product"}

        else:
            order.pickup_status = 'reached'
            order.save()
            response_data = {"StatusCode": 6000, "pick up status": "Reached Pick Up location"}

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def update_delivery_status(request, pk):
    """
    update delivery status
    :param pk:
    :param request:
    """
    response_data = {}

    try:
        order_status = request.data['order_status']

        order = Orders.objects.get(pk=pk)
        current_order_status = order.order_status

        order.order_status = order_status
        order.save()

        if order_status == "20":
            # message = f"Dear ONAIZA customer, your order {order.order_id} has been shipped and expected delivered by {order.delivery_date}."
            msg = sendSMS('shipped', order.customer.phone, [order.order_id, str(order.delivery_date)])
            print('\n\n-------------', msg, '-------------\n\n')

        elif order_status == "30" and not current_order_status == '30':
            # message = f"Dear ONAIZA customer, your order has been delivered on {order.delivery_date}."
            msg = sendSMS('delivered', order.customer.phone, [str(order.delivery_date)])
            print('\n\n-------------', msg, '-------------\n\n')

            for item in order.get_order_items():
                vendor = item.product_variant.product.vendor
                if vendor:
                    total_amount = item.qty * item.price
                    commission_amount = total_amount * item.product_variant.commission_percentage /100

                    VendorCommission.objects.create(
                        commission_amount =commission_amount,
                        vendor = vendor,
                        order_item = item
                    )
                    vendor.current_balance += round(commission_amount,2)
                    vendor.save()

        elif order_status == "40":
            # message = f"Dear ONAIZA customer, your order {order.order_id} has been cancelled."
            msg = sendSMS('cancelled', order.customer.phone, [order.order_id])
            print('\n\n-------------', msg, '-------------\n\n')

        # if message:
        #     msg = sendSMS(order.customer.phone, message)
        #     print('\n\n-------------', msg, '-------------\n\n')

        response_data = {"StatusCode": 6000, "data": order.order_status}

    except Exception as e:
        response_data = {"StatusCode": 6001, "message": str(e)}

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def dashboard(request):
    """
    view to fetch the activities and details of particaular agent
    :param request:
    :return:
    """
    response_data = {}

    try:
        # get ratings
        my_rating_sum = DeliveryRating.objects.filter(delivery_agent__user=request.user).aggregate(Sum('rating'))
        my_rating_count = DeliveryRating.objects.filter(delivery_agent__user=request.user).count()
        my_rating = my_rating_sum['rating__sum']

        if my_rating_sum == 0:
            rating_percent = my_rating / my_rating_count
        else:
            rating_percent = 0

        total_declined_orders = Orders.objects.filter(delivery_agent__user=request.user, delivery_agent_is_accept=False).count()

        total_cancelled_orders = Orders.objects.filter(delivery_agent__user=request.user, order_status="40").count()

        delivered_orders = Orders.objects.filter(order_status="30", delivery_agent__user=request.user, payment_status="20")
        total_delivered_orders = delivered_orders.count()

        # calculate distance travelled for delivered orders
        travel_data = DeliveryAgentTravel.objects.filter(order__in=delivered_orders).aggregate(
            count = Count('id'),
            pickup = Sum('pickup_distance'),
            delivery = Sum('delivery_distance')
        )

        total_pickup_distance = travel_data.get('pickup') or 0
        total_delivery_distance = travel_data.get('delivery') or 0
        print(total_pickup_distance)
        print(total_delivery_distance)

        distance_covered = total_pickup_distance + total_delivery_distance
        # end of distance calculation

        total_cash_in_hand = get_cash_in_hand(request)
        print(total_cash_in_hand,"===================")

        total_activity = {"distance_covered": distance_covered, "orders_delivered": total_delivered_orders,
                          "orders_declined": total_declined_orders, "cash_details": total_cash_in_hand,
                          "my_rating": '{0:.1f}'.format(rating_percent), "rating_customers_count": my_rating_count,
                          "total_cancelled_orders": total_cancelled_orders, }

    except Exception as e:
        response_data = {"StatusCode": 6001, "message": str(e)}

    else:
        response_data = {"StatusCode": 6000, "total_activity": total_activity, }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def notifications(request):
    """
    fetching the notifications of delivery agents like user rating postings etccc
    :param request:
    :return:
    """
    response_data = {}

    try:
        notifications_unread = Notification.objects.filter(who=request.user, is_deleted=False, is_read=False)
        notifications_read = Notification.objects.filter(who=request.user, is_deleted=False, is_read=True)

        unread_serialized = NotificationSerializer(notifications_unread, context={"request": request}, many=True)
        read_serialized = NotificationSerializer(notifications_read, context={"request": request}, many=True)

    except Exception as e:

        response_data = {"StatusCode": 6001, "message": str(e)}
    else:
        response_data = {"StatusCode": 6000, "unread_notifications": unread_serialized.data,
                         "read_notifications": read_serialized.data}

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def mark_as_read(request, pk):
    response_data = {}

    try:
        notification = Notification.objects.get(pk=pk)
        notification.is_read = True
        notification.save()

        response_data = {"StatusCode": 6000, "message": "Notification Mark as Read"}

    except Exception as e:
        response_data = {"StatusCode": 6001, "message": str(e)}

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def view_profile(request):
    try:

        instances = DeliveryAgents.objects.get(user=request.user)

        serialized = DeliveryAgentSerializer(instances, context={"request": request})

        response_data = {"StatusCode": 6000, "data": serialized.data}

    except Exception as e:
        response_data = {"StatusCode": 6001, "error": str(e)}

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def update_profile(request):
    response_data = {}
    try:
        instance = DeliveryAgents.objects.get(user=request.user)

        if 'image' in request.FILES:
            uploaded_file_url = request.data["image"]
            instance.image = uploaded_file_url
            instance.save()

        image_url = instance.image.url
        response = request.build_absolute_uri(image_url),

        response_data = {"StatusCode": 6001, "data": response}

    except Exception as e:
        pass
    else:
        pass

    return Response(response_data, status=status.HTTP_200_OK)
