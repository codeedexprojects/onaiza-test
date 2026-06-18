# standard libraries
import json
import datetime
from decimal import Decimal
# third party libraries
from dal import autocomplete
# django libraries
from django.shortcuts import render, get_object_or_404
from django.http.response import HttpResponseRedirect, HttpResponse, JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_GET
from django.db.models import Sum, Q
from django.db.models.functions import Lower
from django.contrib.auth.models import Group
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.utils import timezone
# local libraries
from main.functions import generate_form_errors, get_auto_id, sendSMS
from main.decorators import role_required
from main.functions import get_current_role
from onaiza import settings
from finance.models import AccountHead
from finance.models import ReceiptVoucher, PaymentVoucher
from orders.models import Orders
from sales.models import Sale
from products.models import Product
from customers.models import Customer, CustomerAddress, UserOtpData, PrivilegePoint, Ticket
from customers.forms import *
from users.models import NotificationSubject, Notification

from main.utils.export_to_excel import ExportToExcelUtils

from api.v1.users.serializers import CustomerExportSerializer

from general.functions import render_to_pdf
from main.decorators import ajax_required

from customers.utils.instances_manager import InstancesManager


class CustomerAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        items = Customer.objects.filter(is_deleted=False).order_by('name', 'auto_id')
        sale_type = self.forwarded.get('sale_type', None)
        if sale_type:
            items = items.filter(customer_type=sale_type)
        if self.q:
            items = items.filter(Q(auto_id__iexact=self.q) | Q(name__icontains=self.q) | Q(address__icontains=self.q) | Q(phone__istartswith=self.q))

        return items


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def create(request):
    code = "onaiza"

    if request.method == "POST":
        form = CustomerForm(request.POST)

        if form.is_valid():
            phone = form.cleaned_data['phone']
            opening_type = form.cleaned_data['opening_type']
            opening_balance = form.cleaned_data['opening_balance']
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            username = str(code) + str(phone)
            password = phone

            data = form.save(commit=False)
            data.creator = request.user
            data.updater = request.user
            data.auto_id = get_auto_id(Customer)
            current_balance = 0
            if opening_type == 'debit':
                current_balance += opening_balance
            elif opening_type == 'credit':
                current_balance -= opening_balance
            data.current_balance = current_balance
            data.save()

            response_data = {"status": "true", "title": "Successfully Created",
                             "message": " Customer Created successfully.", "redirect": "true",
                             "redirect_url": reverse('customers:customer', kwargs={"pk": data.pk})}

        else:
            message = generate_form_errors(form, formset=False)
            response_data = {'status': 'false', 'stable': 'true', 'title': "Form validation error",
                             "message": str(message)}

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:

        form = CustomerForm()
        context = {"form": form, "title": "Create Customer", "redirect": True, "url": reverse("customers:create"), }
        return render(request, 'customers/entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def edit(request, pk):
    instance = get_object_or_404(Customer.objects.filter(pk=pk))
    current_balance = instance.current_balance
    old_opening_balance = instance.opening_balance
    if instance.opening_type == 'debit':
        current_balance -= old_opening_balance
    elif instance.opening_type == 'credit':
        current_balance += old_opening_balance

    if request.method == "POST":
        form = CustomerForm(request.POST, instance=instance)

        if form.is_valid():
            data = form.save(commit=False)
            data.updater = request.user
            data.date_updated = datetime.datetime.now()
            opening_type = form.cleaned_data['opening_type']
            opening_balance = form.cleaned_data['opening_balance']
            if opening_type == 'debit':
                current_balance += opening_balance
            elif opening_type == 'credit':
                current_balance -= opening_balance
            data.current_balance = current_balance
            data.save()

            response_data = {"status": "true", "title": "Successfully Updated",
                             "message": "Customer Successfully Updated.", "redirect": 'true',
                             "redirect_url": reverse('customers:customers')
                             # "redirect_url": reverse('customers:customer', kwargs={"pk": data.pk})
                             }
        else:
            message = generate_form_errors(form, formset=False)

            response_data = {"status": "false", "stable": "true", "title": "Form validation error", "message": message}

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        form = CustomerForm(instance=instance)
        context = {"form": form, "title": "Create Customer", "redirect": True,
                   "url": reverse("customers:edit", kwargs={"pk": instance.pk}), }
        return render(request, 'customers/entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def customers(request):
    instances = Customer.objects.filter(is_deleted=False)

    query = request.GET.get('q')
    view = request.GET.get('view')
    sort_by = request.GET.get('sort_by')
    order_by = request.GET.get('order_by')

    if not order_by:
        order_by = 'desc'

    if sort_by == 'id' or not sort_by:
        sort_by = 'auto_id'

    if view == 'online':
        instances = instances.filter(user__isnull=False)
    elif view == 'offline':
        instances = instances.filter(user__isnull=True)
    else:
        view = 'all'

    if query:
        instances = instances.filter(
            Q(name__icontains=query) | Q(phone__icontains=query) | Q(email__icontains=query) | Q(
                address__icontains=query))

    if sort_by == 'auto_id':
        if order_by == 'asc':
            instances = instances.order_by('auto_id')

    else:
        if order_by == 'desc':
            instances = instances.order_by(Lower(sort_by).desc())
        else:
            instances = instances.order_by(Lower(sort_by))

    filter_data = {'view': view, 'query': query, 'sort_by': sort_by, 'order_by': order_by, }

    context = {"title": "Customers", "instances": instances, "filter_data": filter_data, }

    return render(request, 'customers/customers.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def customer(request, pk):
    instance = get_object_or_404(Customer.objects.filter(pk=pk))
    sale_instances = Sale.objects.filter(customer=instance, is_deleted=False).order_by('-id')[:10]
    order_instances = Orders.objects.filter(customer=instance, is_deleted=False).order_by('-id')[:10]
    receipt_instances = ReceiptVoucher.objects.filter(sub_ledger=instance.pk, is_deleted=False).order_by('-id')[:10]
    payment_instances = PaymentVoucher.objects.filter(sub_ledger=instance.pk, is_deleted=False).order_by('-id')[:10]

    date = datetime.datetime.now().date()

    context = {"instance": instance, "title": "Customer : " + instance.name, "sale_instances": sale_instances,
               "order_instances": order_instances, "receipt_instances": receipt_instances,
               "payment_instances": payment_instances, }

    return render(request, 'customers/customer.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete(request, pk):
    instance = get_object_or_404(Customer.objects.filter(pk=pk, is_deleted=False))
    instance.is_deleted = True
    user = instance.user
    reason = request.GET.get('reason')
    instance.deleted_reason = reason
    instance.save()

    response_data = {"status": "true", "title": "Successfully Deleted", "message": "Customer Successfully Deleted.",
                     "redirect": "true", "redirect_url": reverse('customers:customers')}
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


def get_customer(request):
    pk = request.GET.get('id')
    if pk:
        if Customer.objects.filter(pk=pk).exists():
            customer = Customer.objects.get(pk=pk)
            debit = 0
            credit = 0
            if customer.opening_type == "debit":
                debit = customer.opening_balance
                credit = 0
            if customer.opening_type == "credit":
                credit = customer.opening_balance
                debit = 0

            current_balance = customer.current_balance
            current_privilege_points = customer.current_privilege_points
            privilege_points = customer.privilege_points

            instance = PrivilegePoint.objects.filter(is_deleted=False).first()

            response_data = {"status": 'true', "credit": str(credit), "debit": str(debit), "state": str(customer.state),
                "address": str(customer.address), "current_balance": str(current_balance),
                "minimum_amount": str(instance.minimum_amount), "privilege_points": str(privilege_points),
                "value_of_point": str(instance.value_of_point),
                "current_privilege_points": str(current_privilege_points), }
        else:
            response_data = {"status": "false", "message": "Customer is not exists."}
    else:
        response_data = {"status": "false", "message": "Customer is not exists."}
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def revoke_access(request, pk):
    instance = get_object_or_404(Customer.objects.filter(pk=pk, is_deleted=False))

    User.objects.filter(pk=instance.user.pk).update(
        username=instance.user.username + "_deleted" + str(instance.user.id), email=instance.user.email + "_deleted",
        is_active=False)

    # unset user
    Customer.objects.filter(pk=pk).update(user=None)

    response_data = {"status": "true", "title": "Access Revoked.", "message": "Access Revoked Successfully.",
                     "redirect": "true", "redirect_url": reverse('customers:customer', kwargs={'pk': pk})}

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
def get_customers(request):
    data = []
    if Customer.objects.filter(is_deleted=False).exists():
        instances = Customer.objects.filter(is_deleted=False).order_by('name')

        for i in instances:
            name = i.name
            if i.address:
                name += ' - ' + i.address
            obj = {'name': name, 'pk': str(i.pk)}
            data.append(obj)

        response_data = {"status": "true", "instances": data, "model": 'Customer', }
    else:
        response_data = {"status": "true", "message": "No Customers found."}

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def create_privilege_point(request):
    instance = PrivilegePoint.objects.filter(is_deleted=False).last()

    if request.method == 'POST':
        if instance:
            form = PrivilegePointForm(request.POST, instance=instance)
        else:
            form = PrivilegePointForm(request.POST)

        if form.is_valid():
            # create Privilege Point
            data = form.save(commit=False)
            data.updater = request.user

            if not instance:
                data.creator = request.user
                data.auto_id = get_auto_id(PrivilegePoint)
            else:
                data.date_updated = datetime.datetime.now()

            data.save()

            response_data = {"status": "true", "title": "Successfully Created",
                             "message": "Privilege Point Created Successfully.", "redirect": "true",
                             "redirect_url": reverse('customers:privilege_point')}

        else:
            message = generate_form_errors(form, formset=False)

            response_data = {"status": "false", "stable": "true", "title": "Form validatruetion error",
                             "message": str(message)}
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        if instance:
            form = PrivilegePointForm(instance=instance)
        else:
            form = PrivilegePointForm()
        context = {"title": "Create Privilege Point", "form": form, "stable": "true",
                   "url": reverse('customers:create_privilege_point'), }

        return render(request, 'customers/privilege_point/privilege_point_entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def privilege_point(request):
    instance = PrivilegePoint.objects.filter(is_deleted=False).last()

    if not instance:
        return HttpResponseRedirect(reverse('customers:create_privilege_point'))

    context = {"instance": instance, "title": "Privilege Point : " + str(instance.value_of_point),
               "single_page": True, }

    return render(request, 'customers/privilege_point/privilege_point.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_privilege_point(request, pk):
    reason = request.GET.get('reason')
    instance = get_object_or_404(PrivilegePoint.objects.filter(pk=pk, is_deleted=False))

    PrivilegePoint.objects.filter(pk=pk).update(is_deleted=True, deleted_reason=reason)

    response_data = {"status": "true", "title": "Successfully Deleted",
                     "message": "PrivilegePoint Successfully Deleted.", "redirect": "true",
                     "redirect_url": reverse('customers:create_privilege_point')}

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
def get_balance(request):
    pk = request.GET.get('id')
    instance = Customer.objects.get(pk=pk, is_deleted=False)
    # balance = get_vender_balance(instance.pk)

    head = AccountHead.objects.filter(name='Sundry Debtor', is_deleted=False).last()
    today = datetime.datetime.now().date()

    if instance:
        response_data = {"status": "true", 'current_balance': float(instance.current_balance), }
    else:
        response_data = {"status": "false", "message": "Vendor not found"}

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin'])
def pending_tickets(request):
    instances = Ticket.objects.filter(is_deleted=False, status="pending")

    context = {"instances": instances, "title": "Pending Tickets", }

    return render(request, 'customers/tickets/tickets.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def mark_as_pending(request, pk):
    instance = get_object_or_404(Ticket.objects.filter(pk=pk, is_deleted=False))
    instance.status = 'in_progress'
    instance.date_updated = datetime.datetime.now()
    instance.save()

    notification_subject,created = NotificationSubject.objects.get_or_create(code='ticket_status_updated',defaults={'name':'Ticket status updated'})
    message = "Your ticket on progress."
    user = instance.customer.user
    Notification.objects.create(
        is_active = True,
        subject = notification_subject,
        user = user,
        message = message,
        time = datetime.datetime.now(),
        customer = instance.customer,

    )

    response_data = {"status": "true", "title": "Successfully Updated",
                     "message": "Ticket Successfully Mark as pending.", "redirect": "true",
                     "redirect_url": reverse('customers:customers')}
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin'])
def in_progress_tickets(request):
    instances = Ticket.objects.filter(is_deleted=False, status="in_progress")

    context = {"instances": instances, "title": "In Progress Tickets", }

    return render(request, 'customers/tickets/tickets.html', context)


@login_required
def reject_ticket(request, pk):
    instance = get_object_or_404(Ticket.objects.filter(pk=pk))
    if request.method == "POST":
        form = TicketRejectForm(request.POST, instance=instance)
        if form.is_valid():
            data = form.save(commit=False)
            data.date_updated = datetime.datetime.now()
            data.status = "rejected"
            data.save()
            pk = data.pk

            notification_subject,created = NotificationSubject.objects.get_or_create(code='ticket_status_updated',defaults={'name':'Ticket status updated'})
            message = "Your ticket is rejected."
            user = instance.customer.user
            Notification.objects.create(
                is_active = True,
                subject = notification_subject,
                user = user,
                message = message,
                time = datetime.datetime.now(),
                customer = instance.customer,

            )

            return JsonResponse({"status": "true", 'error': False, 'title': "Rejected",
                                 'message': 'Rejected Reason Updated Successfully', "redirect": 'true',
                                 "redirect_url": reverse('customers:in_progress_tickets')})

        else:

            return JsonResponse({'error': True, 'errors': form, })

    else:
        form = TicketRejectForm()
        context = {"form": form, "title": "Rejected Reason", "redirect": True,
                   "url": reverse("customers:reject_ticket", kwargs={"pk": pk}), }

        return render(request, 'customers/tickets/reject_entry.html', context)


@login_required
def mark_as_solved_ticket(request, pk):
    instance = get_object_or_404(Ticket.objects.filter(pk=pk))
    if request.method == "POST":
        form = TicketResolvedForm(request.POST, instance=instance)
        if form.is_valid():
            data = form.save(commit=False)
            data.date_updated = datetime.datetime.now()
            data.status = "solved"
            data.save()
            pk = data.pk

            notification_subject,created = NotificationSubject.objects.get_or_create(code='ticket_status_updated',defaults={'name':'Ticket status updated'})
            message = "Your ticket is solved."
            user = instance.customer.user
            Notification.objects.create(
                is_active = True,
                subject = notification_subject,
                user = user,
                message = message,
                time = datetime.datetime.now(),
                customer = instance.customer,

            )

            return JsonResponse({"status": "true", 'error': False, 'title': "Sucessfully Updated",
                                 'message': 'Description Updated Successfully', "redirect": 'true',
                                 "redirect_url": reverse('customers:in_progress_tickets')})

        else:

            return JsonResponse({'error': True, 'errors': form, })

    else:
        form = TicketResolvedForm()
        context = {"form": form, "title": "Resolved Reason", "redirect": True,
                   "url": reverse("customers:mark_as_solved_ticket", kwargs={"pk": pk}), }

        return render(request, 'customers/tickets/solved_entry.html', context)


@login_required
@role_required(['superadmin'])
def rejected_tickets(request):
    instances = Ticket.objects.filter(is_deleted=False, status="rejected")

    context = {"instances": instances, "title": "Rejected Tickets", }

    return render(request, 'customers/tickets/tickets.html', context)


@login_required
@role_required(['superadmin'])
def solved_tickets(request):
    instances = Ticket.objects.filter(is_deleted=False, status="solved")

    context = {"instances": instances, "title": "Solved Tickets", }

    return render(request, 'customers/tickets/tickets.html', context)


@login_required
def export_to_excel(request):
    customer_instances = Customer.objects.filter(is_deleted=False)
    export_to_excel_utils = ExportToExcelUtils(customer_instances, CustomerExportSerializer, request, "customer")
    returned_file_url = export_to_excel_utils.export_to_excel()
    return HttpResponseRedirect(returned_file_url)


def customer_to_pdf(request):
    """
    customer to pdf
    :param request:
    """
    instances_manager = InstancesManager(request)
    instances = instances_manager.get_instances_depend_on_params()
    print(instances)
    context = {"sample": "loo", "instances": instances }

    return render_to_pdf('customers/customer_pdf.html', context)
