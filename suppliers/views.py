# Standard libraries
import json
import datetime
from datetime import date, time
# third party libraries
from dal import autocomplete
# django libraries
from django.shortcuts import render, get_object_or_404
from django.http.response import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.db.models import Q
from django.db.models.functions import Lower
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.conf import settings
# Local libraries
from main.functions import get_auto_id, generate_form_errors
from main.decorators import ajax_required, role_required
from main.forms import UserForm
from finance.models import AccountHead
from finance.models import PaymentVoucher, ReceiptVoucher
from purchases.models import Purchase
from suppliers.forms import SupplierForm, SupplierCreateFromForm
from suppliers.models import Supplier
from finance.models import FinancialYear


class SupplierAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        supplier = Supplier.objects.filter(is_deleted=False)

        if self.q:
            supplier = supplier.filter(Q(name__istartswith=self.q))

        return supplier


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def supplier_from_create(request):
    if request.method == 'POST':
        form = SupplierCreateFromForm(request.POST)

        if form.is_valid():
            name = form.cleaned_data['name']
            opening_type = form.cleaned_data['opening_type']
            opening_balance = form.cleaned_data['opening_balance']
            opening_type = form.cleaned_data['opening_type']
            opening_balance = form.cleaned_data['opening_balance']
            is_ok = True

            if is_ok:
                auto_id = get_auto_id(Supplier)
                name = name.title()

                data = form.save(commit=False)
                data.auto_id = auto_id
                data.opening_type = opening_type
                data.opening_balance = opening_balance
                data.name = name
                data.creator = request.user
                data.updater = request.user
                current_balance = 0
                if opening_type == 'debit':
                    current_balance += opening_balance
                elif opening_type == 'credit':
                    current_balance -= opening_balance
                data.current_balance = current_balance
                data.save()

                response_data = {
                    "status": "true",
                    "title": "Successfully Created",
                    "message": "Supplier created successfully.",
                    "redirect": "true",
                    "redirect_url": reverse('purchases:create_new_purchase')
                }
            else:
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": "Opening Debit and Opening Credit can't be positive at the same time."
                }

        else:
            message = generate_form_errors(form, formset=False)
            print(form.errors)
            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": str(message)
            }
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def create_supplier(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)

        if form.is_valid():
            name = form.cleaned_data['name']
            opening_type = form.cleaned_data['opening_type']
            opening_balance = form.cleaned_data['opening_balance']
            is_ok = True

            if is_ok:
                auto_id = get_auto_id(Supplier)
                name = name.title()

                data = form.save(commit=False)
                data.auto_id = auto_id
                data.opening_type = opening_type
                data.opening_balance = opening_balance
                data.name = name
                data.creator = request.user
                data.updater = request.user
                current_balance = 0
                if opening_type == 'debit':
                    current_balance += opening_balance
                elif opening_type == 'credit':
                    current_balance -= opening_balance
                data.current_balance = current_balance
                data.save()

                response_data = {
                    "status": "true",
                    "title": "Successfully Created",
                    "message": "Supplier created successfully.",
                    "redirect": "true",
                    "redirect_url": reverse('suppliers:suppliers')
                }
            else:
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": "Opening Debit and Opening Credit can't be positive at the same time."
                }

        else:
            message = generate_form_errors(form, formset=False)
            print(form.errors)
            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": str(message)
            }
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        form = SupplierForm()

        context = {
            "title": "Create Supplier",
            "form": form,
            "redirect": "true",
            "url": reverse('suppliers:create_supplier'),
        }

        return render(request, 'supplier/entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def suppliers(request):
    instances = Supplier.objects.filter(
        is_deleted=False).order_by(Lower('name'))

    query = request.GET.get("q")
    sort_by = request.GET.get('sort_by')
    order_by = request.GET.get('order_by')

    instances = instances.annotate(
        lower_name=Lower('name'),
        lower_email=Lower('email'),
        lower_phone=Lower('phone'),
        lower_address=Lower('address')
    )

    if not order_by:
        order_by = 'asc'

    if not sort_by:
        sort_by = 'name'

    if sort_by == 'id':
        sort_by = 'auto_id'
        if order_by == 'asc':
            instances = instances.order_by('auto_id')
        else:
            instances = instances.order_by('-auto_id')

    elif sort_by == 'name':
        if order_by != 'asc':
            instances = instances.order_by('-lower_name')

    elif sort_by == 'email':
        if order_by == 'asc':
            instances = instances.order_by('lower_email')
        else:
            instances = instances.order_by('-lower_email')

    elif sort_by == 'phone':
        if order_by == 'asc':
            instances = instances.order_by('lower_phone')
        else:
            instances = instances.order_by('-lower_phone')

    elif sort_by == 'address':
        if order_by == 'asc':
            instances = instances.order_by('lower_address')
        else:
            instances = instances.order_by('-lower_address')

    if query:
        instances = instances.filter(
            Q(name__icontains=query) |
            Q(address__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query)
        )

    filter_data = {
        'query': query,
        'sort_by': sort_by,
        'order_by': order_by,
    }

    context = {
        "title": 'suppliers',
        'instances': instances,
        'filter_data': filter_data,
    }
    return render(request, 'supplier/suppliers.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def edit_supplier(request, pk):
    instance = get_object_or_404(
        Supplier.objects.filter(pk=pk, is_deleted=False))
    current_balance = instance.current_balance
    old_opening_balance = instance.opening_balance
    if instance.opening_type == 'debit':
        current_balance -= old_opening_balance
    elif instance.opening_type == 'credit':
        current_balance += old_opening_balance

    if request.method == "POST":
        form = SupplierForm(request.POST, instance=instance)

        if form.is_valid():
            # update Supplier
            name = form.cleaned_data['name']
            opening_type = form.cleaned_data['opening_type']
            opening_balance = form.cleaned_data['opening_balance']
            name = name.title()
            is_ok = True

            if is_ok:
                data = form.save(commit=False)
                data.name = name
                data.updater = request.user
                data.date_updated = datetime.datetime.now()
                if opening_type == 'debit':
                    current_balance += opening_balance
                elif opening_type == 'credit':
                    current_balance -= opening_balance
                data.current_balance = current_balance
                data.save()

                response_data = {
                    "status": "true",
                    "title": "Successfully Updated",
                    "message": "Supplier updated successfully.",
                    "redirect": "true",
                    "redirect_url": reverse('suppliers:suppliers')
                }

            else:
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": "Opening Debit and Opening Credit can't be positive at the same time."
                }
        else:
            message = generate_form_errors(form, formset=False)

            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        form = SupplierForm(instance=instance)

        context = {
            "form": form,
            "redirect": "true",
            "instance": instance,
            "title": "Edit Supplier :" + instance.name,
            "url": reverse('suppliers:edit_supplier', kwargs={'pk': instance.pk}),
        }

        return render(request, 'supplier/entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def supplier(request, pk):
    instance = get_object_or_404(
        Supplier.objects.filter(pk=pk, is_deleted=False))
    purchase_instances = Purchase.objects.filter(supplier=instance,is_deleted=False).order_by('-id')[:10]
    receipt_instances = ReceiptVoucher.objects.filter(sub_ledger=instance.pk,is_deleted=False).order_by('-id')[:10]
    payment_instances = PaymentVoucher.objects.filter(sub_ledger=instance.pk,is_deleted=False).order_by('-id')[:10]
    
    context = {
        'title': 'Supplier',
        'instance': instance,
        "purchase_instances":purchase_instances,
        "receipt_instances":receipt_instances,
        "payment_instances":payment_instances,
    }

    return render(request, "supplier/supplier.html", context)


@login_required
@ajax_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_supplier(request, pk):
    reason = request.GET.get('reason')
    Supplier.objects.filter(pk=pk).update(is_deleted=True,deleted_reason=reason)

    response_data = {
        "status": "true",
        "title": "Successfully Deleted",
        "message": "Supplier deleted successfully.",
        "redirect": "true",
        "redirect_url": reverse('suppliers:suppliers')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@ajax_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_selected_suppliers(request):
    pks = request.GET.get('pk')

    if pks:
        pks = pks[:-1]
        pks = pks.split(',')

        for pk in pks:
            instance = get_object_or_404(
                Supplier.objects.filter(pk=pk, is_deleted=False))
            Supplier.objects.filter(pk=pk).update(
                is_deleted=True, name=instance.name + "_deleted_" + str(instance.auto_id))

        response_data = {
            "status": "true",
            "title": "Successfully Deleted",
            "message": "Selected Supplier Successfully Deleted.",
            "redirect": "true",
            "redirect_url": reverse('suppliers:suppliers')
        }
    else:

        response_data = {
            "status": "false",
            "title": "Nothing selected",
            "message": "Please select some items first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@ajax_required
@login_required
def get_suppliers(request):
    data = []
    if Supplier.objects.filter(is_deleted=False,).exists():
        instances = Supplier.objects.filter(is_deleted=False,).order_by(
            'name').values_list('name', 'pk')

        for i in instances:
            obj = {
                'name': i[0],
                'pk': str(i[1])
            }
            data.append(obj)

        response_data = {
            "status": "true",
            "model": 'Supplier',
            "instances": data
        }
    else:
        response_data = {
            "status": "false",
            "message": "No suppliers found"
        }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


def get_supplier_data(request):
    pk = request.GET.get('id')

    if Supplier.objects.filter(pk=pk, is_deleted=False,).exists():
        supplier = Supplier.objects.get(pk=pk)
        state = supplier.state

        response_data = {
            "status": 'true',
            "state": str(state),

        }
    else:
        response_data = {
            "status": "false",
            "message": "Supplier is not exists."
        }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')



@login_required
def get_balance(request):
    pk = request.GET.get('id')
    instance = Supplier.objects.get(pk=pk, is_deleted=False)
    # balance = get_vender_balance(instance.pk)

    head = AccountHead.objects.filter(name='Sundry Creditor (Vendor)', is_deleted=False).last()
    today = datetime.datetime.now().date()

    if instance:
        response_data = {
            "status": "true",
            'current_balance': float(instance.current_balance),
        }
    else:
        response_data = {
            "status": "false",
            "message": "Vendor not found"
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')
