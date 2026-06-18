# Local libraries
from main.decorators import role_required
from main.functions import generate_form_errors, get_auto_id, get_a_id, get_date_updated_request, get_otp, sendSMS
from delivery_agent.models import DeliveryAgents
from general.models import InvoiceDesign
from customers.models import CustomerAddress
from finance.models import AccountHead, InvoicePrefix
from orders.forms import *
from orders.models import *
from web.functions import get_order_prefix
from web.models import ProductReturn
from staffs.models import Staff
from users.models import NotificationSubject, Notification
# Django libriries
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Max
from django.urls import reverse
from django.views.decorators.http import require_GET
from django.shortcuts import render, get_object_or_404
from django.http.response import HttpResponse, JsonResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.forms.models import inlineformset_factory
from django.forms.formsets import formset_factory
# Standard libraries
import json
import datetime


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def create_time_slot(request):
    TimeslotTimeFormset = formset_factory(TimeslotTimeForm, extra=1)

    if request.method == 'POST':
        form = TimeslotForm(request.POST)
        time_slot_formset = TimeslotTimeFormset(request.POST, prefix='time_slot_formset')

        if form.is_valid() and time_slot_formset.is_valid():
            day = form.cleaned_data["day"]

            for form_item in time_slot_formset:
                start_time = form_item.cleaned_data["start_time"]
                end_time = form_item.cleaned_data["end_time"]

                auto_id = get_auto_id(TimeSlot)

                # create time-slot
                TimeSlot.objects.create(
                    creator = request.user,
                    updater = request.user,
                    auto_id = auto_id,

                    day = day,
                    end_time = end_time,
                    start_time = start_time,
                )

            response_data = {
                "status": "true",
                "title": "Successfully Created",
                "message": "Time Slot Created Successfully.",
                "redirect": "true",
                "redirect_url": reverse('orders:time_slot', kwargs={'pk': day})
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
        form = TimeslotDayForm()
        time_slot_formset = TimeslotTimeFormset(prefix='time_slot_formset')

        context = {
            "form": form,
            "title": "Create TimeSlot ",
            "time_slot_formset": time_slot_formset,
            "url": reverse('orders:create_time_slot'),
        }

        return render(request, 'orders/timeslot/timeslot_entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def time_slots(request):
    instances = TimeSlot.objects.filter(is_deleted=False)
    days = []

    for item in DAY_CHOICES:
        days.append({
            "pk": item[0],
            "name": item[1],
            "count": instances.filter(day=item[0]).count()
        })

    context = {
        "title": "Time Slots",
        "days": days,
    }

    return render(request, 'orders/timeslot/timeslots.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def edit_time_slot(request, pk):
    instance = get_object_or_404(TimeSlot.objects.filter(pk=pk, is_deleted=False))

    if request.method == 'POST':
        response_data = {}
        form = TimeslotForm(request.POST, instance=instance)

        if form.is_valid():
            # update offer
            data = form.save(commit=False)
            data.updater = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            response_data = {
                "status": "true",
                "title": "Successfully Updated",
                "message": "Time Slot Successfully Updated.",
                "redirect": "true",
                "redirect_url": reverse('orders:time_slot', kwargs={'pk': data.pk})
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
        form = TimeslotForm(instance=instance)

        context = {
            "form": form,
            "title": "Edit Time Slot : " + str(instance.day),
            "instance": instance,
            "url": reverse('orders:edit_time_slot', kwargs={'pk': instance.pk}),
            "redirect": True,
        }

        return render(request, 'orders/timeslot/edit_timeslot.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_time_slot(request, pk):
    reason = request.GET.get('reason')
    instance = get_object_or_404(TimeSlot.objects.filter(pk=pk, is_deleted=False))

    TimeSlot.objects.filter(pk=pk).update(is_deleted=True, deleted_reason=reason)

    response_data = {
        "status": "true",
        "title": "Successfully Deleted",
        "message": "TimeSlot Successfully Deleted.",
        "redirect": "true",
        "redirect_url": reverse('orders:time_slots')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def time_slot(request, pk):
    instances = TimeSlot.objects.filter(is_deleted=False)

    days = []
    for item in DAY_CHOICES:
        days.append({
            "pk": item[0],
            "name": item[1],
            "count": instances.filter(day=item[0]).count()
        })

    instances = instances.filter(day=pk)

    context = {
        "title": "Time Slot : ",
        "pk": pk,
        "days": days,
        "instances": instances,
    }

    return render(request, 'orders/timeslot/timeslots.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def orders(request, order_type):
    order_status_form = OrderStatusForm()
    instances = Orders.objects.filter(is_deleted=False) #, order_status="10")
    query = request.GET.get('query')

    if order_type == 'pending':
        instances = instances.filter(order_status="10")
    elif order_type == 'shipped':
        instances = instances.filter(order_status="20")
    elif order_type == 'delivered':
        instances = instances.filter(order_status="30")
    elif order_type == 'cancelled':
        instances = instances.filter(order_status="40")
    else:
        order_type = 'all'

    if query:
        if 'unassigned' in query:
            instances = instances.filter(delivery_agent__isnull=True, order_status="10")

        elif 'pending' in query:
            instances = instances.filter(order_status="10")

        elif 'assigned' in query:
            instances = instances.filter(delivery_agent__isnull=False, order_status__in=["10", "20"])

        elif 'shipped' in query:
            instances = instances.filter(is_deleted=False, order_status="20")

        elif 'completed' in query:
            instances = instances.filter(is_deleted=False, order_status="30")

        elif 'cancelled' in query:
            instances = instances.filter(is_deleted=False, order_status="40")
    else:
        query = 'all'

    context = {
        "query": query,
        "is_all_order":True,
        "instances": instances,
        "order_type": order_type,
        "order_status_form":order_status_form,
        "title": f"{order_type.title()} Orders",
    }
    return render(request, 'orders/orders/orders.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def order(request, pk):
    instance = get_object_or_404(Orders.objects.filter(pk=pk))
    items = OrderItem.objects.filter(order_id=pk)
    delivery_agent_instances = DeliveryAgents.objects.filter(is_deleted=False)

    if instance.warehouse:
        delivery_agent_instances = delivery_agent_instances.filter(warehouse_id=instance.warehouse_id)

    context = {
        "title": "Order : " + str(instance.order_id),
        "has_vendor": items.filter(product_variant__product__vendor__isnull=False).exists(),
        "instance": instance,
        "delivery_agents": delivery_agent_instances,
    }
    return render(request, 'orders/orders/order.html', context)


@role_required(['superadmin', 'warehouse_manager'])
def assign_agent(request):
    agent_pk = request.GET.get('agent')
    order_pk = request.GET.get('order')

    try:
        agent = DeliveryAgents.objects.get(pk=agent_pk)
    except:
        agent = None
        print(f"\n\n Error: Could not find agent with pk: {agent_pk}\n\n")

    order_instances = get_object_or_404(Orders.objects.filter(pk=order_pk))

    order_instances.assigned_time = datetime.datetime.now()
    order_instances.delivery_agent = agent
    order_instances.save()

    response_data = {
        "status": True,
    }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def bookings(request):
    instances = Booking.objects.filter(is_deleted=False, status="pending")

    context = {
        "title": "All Bookings",
        "instances": instances,
        "pending_order": True,
    }
    return render(request, 'orders/bookings/bookings.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def booking(request, pk):
    instance = get_object_or_404(Booking.objects.filter(pk=pk))

    context = {
        "title": "Booking : " + str(instance.order_id),
        "instance": instance,
    }
    return render(request, 'orders/bookings/booking.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def accept_booking(request, pk, address_pk):
    booking_instance = Booking.objects.get(pk=pk)
    address_instance = CustomerAddress.objects.get(pk=address_pk)

    variant = booking_instance.product_variant
    pincode = address_instance.pincode.pincode
    customer_instance = address_instance.customer

    batch = None
    if variant.product.vendor:
        pass
    elif Batch.objects.filter(is_deleted=False, warehouse__location__pincode=pincode, product_variant=variant).exists():
        batch = Batch.objects.filter(is_deleted=False, warehouse__location__pincode=pincode, product_variant=variant).first()

    else:
        response_data = {
            "status": "false",
            "title": "Batch Not Found",
            "message": "Batch Not Found on Customers preferred location",
            "redirect": "true",
            "redirect_url": reverse('orders:bookings')
        }
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    order_id = get_order_prefix()
    order_no = 0
    prefix = None

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
        customer=customer_instance,
        billing_name=address_instance.name,
        billing_phone=address_instance.phone,
        billing_address=address_instance.house_name,
        billing_street=address_instance.street,
        billing_landmark=address_instance.landmark,
        billing_city=address_instance.city,
        billing_state=address_instance.state,
        order_status=10,
        total_amt=variant.mrp,
        payment_method="cod",
        payment_status=10,
        order_no=order_no,
        order_id=order_id,
        prefix=prefix,
        warehouse=batch.warehouse,
    )

    OrderItem.objects.create(
        product_variant=variant,
        qty="1",
        price=variant.mrp,
        order=order,
        batch=batch,
    )

    booking_instance.status = "confirmed"
    booking_instance.save()

    response_data = {
        "status": "true",
        "title": "Accept Booking",
        "message": "Successfully Accepted Booking.",
        "redirect": "true",
        "redirect_url": reverse('orders:bookings')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def accepted_bookings(request):
    instances = Booking.objects.filter(is_deleted=False, status="confirmed")

    context = {
        "title": "All Bookings",
        "instances": instances,
        "accepted_order": True
    }

    return render(request, 'orders/bookings/bookings.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def returns(request):
    warehouse = request.GET.get('warehouse')
    return_status = request.GET.get('return_status')
    user_role = request.GET.get('user_role')

    is_admin = None
    if request.user.is_superuser:
        is_admin = True

    if user_role:
        if 'warehouse_manager' in user_role:
            staff_instance = Staff.objects.get(user=request.user)
            is_admin = False

    instances = ProductReturn.objects.filter(is_deleted=False, status="pending")

    warehouse_instances = Warehouse.objects.filter(is_deleted=False)

    if warehouse:
        instances = instances.filter(is_deleted=False, order_item__batch__warehouse__pk=warehouse)

    if return_status:
        instances = instances.filter(is_deleted=False, status=return_status)

    context = {
        "title": "Pending Return Requests",
        "instances": instances,
        "warehouse_instances":warehouse_instances,
        "warehouse":warehouse,
        "return_status":return_status,
        "is_admin":is_admin,
    }
    return render(request, 'orders/returns/returns.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def product_return(request, pk):
    warehouse = request.GET.get('warehouse')
    instance = get_object_or_404(ProductReturn.objects.filter(pk=pk))

    delivery_agent_instances = DeliveryAgents.objects.filter(is_deleted=False)
    if warehouse:
        delivery_agent_instances = delivery_agent_instances.filter(warehouse=warehouse)

    context = {
        "title": "Returned Product : " + str(instance.order.billing_name),
        "instance": instance,
        "delivery_agents": delivery_agent_instances,
    }
    return render(request, 'orders/returns/return.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def accept_or_reject_return(request):
    response_data = {}

    pk = request.GET.get('pk')
    status = request.GET.get('status')
    rejected_reason = request.GET.get('rejected_reason')

    product_return_instances = ProductReturn.objects.get(pk=pk)

    if 'reject' in status:
        product_return_instances.status = "rejected"
        product_return_instances.rejected_reason = rejected_reason
        product_return_instances.save()

        response_data = {
            "status": True,
            "return_status": "rejected"
        }

    elif 'accepted' in status:
        product_return_instances.status = "accepted"
        product_return_instances.save()

        response_data = {
            "status": True,
            "return_status": "accepted"
        }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@role_required(['superadmin', 'warehouse_manager'])
def assign_agent_for_return(request):
    agent_pk = request.GET.get('agent')
    return_pk = request.GET.get('return_pk')

    agent = DeliveryAgents.objects.get(pk=agent_pk)

    return_instances = get_object_or_404(ProductReturn.objects.filter(pk=return_pk))
    return_instances.delivery_boy = agent
    return_instances.save()

    response_data = {
        "status": True,
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def product_recieved(request):
    return_pk = request.GET.get('return_pk')

    return_instances = get_object_or_404(ProductReturn.objects.filter(pk=return_pk))
    return_instances.status = "onaiza_received"
    return_instances.save()

    response_data = {
        "status": True,
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'staff_user'])
def print_sale_order(request, pk):
    instance = get_object_or_404(Orders.objects.filter(pk=pk))

    invoice_design = None
    if InvoiceDesign.objects.filter(is_deleted=False,is_active=True):
        invoice_design = InvoiceDesign.objects.filter(is_deleted=False,is_active=True).first()

    order_items = OrderItem.objects.filter(order=instance)
    total_taxable_amount = 0
    total_gst_amount = 0

    total_cgst = 0
    total_sgst = 0
    total_igst = 0
    total_discount = 0

    order_items_arr = []
    for order_item in order_items:
        total_price = order_item.price
        sgst = order_item.product_variant.sgst
        cgst = order_item.product_variant.cgst
        gst_percentage = sgst + cgst
        taxable_amount = total_price / 1 +(gst_percentage/100)
        gst_amount = total_price - taxable_amount
        dic = {
            "product_name":order_item.product_variant.title,
            "qty":order_item.qty,
            "price":order_item.price,
            "gst":gst_amount,
            "taxable_amount":taxable_amount,
        }
        order_items_arr.append(dic)
        total_taxable_amount += taxable_amount
        total_gst_amount += gst_amount
    total_cgst = total_gst_amount/2
    total_sgst = total_gst_amount/2


    context = {
        "title": "Quotation ",
        "instance": instance,
        "order_items": order_items_arr,

        "total_cgst": total_cgst,
        "total_sgst": total_sgst,
        "total_igst": total_igst,
        "invoice_design": invoice_design,
    }

    return render(request, 'invoice/print_sale_order.html', context)


@login_required
@role_required(['superadmin', 'staff_user'])
def print_staff_view_order(request,view_type, pk):
    instance = get_object_or_404(Orders.objects.filter(pk=pk))
    order_items = OrderItem.objects.filter(order=instance)

    invoice_design = None
    if InvoiceDesign.objects.filter(is_deleted=False,is_active=True):
        invoice_design = InvoiceDesign.objects.filter(is_deleted=False,is_active=True).first()
        
    if view_type == "staff":
        order_items = order_items.filter(product_variant__product__vendor__isnull=True)
        
    total_taxable_amount = 0
    total_gst_amount = 0

    total_cgst = 0
    total_sgst = 0
    total_igst = 0
    total_discount = 0

    order_items_arr = []
    for order_item in order_items:
        total_price = order_item.price * order_item.qty
        batch = order_item.batch
        print(batch)
        dic = {
            "product_name": str(order_item.product_variant),
            "qty":order_item.qty,
            "price":order_item.price,
            "total_price":total_price,
            "batch":batch,
        }
        order_items_arr.append(dic)

    context = {
        "title": "Orders ",
        "instance": instance,
        "order_items": order_items_arr,

        "invoice_design": invoice_design,
    }

    return render(request, 'invoice/print_staff_view_order.html', context)


@login_required
@role_required(['superadmin', 'staff_user'])
def print_sale_order_a4(request, pk):
    instance = get_object_or_404(Orders.objects.filter(pk=pk))

    invoice_design = None
    if InvoiceDesign.objects.filter(is_deleted=False,is_active=True):
        invoice_design = InvoiceDesign.objects.filter(is_deleted=False,is_active=True).first()

    order_items = OrderItem.objects.filter(order=instance)
    total_taxable_amount = 0
    total_gst_amount = 0

    total_cgst = 0
    total_sgst = 0
    total_igst = 0
    total_discount = 0

    order_items_arr = []
    for order_item in order_items:
        total_price = order_item.price
        sgst = order_item.product_variant.sgst
        cgst = order_item.product_variant.cgst
        gst_percentage = sgst + cgst
        taxable_amount = total_price / 1 +(gst_percentage/100)
        gst_amount = total_price - taxable_amount
        dic = {
            "product_name":order_item.product_variant.title,
            "product_variant":order_item.product_variant,
            "qty":order_item.qty,
            "price":order_item.price,
            "taxable_amount":taxable_amount,
            "total_price":total_price
        }
        order_items_arr.append(dic)
        total_taxable_amount += taxable_amount
        total_gst_amount += gst_amount
    total_cgst = total_gst_amount/2
    total_sgst = total_gst_amount/2
    print(order_items_arr)

    context = {
        "title": "Quotation ",
        "instance": instance,
        "order_items": order_items_arr,

        "total_cgst": total_cgst,
        "total_sgst": total_sgst,
        "total_igst": total_igst,
        "invoice_design": invoice_design,
    }

    return render(request, 'invoice/print_order.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def change_order_status(request, pk):
    if request.method == 'POST':
        form = OrderStatusForm(request.POST)

        if form.is_valid():
            status = form.cleaned_data['order_status']
            Orders.objects.filter(pk=pk).update(order_status=status,date_updated=datetime.datetime.now())
            order = get_object_or_404(Orders, pk=pk)

            message = None
            print(order.order_id, str(order.delivery_date))
            if status == "20":
                msg = sendSMS('shipped', order.customer.phone, [order.order_id, str(order.delivery_date)])
                print('\n\n-------------', msg, '-------------\n\n')
                message = f"Dear ONAIZA customer, your order {order.order_id} has been shipped and expected delivered by {str(order.delivery_date)}."

            elif status == "30":
                msg = sendSMS('delivered', order.customer.phone, [str(order.delivery_date)])
                print('\n\n-------------', msg, '-------------\n\n')
                message = f"Dear ONAIZA customer, your order has been delivered on {str(order.delivery_date)}."

            elif status == "40":
                msg = sendSMS('cancelled', order.customer.phone, [order.order_id])
                print('\n\n-------------', msg, '-------------\n\n')
                message = f"Dear ONAIZA customer, your order {order.order_id} has been cancelled."

            Notification.objects.create(
                is_active = True,
                # subject = notification_subject,
                user = order.customer.user,
                message = message,
                time = datetime.datetime.now()
            )
            # if message:
            #     msg = sendSMS(order.customer.phone, message)
            #     print('\n\n-------------', msg, '-------------\n\n')

            response_data = {
                "status": "true",
                "title": "Successfully Updates",
                "message": "Order Status Successfully Updates.",
                "redirect": "true",
                "redirect_url": reverse('orders:order', kwargs={'pk':pk})
            }
            return HttpResponse(json.dumps(response_data), content_type='application/javascript')
