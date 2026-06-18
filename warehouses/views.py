import xlrd
import xlwt
import json
import datetime
import requests
from decimal import Decimal
from itertools import chain
from operator import attrgetter, itemgetter
# Third party libraries
from ast import literal_eval
from dal import autocomplete
# Django libraries
from django.shortcuts import render, get_object_or_404
from django.conf import settings as SETTINGS
from django.conf import settings
from django.urls import reverse
from django.db.models import Q, F, Sum
from django.core import serializers
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from django.forms.models import inlineformset_factory
from django.forms.widgets import Select, TextInput
from django.forms.formsets import formset_factory
from django.http.response import HttpResponse, HttpResponseRedirect
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
# Local libraries
from main.decorators import role_required
from main.functions import generate_form_errors, get_auto_id, get_a_id, get_date_updated_request
from staffs.models import Staff
from users.forms import UserForm
from staffs.forms import StaffForm
from warehouses.models import Warehouse, Location
from warehouses.forms import WarehouseForm,LocationForm
from products.models import ProductVariant
from orders.models import Orders


class WarehouseAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        items = Warehouse.objects.filter(is_deleted=False)

        if Staff.objects.filter(user=self.request.user, warehouse__isnull=False).exists():
            warehouse_pk = Staff.objects.get(user=self.request.user, warehouse__isnull=False).warehouse.pk
            items = items.filter(pk=warehouse_pk)

        if self.q:
            items = items.filter(
                Q(auto_id__istartswith=self.q) |
                Q(name__istartswith=self.q)
            )

        return items


class ToWarehouseAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        items = Warehouse.objects.filter(is_deleted=False)

        warehouse = self.forwarded.get('warehouse', None)
        if warehouse:
            items = items.exclude(pk=warehouse)

        if Staff.objects.filter(user=self.request.user, warehouse__isnull=False).exists():
            pk = Staff.objects.get(user=self.request.user, warehouse__isnull=False).warehouse.pk
            items = items.exclude(pk=pk)

        if self.q:
            items = items.filter(
                Q(auto_id__istartswith=self.q) |
                Q(name__istartswith=self.q)
            )

        return items


class LocationAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        items = Location.objects.filter(is_deleted=False)

        if self.q:
            items = items.filter(
                Q(auto_id__istartswith=self.q) |
                Q(name__istartswith=self.q)
            )

        return items


class WarehouseLocationAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        instances = Location.objects.filter(is_deleted=False)

        ''' this section of code is used for filtering locations that doesn't fall under any other warehouses.'''
        warehouses = Warehouse.objects.filter(is_deleted=False)
        items = Location.objects.none()

        for warehouse in warehouses:
            items |= warehouse.location.all()

        if items.exists():
            item_pks = items.values_list('pk', flat=True)
            instances = instances.exclude(pk__in=item_pks)
        ''' warehouse filter ends here.'''

        if self.q:
            instances = instances.filter(
                Q(auto_id__istartswith=self.q) |
                Q(name__istartswith=self.q)
            )

        return instances


