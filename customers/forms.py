from django import forms
from django.forms.widgets import TextInput, Textarea, Select
from django.utils.translation import ugettext_lazy as _
from dal import autocomplete
from customers.models import Customer, PrivilegePoint,Ticket


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        exclude = ['creator', 'updater','deleted_reason', 'auto_id', 'current_privilege_points',
                   'privilege_points', 'is_deleted', 'user', 'current_balance']

        widgets = {
            'name': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Name'}),
            'email': TextInput(attrs={'class': ' email form-control', 'placeholder': 'Email'}),
            'customer_type': Select(attrs={'class': 'required form-control', 'placeholder': 'Customer Type'}),
            'opening_balance': TextInput(attrs={'class': 'form-control', 'placeholder': ' Opening Balance'}),
            'opening_type': Select(attrs={'class': 'required form-control'}),
            'gst_number': TextInput(attrs={'class': 'form-control', 'placeholder': 'Gst Number'}),
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


class CustomerFilterForm(forms.Form):
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.filter(is_deleted=False),
        required=False,
        widget=autocomplete.ModelSelect2(url='customers:customer_autocomplete', attrs={
                                         'class': 'form-control', 'data-placeholder': 'Customer', 'data-minimum-input-length': 0}),
    )


class PrivilegePointForm(forms.ModelForm):
    class Meta:
        model = PrivilegePoint
        exclude = ['creator', 'updater','deleted_reason', 'auto_id', 'is_deleted']

        widgets = {
            'minimum_amount': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Minimum Amount'}),
            'value_of_point': TextInput(attrs={'class': 'form-control', 'placeholder': 'Value Of Point'}),
            'point_gained_online': TextInput(attrs={'class': 'form-control', 'placeholder': 'Point Gained Online'}),
            'point_gained_offline': TextInput(attrs={'class': 'form-control', 'placeholder': 'Point Gained Offline'}),
        }

        error_messages = {
            'minimum_amount': {
                'required': _("minimum_amount field is required."),
            },
            'value_of_point': {
                'required': _("value_of_point field is required."),
            },
            'point_gained_online': {
                'required': _("point_gained_online field is required."),
            },
            'point_gained_offline': {
                'required': _("point_gained_offline field is required."),
            },
        }

        labels = {
            'minimum_amount': 'Minimum Purchase amount',
            'value_of_point': 'Value of a point when withdrawing'
        }


class TicketRejectForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['reject_reason']

        widgets = {
            'reject_reason': Textarea(attrs={'class': 'form-control', 'placeholder': 'Specify the reject reason'}),
        }
        error_messages = {
            'reject_reason': {
                'required': _("minimum_amount field is required."),
            },

        }



class TicketResolvedForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['message']

        widgets = {
            'message': Textarea(attrs={'class': 'form-control', 'placeholder': 'Message'}),
        }
        error_messages = {
            'message': {
                'required': _("Message field is required."),
            },

        }