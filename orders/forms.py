from django import forms
from django.forms.widgets import TextInput, Textarea, HiddenInput, Select, FileInput
from products.models import Category
from dal import autocomplete
from django.utils.translation import ugettext_lazy as _
from orders.models import *


class TimeslotDayForm(forms.ModelForm):
    class Meta:
        model = TimeSlot
        fields = ['day']
        widgets = {
            'day': Select(attrs={'class': " form-control"}),
        }

        error_messages = {
            'day': {
                'required': _("Day field is required."),
            },
        }


class TimeslotTimeForm(forms.ModelForm):
    class Meta:
        model = TimeSlot
        exclude = ['creator', 'updater','deleted_reason', 'auto_id', 'is_deleted', 'day']
        widgets = {
            'start_time': TextInput(attrs={'class': 'required date-time-picker form-control','type': 'time', 'placeholder': 'Start Time'}),
            'end_time': TextInput(attrs={'class': 'required date-time-picker form-control','type': 'time', 'placeholder': 'End Time'}),
        }

        error_messages = {
            'day': {
                'required': _("Day field is required."),
            },
            'start_time': {
                'required': _("Start Time field is required."),
            },
            'end_time': {
                'required': _("End Time field is required."),
            },
        }


class TimeslotForm(forms.ModelForm):
    class Meta:
        model = TimeSlot
        exclude = ['creator', 'updater','deleted_reason', 'auto_id', 'is_deleted']
        widgets = {
            'day': Select(attrs={'class': "form-control"}),
            'start_time': TextInput(attrs={'class': 'required date-time-picker form-control','type': 'time', 'placeholder': 'Start Time'}),
            'end_time': TextInput(attrs={'class': 'required date-time-picker form-control','type': 'time', 'placeholder': 'End Time'}),
        }

        error_messages = {
            'day': {
                'required': _("Day field is required."),
            },
            'start_time': {
                'required': _("Start Time field is required."),
            },
            'end_time': {
                'required': _("End Time field is required."),
            },
        }


class DeliveryAgentAssignForm(forms.ModelForm):
    class Meta:
        model = Orders
        fields = ['delivery_agent']
        widgets = {
            'delivery_agent': autocomplete.ModelSelect2(attrs={'data-placeholder': 'Category', 'class': 'required',
                                                         'data-minimum-input-length': 0}),

        }

        error_messages = {
            'delivery_agent': {
                'required': _("Day field is required."),
            },

        }


class OrderStatusForm(forms.Form):
    ORDER_CHOICES = (
            ("10", 'Pending'),
            ("20", 'Shipped'),
            ("30", 'Delivered'),
            ("40", 'Cancelled'),
        )
    order_status = forms.CharField(widget=forms.Select(choices=ORDER_CHOICES, attrs={'class':'form-control selectpicker'}))