@login_required
@role_required(['superadmin'])
def create_warehouse(request):
    if request.method == 'POST':
        form = WarehouseForm(request.POST)

        if form.is_valid():
            auto_id = get_auto_id(Warehouse)
            # create warehouse
            data = form.save(commit=False)
            data.creator = request.user
            data.updater = request.user
            data.auto_id = auto_id
            data.save()

            location = request.POST.getlist('location')
            for item in location:
                p = Location.objects.get(pk=item)
                data.location.add(p)

            staff = form.cleaned_data['manager']
            if staff:
                staff.warehouse = data
                staff.save()
            response_data = {
                "status": "true",
                "title": "Successfully Created",
                "message": "Warehouse Created Successfully.",
                "redirect": "true",
                "redirect_url": reverse('warehouses:warehouse', kwargs={'pk': data.pk})
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
        auto_id = get_auto_id(Staff)
        if auto_id < 10:
            staff_id = 'ONZ000%s' % (str(auto_id))
        elif auto_id < 100:
            staff_id = 'ONZ00%s' % (str(auto_id))
        elif auto_id < 1000:
            staff_id = 'ONZ0%s' % (str(auto_id))
        else:
            staff_id = 'ONZ%s' % (str(auto_id))

        staff_initial = {
            'staff_id': staff_id,
            'staff_role': 'warehouse_manager',
        }

        user_form = UserForm()
        staff_form = StaffForm(initial=staff_initial)
        form = WarehouseForm()

        context = {
            "title": "Create Warehouse ",
            "form": form,
            "staff_form": staff_form,
            "user_form": user_form,
            "url": reverse('warehouses:create_warehouse'),
        }

        return render(request, 'warehouses/warehouse_entry.html', context)


@login_required
@role_required(['superadmin'])
def warehouses(request):
    instances = Warehouse.objects.filter(is_deleted=False)
    title = "Warehouse"
    query = request.GET.get("q")
    if query:
        instances = instances.filter(
            Q(auto_id__icontains=query) | Q(name__icontains=query))
        title = "Brands - %s" % query
    print(instances)
    context = {
        "instances": instances,
        'title': title,

    }
    return render(request, 'warehouses/warehouses.html', context)


@login_required
@role_required(['superadmin'])
def warehouse(request, pk):
    instance = get_object_or_404(
        Warehouse.objects.filter(pk=pk, is_deleted=False))
    context = {
        "instance": instance,
        "title": "Warehouse : " + instance.name,
        "single_page": True,

    }
    return render(request, 'warehouses/warehouse.html', context)


@login_required
@role_required(['superadmin'])
def edit_warehouse(request, pk):
    instance = get_object_or_404(
        Warehouse.objects.filter(pk=pk, is_deleted=False))
    old_staff = instance.manager
    if old_staff:
        old_staff.warehouse = None
        old_staff.save()

    if request.method == 'POST':
        response_data = {}
        form = WarehouseForm(request.POST, instance=instance)

        if form.is_valid():

            # update warehouse
            data = form.save(commit=False)
            data.updater = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            locations = request.POST.getlist('location')
            instance.location.clear()
            for item in locations:
                p = Location.objects.get(pk=item)
                data.location.add(p)

            staff = form.cleaned_data['manager']
            if staff:
                staff.warehouse = data
                staff.save()

            response_data = {
                "status": "true",
                "title": "Successfully Updated",
                "message": "Warehouse Successfully Updated.",
                "redirect": "true",
                "redirect_url": reverse('warehouses:warehouse', kwargs={'pk': data.pk})
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
        auto_id = get_auto_id(Staff)
        if auto_id < 10:
            staff_id = 'ONZ000%s' % (str(auto_id))
        elif auto_id < 100:
            staff_id = 'ONZ00%s' % (str(auto_id))
        elif auto_id < 1000:
            staff_id = 'ONZ0%s' % (str(auto_id))
        else:
            staff_id = 'ONZ%s' % (str(auto_id))

        staff_initial = {
            'staff_id': staff_id,
            'staff_role': 'warehouse_manager',
        }
        user_form = UserForm()
        staff_form = StaffForm(initial=staff_initial)
        form = WarehouseForm(instance=instance)

        context = {
            "form": form,
            "user_form": user_form,
            "staff_form": staff_form,
            "title": "Edit Warehouse : " + instance.name,
            "instance": instance,
            "url": reverse('warehouses:edit_warehouse', kwargs={'pk': instance.pk}),
            "redirect": True,

        }
        return render(request, 'warehouses/warehouse_entry.html', context)


@login_required
@role_required(['superadmin'])
def delete_warehouse(request, pk):
    reason = request.GET.get('reason')
    instance = get_object_or_404(
        Warehouse.objects.filter(pk=pk, is_deleted=False))

    Warehouse.objects.filter(pk=pk).update(
        is_deleted=True, name=instance.name + "_deleted_" + str(instance.auto_id),deleted_reason=reason)

    response_data = {
        "status": "true",
        "title": "Successfully Deleted",
        "message": "WarehouseSuccessfully Deleted.",
        "redirect": "true",
        "redirect_url": reverse('warehouses:warehouses')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin'])
def delete_selected_warehouses(request):
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(
                Warehouse.objects.filter(pk=pk, is_deleted=False))
            Warehouse.objects.filter(pk=pk).update(
                is_deleted=True, name=instance.name + "_deleted_" + str(instance.auto_id))

        response_data = {
            "status": "true",
            "title": "Successfully Deleted",
            "message": "Selected Warehouse Successfully Deleted.",
            "redirect": "true",
            "redirect_url": reverse('warehouses:warehouses')
        }
    else:
        response_data = {
            "status": "false",
            "title": "Nothing selected",
            "message": "Please select some items first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


def get_warehouse_variant(request):
    pk = request.GET.get('id')

    if Warehouse.objects.filter(pk=pk, is_deleted=False,).exists():
        warehouse = Warehouse.objects.get(pk=pk)
        variants = ProductVariant.objects.filter(warehouse=warehouse, is_admin_approved=True, is_deleted=False)
        variants_arr = []
        results = []
        for i in variants:
            if i.product.brand:
                name = str(i.product.brand)+str('-') + str(i.product.name)+str('-')+str(i.title)
            else:
                name = str(i.product.name)+str('-')+str(i.title)
            dic = {
                'id': str(i.id),
                'name': name,
            }
            variants_arr.append(dic)
        response_data = {
            "status": 'true',
            "variants": variants_arr,

        }
    else:
        response_data = {
            "status": "false",
            "message": "Warehouse is not exists."
        }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin'])
def create_location(request):

    if request.method == 'POST':
        form = LocationForm(request.POST)

        if form.is_valid():

            auto_id = get_auto_id(Warehouse)

            # create location

            data = form.save(commit=False)
            data.creator = request.user
            data.updater = request.user
            data.auto_id = auto_id

            data.save()

            response_data = {
                "status": "true",
                "title": "Successfully Created",
                "message": "Warehouse Created Successfully.",
                "redirect": "true",
                "redirect_url": reverse('warehouses:warehouse', kwargs={'pk': data.pk})
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
        form = LocationForm()
        context = {
            "title": "Create Location ",
            "form": form,
            "url": reverse('warehouses:create_location'),


        }
        return render(request, 'warehouses/location_entry.html', context)


@login_required
@role_required(['superadmin'])
def locations(request):

    instances = Location.objects.filter(is_deleted=False)
    title = "Location"
    query = request.GET.get("q")
    if query:
        instances = instances.filter(
            Q(auto_id__icontains=query) | Q(name__icontains=query))
        title = "Location - %s" % query

    context = {
        "instances": instances,
        'title': title,

    }
    return render(request, 'warehouses/locations.html', context)


@login_required
@role_required(['superadmin'])
def location(request, pk):
    instance = get_object_or_404(
        Location.objects.filter(pk=pk, is_deleted=False))
    context = {
        "instance": instance,
        "title": "Location : " + instance.name,
        "single_page": True,

    }
    return render(request, 'warehouses/location.html', context)


@login_required
@role_required(['superadmin'])
def edit_location(request, pk):
    instance = get_object_or_404(
        Location.objects.filter(pk=pk, is_deleted=False))

    if request.method == 'POST':
        response_data = {}
        form = LocationForm(request.POST, instance=instance)

        if form.is_valid():

            # update stock location
            data = form.save(commit=False)
            data.updater = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            response_data = {
                "status": "true",
                "title": "Successfully Updated",
                "message": "Warehouse Successfully Updated.",
                "redirect": "true",
                "redirect_url": reverse('warehouses:location', kwargs={'pk': data.pk})
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
        form = LocationForm(instance=instance)

        context = {
            "form": form,
            "title": "Edit Location : " + instance.name,
            "instance": instance,
            "url": reverse('warehouses:edit_location', kwargs={'pk': instance.pk}),
            "redirect": True,

        }
        return render(request, 'warehouses/location_entry.html', context)


@login_required
@role_required(['superadmin'])
def delete_location(request, pk):
    reason = request.GET.get('reason')
    instance = get_object_or_404(
        Location.objects.filter(pk=pk, is_deleted=False))

    Location.objects.filter(pk=pk).update(
        is_deleted=True, name=instance.name + "_deleted_" + str(instance.auto_id),deleted_reason=reason)

    response_data = {
        "status": "true",
        "title": "Successfully Deleted",
        "message": "Location Successfully Deleted.",
        "redirect": "true",
        "redirect_url": reverse('warehouses:locations')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin'])
def delete_selected_locations(request):
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(
                Location.objects.filter(pk=pk, is_deleted=False))
            Location.objects.filter(pk=pk).update(
                is_deleted=True, name=instance.name + "_deleted_" + str(instance.auto_id))

        response_data = {
            "status": "true",
            "title": "Successfully Deleted",
            "message": "Selected Location Successfully Deleted.",
            "redirect": "true",
            "redirect_url": reverse('warehouses:locations')
        }
    else:
        response_data = {
            "status": "false",
            "title": "Nothing selected",
            "message": "Please select some items first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin'])
def create_location(request):

    if request.method == 'POST':
        form = LocationForm(request.POST)

        if form.is_valid():

            name = form.cleaned_data['name']
            pincode = form.cleaned_data['pincode']

            latitude = None
            longitude = None

            baseurl_1 = f"https://api.postalpincode.in/pincode/{pincode}"
            baseurl_2 = f"https://maps.googleapis.com/maps/api/geocode/json?address={pincode}&key={SETTINGS.PLACES_MAPS_API_KEY}"

            postofficeapi_response = requests.get(baseurl_1).json()
            googleapi_response = requests.get(baseurl_2).json()

            if postofficeapi_response[0]["Status"] == 'Success' and googleapi_response['status'] == 'OK':

                if 'PostOffice' in postofficeapi_response[0] and 'postal_code' in googleapi_response['results'][0][
                    'types']:
                    for post_offices in postofficeapi_response[0]['PostOffice']:
                        response = post_offices
            else:
                response = False

            latitude = googleapi_response['results'][0]['geometry']['location']['lat']
            longitude = googleapi_response['results'][0]['geometry']['location']['lng']

            auto_id = get_auto_id(Location)

            # create location
            data = form.save(commit=False)
            data.creator = request.user
            data.updater = request.user
            data.latitude = latitude
            data.longitude = longitude
            data.auto_id = auto_id

            data.save()

            response_data = {
                "status": "true",
                "title": "Successfully Created",
                "message": "Location Created Successfully.",
                "redirect": "true",
                "redirect_url": reverse('warehouses:location', kwargs={'pk': data.pk})
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
        form = LocationForm()
        context = {
            "title": "Create Location ",
            "form": form,
            "url": reverse('warehouses:create_location'),
            "location": True,
        }
        return render(request, 'warehouses/location_new_entry.html', context)



@login_required
@role_required(['superadmin'])
def locations(request):

    instances = Location.objects.filter(is_deleted=False)
    title = "Location"
    query = request.GET.get("q")
    if query:
        instances = instances.filter(
            Q(auto_id__icontains=query) | Q(name__icontains=query))
        title = "Location - %s" % query
    print(instances)
    context = {
        "instances": instances,
        'title': title,

    }
    return render(request, 'warehouses/locations.html', context)


@login_required
@role_required(['superadmin'])
def location(request, pk):
    instance = get_object_or_404(
        Location.objects.filter(pk=pk, is_deleted=False))
    context = {
        "instance": instance,
        "title": "Location : " + instance.name,
        "single_page": True,

    }
    return render(request, 'warehouses/location.html', context)


@login_required
@role_required(['superadmin'])
def edit_location(request, pk):
    instance = get_object_or_404(
        Location.objects.filter(pk=pk, is_deleted=False))

    if request.method == 'POST':
        response_data = {}
        form = LocationForm(request.POST, instance=instance)

        if form.is_valid():

            name = form.cleaned_data['name']
            pincode = form.cleaned_data['pincode']

            latitude = None
            longitude = None

            baseurl_1 = f"https://api.postalpincode.in/pincode/{pincode}"
            baseurl_2 = f"https://maps.googleapis.com/maps/api/geocode/json?address={pincode}&key={SETTINGS.PLACES_MAPS_API_KEY}"

            postofficeapi_response = requests.get(baseurl_1).json()
            googleapi_response = requests.get(baseurl_2).json()

            if postofficeapi_response[0]["Status"] == 'Success' and googleapi_response['status'] == 'OK':

                if 'PostOffice' in postofficeapi_response[0] and 'postal_code' in googleapi_response['results'][0][
                    'types']:
                    for post_offices in postofficeapi_response[0]['PostOffice']:
                        response = post_offices
            else:
                response = "false"

            latitude = googleapi_response['results'][0]['geometry']['location']['lat']
            longitude = googleapi_response['results'][0]['geometry']['location']['lng']

            auto_id = get_auto_id(Location)

            # create location
            data = form.save(commit=False)
            data.updater = request.user
            data.date_updated = datetime.datetime.now()
            data.latitude = latitude
            data.longitude = longitude

            data.save()

            response_data = {
                "status": "true",
                "title": "Successfully Updated",
                "message": "Location Successfully Updated.",
                "redirect": "true",
                "redirect_url": reverse('warehouses:location', kwargs={'pk': data.pk})
            }
        else:
            message = generate_form_errors(form, formset=False)

            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": str(message),
                "location": True,
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = LocationForm(instance=instance)

        context = {
            "form": form,
            "title": "Edit Location : " + instance.name,
            "instance": instance,
            "url": reverse('warehouses:edit_location', kwargs={'pk': instance.pk}),
            "redirect": True,
            "location": True,
            "is_location_edit":True,
        }
        print("jiii")
        return render(request, 'warehouses/location_new_entry.html', context)


@login_required
@role_required(['superadmin'])
def delete_location(request, pk):
    reason = request.GET.get('reason')
    instance = get_object_or_404(
        Location.objects.filter(pk=pk, is_deleted=False))

    Location.objects.filter(pk=pk).update(
        is_deleted=True, name=instance.name + "_deleted_" + str(instance.auto_id),deleted_reason=reason)

    response_data = {
        "status": "true",
        "title": "Successfully Deleted",
        "message": "LocationSuccessfully Deleted.",
        "redirect": "true",
        "redirect_url": reverse('warehouses:locations')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin'])
def delete_selected_locations(request):
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(
                Location.objects.filter(pk=pk, is_deleted=False))
            Location.objects.filter(pk=pk).update(
                is_deleted=True, name=instance.name + "_deleted_" + str(instance.auto_id))

        response_data = {
            "status": "true",
            "title": "Successfully Deleted",
            "message": "Selected Location Successfully Deleted.",
            "redirect": "true",
            "redirect_url": reverse('warehouses:warehouses')
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
def our_orders(request):

    staff_instance = Staff.objects.get(user=request.user)
    instances = Orders.objects.filter(is_deleted=False, order_status="10",warehouse=staff_instance.warehouse)

    query = request.GET.get('query')
    if query:
        if 'unassigned' in query:
            instances = instances.filter(delivery_agent__isnull=True)

        elif 'pending' in query:
            instances = instances.filter(order_status="10")

        elif 'assigned' in query:
            instances = instances.filter(delivery_agent__isnull=False, order_status__in=["10", "20"])

        elif 'shipped' in query:
            instances = Orders.objects.filter(is_deleted=False, order_status="20")

        elif 'completed' in query:
            instances = Orders.objects.filter(is_deleted=False, order_status="30")

        elif 'cancelled' in query:
            instances = Orders.objects.filter(is_deleted=False, order_status="40")

    context = {
        "title": "All Orders",
        "instances": instances,
    }
    return render(request, 'orders/orders/orders.html', context)