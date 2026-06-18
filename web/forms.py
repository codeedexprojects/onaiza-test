from django import forms
from django.forms.widgets import TextInput, Textarea, HiddenInput, Select, FileInput
from products.models import Category
from dal import autocomplete
from django.utils.translation import ugettext_lazy as _
from web.models import FeauturedCategory, SpotlightBanner
from customers.models import UserOtpData, Customer
from warehouses.models import Location
from orders.models import TimeSlot


class FeauturedCategoryForm(forms.ModelForm):
    class Meta:
        model = FeauturedCategory
        exclude = ['creator', 'updater', 'deleted_reason', 'auto_id', 'is_deleted']
        widgets = {
            'category': autocomplete.ModelSelect2(url='products:category_autocomplete',
                                                  attrs={'data-placeholder': 'Category',
                                                         'class': 'required',
                                                         'data-minimum-input-length': 0}),
        }

        error_messages = {

            'category': {
                'required': _("Category field is required."),
            },
        }


class SpotlightBannerForm(forms.ModelForm):
    class Meta:
        model = SpotlightBanner
        exclude = ['creator', 'updater', 'deleted_reason', 'auto_id', 'is_deleted']
        widgets = {
            'banner_type': Select(attrs={"class": " selectpicker form-control", "data-live-search": "true"}),
            'offer_type': Select(attrs={"class": " selectpicker form-control", "data-live-search": "true"}),
            'product_variant': autocomplete.ModelSelect2(url='products:product_variant_autocomplete',
                                                         attrs={'data-placeholder': 'Product Variant', 'class': '',
                                                                'data-minimum-input-length': 0}),
            'category': autocomplete.ModelSelect2(url='products:category_autocomplete',
                                                  attrs={'data-placeholder': 'Category', 'class': '',
                                                         'data-minimum-input-length': 0}),
            'brand': autocomplete.ModelSelect2(url='products:brand_autocomplete',
                                               attrs={'data-placeholder': 'Brand', 'class': '',
                                                      'data-minimum-input-length': 0}),

        }

        error_messages = {

            'product_variant': {
                'required': _("Product field is required."),
            },
        }


class SignUpForm(forms.ModelForm):
    class Meta:
        model = UserOtpData
        fields = ['name', 'phone']
        widgets = {
            'phone': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Enter Your Phone Number'}),
            'name': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Enter Your Phone Name'}),

        }

        error_messages = {

            'phone': {
                'required': _("Phone field is required."),
            },
            'name': {
                'required': _("Name field is required."),
            },
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone', 'image', 'address']
        widgets = {
            'phone': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Enter Your Phone Number'}),
            'name': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Enter Your Phone Name'}),
            'email': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Enter Your Phone Name'}),
            'address': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Address'}),
        }

        error_messages = {

            'phone': {
                'required': _("Phone field is required."),
            },
            'name': {
                'required': _("Name field is required."),
            },
            'email': {
                'required': _("Email field is required."),
            },
        }


class PincodeForm(forms.Form):
    pincode = forms.ModelChoiceField(queryset=Location.objects.filter(is_deleted=False))
