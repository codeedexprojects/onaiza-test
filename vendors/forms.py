from django import forms
from django.forms.widgets import TextInput, Select
from vendors.models import Vendor
from dal import autocomplete
from django.utils.translation import ugettext_lazy as _


class VendorForm(forms.ModelForm):
    username = forms.CharField(label=_("Username"), max_length=254, widget=forms.TextInput(
        attrs={'class': 'required form-control',}))

    password = forms.CharField(label=_("Password"), max_length=254, widget=forms.TextInput(
        attrs={'class': 'required form-control', }))

    class Meta:
        model = Vendor
        exclude = ['creator', 'updater','deleted_reason', 'auto_id',
                   'is_deleted', 'current_balance']
        widgets = {
            'name': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Name'}),
            'malayalam_name': TextInput(attrs={'class': 'required form-control', 'placeholder': 'മലയാളം പേര്'}),
            'address': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Address'}),
            'phone': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Phone'}),
            'email': TextInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'opening_type': Select(attrs={'class': 'required form-control'}),

            'district': TextInput(attrs={'class': 'form-control', 'placeholder': 'District'}),
            'country': TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),


            'place': TextInput(attrs={'class': 'form-control', 'placeholder': 'Place'}),
            'location': autocomplete.ModelSelect2(url='warehouses:location_autocomplete', attrs={'data-placeholder': 'Location', 'data-minimum-input-length': 0},),
            'commission_type': Select(attrs={'class': 'required form-control'}),
            'commission_percentage': TextInput(attrs={'class': 'form-control', 'placeholder': ' Commission Percentage'}),

            'opening_balance': TextInput(attrs={'class': 'form-control', 'placeholder': ' Opening Balance'}),
            'state': Select(attrs={'class': 'form-control', 'placeholder': 'State code'}),
            'gst_number': TextInput(attrs={'class': 'form-control', 'placeholder': 'Gst Number'}),
            'bank_name': TextInput(attrs={'class': 'form-control', 'placeholder': 'Bank Name'}),
            'branch': TextInput(attrs={'class': 'form-control', 'placeholder': 'Branch'}),
            'bank_account_name': TextInput(attrs={'class': 'form-control', 'placeholder': 'Bank Account Name'}),
            'ifsc_code': TextInput(attrs={'class': 'form-control', 'placeholder': 'IFSC'}),
            'account_num': TextInput(attrs={'class': 'form-control', 'placeholder': 'Account Number'}),


        }
        error_messages = {
            'name': {
                'required': _("Name field is required."),
            },
            'address': {
                'required': _("Address field is required."),
            },
            'phone': {
                'required': _("Phone field is required."),
            }
        }
        labels = {
            'account_num': "Account Number",
            'opening_type': "Opening Type",
            'opening_balance': "Opening Balance",
        }


class VendorCreateFromForm(forms.ModelForm):

    class Meta:
        model = Vendor
        exclude = ['creator', 'updater','deleted_reason', 'auto_id',
                   'is_deleted', 'debit', 'credit', 'current_balance']
        widgets = {
            'name': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Name'}),
            'address': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Address'}),
            'phone': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Phone'}),
            'email': TextInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'opening_type': Select(attrs={'class': 'required form-control'}),

            'district': TextInput(attrs={'class': 'form-control', 'placeholder': 'District'}),
            'country': TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),

            'opening_balance': TextInput(attrs={'class': 'form-control', 'placeholder': ' Opening Balance'}),
            'state': Select(attrs={'class': 'form-control', 'placeholder': 'State code'}),
            'gst_number': TextInput(attrs={'class': 'form-control', 'placeholder': 'Gst Number'}),

        }
