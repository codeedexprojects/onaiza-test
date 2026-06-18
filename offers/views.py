import json
import datetime
from decimal import Decimal
from itertools import chain
from operator import attrgetter, itemgetter
# Third party libraries
from ast import literal_eval
from dal import autocomplete
# Django libraries
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.http.response import HttpResponse, HttpResponseRedirect,JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from django.db.models import Q, F
from django.views.decorators.http import require_GET
from django.forms.widgets import Select, TextInput
from django.forms.formsets import formset_factory
from django.forms.models import inlineformset_factory
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.db.models import Sum
# Local libraries
from main.decorators import role_required
from main.functions import generate_form_errors, get_auto_id, get_a_id, get_date_updated_request
from users.functions import get_warehouse
from offers.models import Offers, DealOfDay, VoucherCode
from offers.forms import OffersForm, DealOfDayForm, VoucherForm
from general.models import Batch


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def create_offer(request):
    if request.method == 'POST':
        form = OffersForm(request.POST, request.FILES)

        if form.is_valid():
            auto_id = get_auto_id(Offers)
            # create offer
            data = form.save(commit=False)
            data.creator = request.user
            data.updater = request.user
            data.auto_id = auto_id

            if data.offer_type == 'product':
                data.category = None
                data.subcategory = None
            elif data.offer_type == 'category':
                data.product = None
                data.subcategory = None
            elif data.offer_type == 'sub_category':
                data.product = None
                data.category = None

            data.save()

            response_data = {
                "status": "true",
                "title": "Successfully Created",
                "message": "Offer Created Successfully.",
                "redirect": "true",
                "redirect_url": reverse('offers:offer', kwargs={'pk': data.pk})
            }

        else:
            message = generate_form_errors(form, formset=False)

            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": str(message)
            }

        return JsonResponse(response_data)

    else:
        form = OffersForm()
        context = {
            "title": "Create Offer ",
            "form": form,
            "url": reverse('offers:create_offer'),
        }

        return render(request, 'offers/offers/offer_entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def offers(request):
    instances = Offers.objects.filter(is_deleted=False)
    title = "Offers"
    query = request.GET.get("q")
    if query:
        instances = instances.filter(
            Q(auto_id__icontains=query) | Q(name__icontains=query))
        title = "Offers - %s" % query

    context = {
        "instances": instances,
        'title': title,

    }
    return render(request, 'offers/offers/offers.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def offer(request, pk):
    instance = get_object_or_404(Offers.objects.filter(pk=pk, is_deleted=False))

    context = {
        "instance": instance,
        "title": "Offer : " + instance.title,
        "single_page": True,

    }
    return render(request, 'offers/offers/offer.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def edit_offer(request, pk):
    instance = get_object_or_404(Offers.objects.filter(pk=pk, is_deleted=False))

    if request.method == 'POST':
        response_data = {}
        form = OffersForm(request.POST, request.FILES, instance=instance)

        if form.is_valid():
            # update offer
            data = form.save(commit=False)
            data.updater = request.user
            data.date_updated = datetime.datetime.now()

            if data.offer_type == 'product':
                data.category = None
                data.subcategory = None
            elif data.offer_type == 'category':
                data.product = None
                data.subcategory = None
            elif data.offer_type == 'sub_category':
                data.product = None
                data.category = None

            data.save()

            response_data = {
                "status": "true",
                "title": "Successfully Updated",
                "message": "Offer Successfully Updated.",
                "redirect": "true",
                "redirect_url": reverse('offers:offer', kwargs={'pk': data.pk})
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
        initial = {
            'start_time': datetime.datetime.strftime(instance.start_time, '%Y-%m-%d'),
            'end_time': datetime.datetime.strftime(instance.end_time, '%Y-%m-%d')
        }
        form = OffersForm(instance=instance, initial=initial)

        context = {
            "form": form,
            "title": "Edit Offer : " + instance.title,
            "instance": instance,
            # "url": reverse('offers:edit_offer', kwargs={'pk': instance.pk}),
            "redirect": True,
        }

        return render(request, 'offers/offers/offer_entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_offer(request, pk):
    reason = request.GET.get('reason')
    instance = get_object_or_404(Offers.objects.filter(pk=pk, is_deleted=False))

    Offers.objects.filter(pk=pk).update(is_deleted=True, deleted_reason=reason)

    response_data = {
        "status": "true",
        "title": "Successfully Deleted",
        "message": "Offer Successfully Deleted.",
        "redirect": "true",
        "redirect_url": reverse('offers:offers')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_selected_offers(request):
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(
                Offers.objects.filter(pk=pk, is_deleted=False))
            Offers.objects.filter(pk=pk).update(
                is_deleted=True, name=instance.name + "_deleted_" + str(instance.auto_id))

        response_data = {
            "status": "true",
            "title": "Successfully Deleted",
            "message": "Selected Offers Successfully Deleted.",
            "redirect": "true",
            "redirect_url": reverse('offers:offers')
        }
    else:
        response_data = {
            "status": "false",
            "title": "Nothing selected",
            "message": "Please select some items first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def create_dealofday(request):
    if request.method == 'POST':
        form = DealOfDayForm(request.POST)

        if form.is_valid():

            auto_id = get_auto_id(DealOfDay)

            # create DealOfDay

            data = form.save(commit=False)
            data.creator = request.user
            data.updater = request.user
            data.auto_id = auto_id

            data.save()

            response_data = {
                "status": "true",
                "title": "Successfully Created",
                "message": "DealOfDay Created Successfully.",
                "redirect": "true",
                "redirect_url": reverse('offers:dealofday', kwargs={'pk': data.pk})
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
        form = DealOfDayForm()
        context = {
            "title": "Create DealOfDay ",
            "form": form,
            "url": reverse('offers:create_dealofday'),

        }
        return render(request, 'offers/dealofdays/dealofday_entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def dealofdays(request):
    instances = DealOfDay.objects.filter(is_deleted=False)
    title = "DealOfDay"
    query = request.GET.get("q")
    if query:
        instances = instances.filter(
            Q(auto_id__icontains=query) | Q(name__icontains=query))
        title = "DealOfDay - %s" % query

    context = {
        "instances": instances,
        'title': title,

    }
    return render(request, 'offers/dealofdays/dealofdays.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def dealofday(request, pk):
    instance = get_object_or_404(
        DealOfDay.objects.filter(pk=pk, is_deleted=False))
    context = {
        "instance": instance,
        "title": "DealOfDay : " + str(instance.offer_percentage),
        "single_page": True,
    }
    return render(request, 'offers/dealofdays/dealofday.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def edit_dealofday(request, pk):
    instance = get_object_or_404(DealOfDay.objects.filter(pk=pk, is_deleted=False))

    if request.method == 'POST':
        response_data = {}
        form = DealOfDayForm(request.POST, instance=instance)

        if form.is_valid():
            # update dealofdays
            data = form.save(commit=False)
            data.updater = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            response_data = {
                "status": "true",
                "title": "Successfully Updated",
                "message": "Deal Of Day Successfully Updated.",
                "redirect": "true",
                "redirect_url": reverse('offers:dealofday', kwargs={'pk': data.pk})
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
        form = DealOfDayForm(instance=instance)

        context = {
            "form": form,
            "title": "Edit Deal Of Day : " + instance.offer_percentage,
            "instance": instance,
            "url": reverse('offers:edit_dealofday', kwargs={'pk': instance.pk}),
            "redirect": True,
        }

        return render(request, 'offers/dealofdays/dealofday_entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_dealofday(request, pk):
    reason = request.GET.get('reason')
    instance = get_object_or_404(
        DealOfDay.objects.filter(pk=pk, is_deleted=False))

    DealOfDay.objects.filter(pk=pk).update(is_deleted=True, deleted_reason=reason)

    response_data = {
        "status": "true",
        "title": "Successfully Deleted",
        "message": "DealOfDay Successfully Deleted.",
        "redirect": "true",
        "redirect_url": reverse('offers:dealofdays')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_selected_dealofdays(request):
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(
                DealOfDay.objects.filter(pk=pk, is_deleted=False))
            DealOfDay.objects.filter(pk=pk).update(
                is_deleted=True, name=instance.name + "_deleted_" + str(instance.auto_id))

        response_data = {
            "status": "true",
            "title": "Successfully Deleted",
            "message": "Selected Offers Successfully Deleted.",
            "redirect": "true",
            "redirect_url": reverse('offers:dealofdays')
        }
    else:
        response_data = {
            "status": "false",
            "title": "Nothing selected",
            "message": "Please select some items first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def create_voucher(request):
    if request.method == 'POST':
        form = VoucherForm(request.POST)

        if form.is_valid():
            auto_id = get_auto_id(VoucherCode)

            # create timeslot
            data = form.save(commit=False)
            data.creator = request.user
            data.updater = request.user
            data.auto_id = auto_id

            data.save()

            response_data = {
                "status": "true",
                "title": "Successfully Created",
                "message": "Voucher Code Created Successfully.",
                "redirect": "true",
                "redirect_url": reverse('offers:voucher', kwargs={'pk': data.pk})
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
        form = VoucherForm()
        context = {
            "title": "Create Voucher ",
            "form": form,
            "url": reverse('offers:create_voucher'),
        }

        return render(request, 'offers/voucher/voucher_entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def edit_voucher(request, pk):
    instance = get_object_or_404(
        VoucherCode.objects.filter(pk=pk, is_deleted=False))

    if request.method == 'POST':
        form = VoucherForm(request.POST, instance=instance)

        if form.is_valid():
            data = form.save(commit=False)
            data.updater = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            response_data = {
                "status": "true",
                "title": "Successfully Updated",
                "message": "Voucher Code Successfully Updated.",
                "redirect": "true",
                "redirect_url": reverse('offers:voucher', kwargs={'pk': data.pk})
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
        form = VoucherForm(instance=instance)

        context = {
            "form": form,
            "title": "Edit Voucher : " + instance.title,
            "edit":True,
            "instance": instance,
            "url": reverse('offers:edit_voucher', kwargs={'pk': instance.pk}),
            "redirect": True,

        }
        return render(request, 'offers/voucher/voucher_entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def voucher(request, pk):
    instance = get_object_or_404(
        VoucherCode.objects.filter(pk=pk, is_deleted=False))
    context = {
        "instance": instance,
        "title": "Voucher Code : " + instance.voucher_code,
        "single_page": True,
    }

    return render(request, 'offers/voucher/voucher.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_voucher(request, pk):
    reason = request.GET.get('reason')
    # instance = get_object_or_404(VoucherCode.objects.filter(pk=pk, is_deleted=False))

    VoucherCode.objects.filter(pk=pk).update(is_deleted=True, deleted_reason=reason)

    response_data = {
        "status": "true",
        "title": "Successfully Deleted",
        "message": "Voucher Code Successfully Deleted.",
        "redirect": "true",
        "redirect_url": reverse('offers:vouchers')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def vouchers(request):
    instances = VoucherCode.objects.filter(is_deleted=False)
    title = "Voucher Codes"
    query = request.GET.get("q")
    if query:
        instances = instances.filter(
            Q(auto_id__icontains=query) |
            Q(voucher_code__icontains=query)
        )
        title = "Voucher Codes - %s" % query

    context = {
        "instances": instances,
        'title': title,
    }
    return render(request, 'offers/voucher/vouchers.html', context)
