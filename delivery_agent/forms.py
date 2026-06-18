from dal import autocomplete
from delivery_agent.models import *
from django import forms
from django.forms.widgets import TextInput, FileInput
from django.utils.translation import ugettext_lazy as _


class DeliveryAgentForm(forms.ModelForm):
    class Meta:
        model = DeliveryAgents
        exclude = ['creator', 'updater','deleted_reason', 'auto_id', 'user']

        widgets = {
            'name': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Name'}),
            'email': TextInput(attrs={'class': 'email form-control', 'placeholder': 'Email'}),
            'phone1': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Phone'}),
            'phone2': TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone'}),
            'password': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Password'}),
            'image': FileInput(attrs={'class': 'form-control dropify'}),
            'proof': FileInput(attrs={'class': 'form-control dropify'}),
            'warehouse': autocomplete.ModelSelect2(url='warehouses:warehouse_autocomplete', attrs={'class': 'required', 'data-placeholder': 'Warehouse', 'data-minimum-input-length': 0}, ),
        }

        error_messages = {
            'name': {
                'required': _("Name field is required."),
            },
            'email': {
                'required': _("Email field is required."),
            },
            'phone': {
                'required': _("Phone field is required."),
            },
            'address': {
                'required': _("Addess field is required."),
            },
        }

