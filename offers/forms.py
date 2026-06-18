from django import forms
from django.forms.widgets import TextInput, Textarea, HiddenInput, Select, FileInput, CheckboxInput
from offers.models import Offers, DealOfDay, VoucherCode
from dal import autocomplete
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError


class OffersForm(forms.ModelForm):
    class Meta:
        model = Offers
        exclude = ['creator', 'updater','deleted_reason', 'auto_id', 'is_deleted']
        widgets = {
            'title': TextInput(attrs={'class': 'required form-control', 'placeholder': 'title'}),
            'offer_type': Select(attrs={'class': 'required form-control'}),
            'offer_percentage': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Offer Percentage'}),

            'start_time': TextInput(attrs={'class': 'required date-time-picker form-control', 'type': 'date', 'placeholder': 'Start Time'}),
            'end_time': TextInput(attrs={'class': 'required date-time-picker form-control', 'type': 'date', 'placeholder': 'End Time'}),

            'warehouse': autocomplete.ModelSelect2(url='warehouses:warehouse_autocomplete', attrs={'class': 'required', 'data-placeholder': 'Warehouse', 'data-minimum-input-length': 0},),
            'product_variant': autocomplete.ModelSelect2(url='products:product_variant_autocomplete', attrs={'data-placeholder': 'Product', 'data-minimum-input-length': 0},),
            'category': autocomplete.ModelSelect2(url='products:category_autocomplete', attrs={'data-placeholder': 'Category', 'data-minimum-input-length': 0},),
            'subcategory': Select(attrs={'class': 'form-control'}),
            'image': FileInput(attrs={'class': 'form-control'}),
        }

        error_messages = {
            'start_time': {
                'required': _("Start Time field is required."),
            },
            'end_time': {
                'required': _("End Time field is required."),
            },
            'warehouse': {
                'required': _("Warehouse field is required."),
            },
            'product_variant': {
                'required': _("Product Variant field is required."),
            },
            'offer_percentage': {
                'required': _("Offer Percentage field is required."),
            }
        }


class DealOfDayForm(forms.ModelForm):
    class Meta:
        model = DealOfDay
        exclude = ['creator', 'updater','deleted_reason', 'auto_id', 'is_deleted']

        widgets = {
            'deal_date': TextInput(attrs={'class': 'required date-picker form-control', 'placeholder': 'Deal Date'}),
            'warehouse': autocomplete.ModelSelect2(url='warehouses:warehouse_autocomplete',attrs={'class': 'required', 'data-placeholder': 'Warehouse','data-minimum-input-length': 0}, ),
            'product_variant': autocomplete.ModelSelect2(url='products:product_variant_autocomplete',attrs={'class': 'required', 'data-placeholder': 'Product','data-minimum-input-length': 0}, ),
            'offer_percentage': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Offer Percentage'}),
        }

        error_messages = {
            'deal_date': {
                'required': _("Deal Date field is required."),
            },
            'warehouse': {
                'required': _("Warehouse field is required."),
            },
            'product_variant': {
                'required': _("Product Variant field is required."),
            },
            'offer_percentage': {
                'required': _("Offer Percentage field is required."),
            }
        }


class VoucherForm(forms.ModelForm):
    class Meta:
        model = VoucherCode
        exclude = ['creator', 'updater','deleted_reason', 'auto_id', 'is_deleted']
        widgets = {
            'is_expired': CheckboxInput(),
            'is_exclusive': CheckboxInput(),
            'customer': autocomplete.ModelSelect2(url='customers:customer_autocomplete', attrs={'data-placeholder': 'Customers', 'data-minimum-input-length': 0}, ),
            'percentage': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Percentage'}),

            'voucher_code': TextInput(attrs={'class': 'required date-time-picker form-control', 'placeholder': 'Voucher Code'}),
            'title': TextInput(attrs={'class': 'required date-time-picker form-control', 'placeholder': 'Title'}),
            'description': TextInput(attrs={'class': 'required date-time-picker form-control', 'placeholder': 'Description'}),
            'start_time': TextInput(attrs={'class': ' date-time-picker form-control', 'type': 'date', 'placeholder': 'Start Time'}),
            'end_time': TextInput(attrs={'class': ' date-time-picker form-control', 'type': 'date', 'placeholder': 'End Time'}),
            'upto_limit': TextInput(attrs={'class': 'required date-time-picker form-control', 'placeholder': 'Upto Limit'}),
            'minimum_order_amount': TextInput(attrs={'class': 'required date-time-picker form-control', 'placeholder': 'Minimum Order Amount'}),
        }
        error_messages = {
            'is_expired': {
                'required': _("Expired field is required."),
            },
            'voucher_code': {
                'required': _("Voucher Code field is required."),
            },
            'title': {
                'required': _("Title field is required."),
            },
            'description': {
                'required': _("Description Variant field is required."),
            },
            'is_exclusive': {
                'required': _("Exclusive field is required."),
            },
            'customer': {
                'required': _("Customer field is required."),
            },
            'start_time': {
                'required': _("Start time field is required."),
            },
            'end_time': {
                'required': _("End time field is required."),
            },
            'upto_limit': {
                'required': _("Upto Limit field is required."),
            }
        }
