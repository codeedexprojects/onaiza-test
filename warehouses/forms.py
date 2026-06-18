from django import forms
from django.forms.widgets import TextInput, Textarea, HiddenInput, Select, FileInput
from warehouses.models import Warehouse, Location
from dal import autocomplete
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError


class WarehouseForm(forms.ModelForm):

    class Meta:
        model = Warehouse
        exclude = ['creator', 'updater','deleted_reason', 'auto_id', 'is_deleted']
        widgets = {
            'name': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Name'}),
            # 'location': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Location'}),
            'location': autocomplete.ModelSelect2Multiple(url='warehouses:warehouse_location_autocomplete', attrs={'data-placeholder': 'Location', 'data-minimum-input-length': 0},),
            'manager': autocomplete.ModelSelect2(url='staffs:warehouse_manager_autocomplete', attrs={'data-placeholder': 'Warehouse Manager', 'data-minimum-input-length': 0},),

            'phone': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Phone'}),
            'address': Textarea(attrs={'class': 'required form-control', 'placeholder': 'Address'}),
            'state': Select(attrs={'class': 'form-control', 'placeholder': 'State code'}),
            'district': TextInput(attrs={'class': 'form-control', 'placeholder': 'District'}),
            'country': TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),
        }

        error_messages = {
            'name': {
                'required': _("Name field is required."),
            },
            'location': {
                'required': _("Location field is required."),
            },
        }


class LocationForm(forms.ModelForm):

    class Meta:
        model = Location
        exclude = ['creator', 'updater','deleted_reason', 'auto_id', 'is_deleted']
        widgets = {
            'name': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Name'}),
            'malayalam_name': TextInput(attrs={'class': 'required form-control', 'placeholder': 'മലയാളം പേര്'}),
            'pincode': Select(attrs={'class': 'required form-control', 'placeholder': 'Pincode'}),
        }

        error_messages = {
            'name': {
                'required': _("Name field is required."),
            },
            'pincode': {
                'required': _("Pincode field is required."),
            },
        }
