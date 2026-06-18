from django import forms
from django.forms.widgets import TextInput, Textarea, Select, CheckboxInput, HiddenInput
from django.utils.translation import ugettext_lazy as _
from finance.models import ReceiptVoucher
from sales.models import Sale, SaleItem, SaleReturn, SaleReturnItem
from dal import autocomplete, forward
from customers.models import Customer


class SaleItemForm(forms.ModelForm):
    class Meta:
        model = SaleItem
        fields = ['id', 'comments', 'quantity', 'amount', 'mrp',
                  'discount', 'discount_rate', 'product_variant', 'batch']

        widgets = {
            'discount_rate': HiddenInput(attrs={'class': ' number form-control', 'placeholder': 'Discount rate'}),
            # 'product': autocomplete.ModelSelect2(url='products:product_autocomplete', attrs={'data-placeholder': 'Product', 'data-minimum-input-length': 0},),
            # 'product': Select(attrs={"class":" selectpicker product form-control","data-live-search":"true"}),
            'batch': Select(attrs={"class": " selectpicker product form-control", "data-live-search": "true"}),
            # 'product_variant': Select(attrs={"class": "selectpicker form-control", "data-live-search": "true"}),
            'product_variant': autocomplete.ModelSelect2(url='products:product_variant_autocomplete', forward=["warehouse"], attrs={'data-placeholder': 'Product', 'data-minimum-input-length': 0},),
            'quantity': TextInput(attrs={'class': ' number form-control', 'placeholder': 'Qty'}),
            'amount': TextInput(attrs={'class': ' number form-control', 'placeholder': 'Amount'}),
            'price': TextInput(attrs={'class': ' number form-control', 'disabled': 'disabled', 'placeholder': 'Price'}),
            'mrp': TextInput(attrs={'class': ' number form-control', 'readonly': 'readonly', 'placeholder': 'MRP'}),
            'discount': TextInput(attrs={'class': ' number form-control', 'readonly': 'readonly', 'placeholder': 'Discount Amount'}),
            'total': TextInput(attrs={'class': ' number form-control', 'placeholder': 'Total'}),
            'hsn': TextInput(attrs={'class': ' number form-control', 'disabled': 'disabled', 'placeholder': 'hsn'}),
            'gst': TextInput(attrs={'class': 'number form-control', 'disabled': 'disabled', 'placeholder': 'gst'}),
            'net_rate': TextInput(attrs={'class': 'number form-control', 'readonly': '', 'style': 'width:2cm;'}),
            'comments': TextInput(attrs={'class': 'form-control', 'style': 'width:2cm;,', 'placeholder': 'Comments'}),
        }

        error_messages = {
            'product': {
                'required': _("Product field is required."),
            },
            'quantity': {
                'required': _("Qty field is required."),
            },
            'amount': {
                'required': _("Amount field is required."),
            },
            'total': {
                'required': _("Total field is required."),
            },
        }


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['sale_prifix','sale_id','total_outstanding','privilege_point_used', 'privilege_point_amnt', 'use_privilege_point', "warehouse", "sale_type", "sale_date", 'discount', 'discount_rate', 'customer', 'customer_address', 'transporter',
                  'shipment_date', 'sale_category', 'add_gst', 'total', 'paid', 'subtotal', 'round_off']

        widgets = {
            'warehouse': autocomplete.ModelSelect2(url='warehouses:warehouse_autocomplete', attrs={'class': 'required', 'data-placeholder': 'Warehouse', 'data-minimum-input-length': 0},),
            'sale_id': TextInput(attrs={'class': 'required form-control','readonly': 'readonly','placeholder': 'Sale Id'}),
            'sale_prifix': Select(attrs={'class': 'required form-control'}),

            'sale_date': TextInput(attrs={'class': 'required date-picker-dd form-control', 'placeholder': 'Sale Date'}),
            'discount_rate': TextInput(attrs={'class': 'required number form-control', 'placeholder': 'Discount rate'}),
            'discount': TextInput(attrs={'class': 'required number form-control', 'placeholder': 'Discount'}),
            'customer': autocomplete.ModelSelect2(url='customers:customer_autocomplete', forward=["sale_type"], attrs={'data-placeholder': 'Customer', 'data-minimum-input-length': 0},),
            'transporter': TextInput(attrs={'class': 'form-control', 'placeholder': 'Transporter Vehicle Number'}),
            'shipment_date': TextInput(attrs={'class': 'required date-picker-dd form-control', 'placeholder': 'Shipment Date'}),
            'sale_category': Select(attrs={'class': 'required form-control'}),
            'sale_type': Select(attrs={'class': 'required form-control'}),
            'subtotal': TextInput(attrs={'class': 'required number form-control', 'id': 'meterial_subtotal', 'placeholder': 'Subtotal', "readonly": ""}),
            'total': TextInput(attrs={'class': 'required number form-control', 'id': 'meterial_total', 'placeholder': 'Total', 'readonly': ""}),
            'customer_address': TextInput(attrs={'class': ' form-control', 'placeholder': 'Shipping Address'}),
            'paid': TextInput(attrs={'class': ' number form-control', 'id': 'paid_amount', 'placeholder': 'balance'}),
            'privilege_point_used': TextInput(attrs={'type': 'number','class': ' number form-control', 'placeholder': 'Privilege Point Used'}),
            'privilege_point_amnt': TextInput(attrs={'class': ' number form-control', 'readonly': 'readonly', 'placeholder': 'Privilege Point Amount'}),
            'round_off': TextInput(attrs={'class': ' number form-control', 'placeholder': 'round_off', 'readonly': ''}),
            'total_outstanding': TextInput(attrs={'class': ' number form-control', 'readonly': 'readonly', 'placeholder': 'Total Outstanding'}),

        }

        error_messages = {
            'sale_date': {
                'required': _("Date field is required."),
            },
            'customer': {
                'required': _("Customer field is required."),
            },
            'subtotal': {
                'required': _("Subtotal field is required."),
            },
            'total': {
                'required': _("Total field is required."),
            }
        }

        labels = {
            'add_gst': 'Add GST',
            'transporter': 'Transporter Vehicle Number',
            'discount_rate': 'Discount Rate(%)',
            'discount': 'Special Discount Amount',
            'customer_address': 'Shipping Address',
            'sale_prifix': 'Sale Prifix'
        }


class CustomerCreateFromForm(forms.ModelForm):

    class Meta:
        model = Customer
        exclude = ['creator', 'updater','deleted_reason', 'auto_id', 'current_privilege_points',
                   'privilege_points', 'is_deleted', 'user', 'current_balance']

        widgets = {
            'name': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Name'}),
            'email': TextInput(attrs={'class': ' email form-control', 'placeholder': 'Email'}),
            'phone': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Phone'}),
            'address': Textarea(attrs={'class': 'required form-control', 'placeholder': 'Address'}),
            'customer_type': Select(attrs={'class': 'required form-control', 'placeholder': 'Customer Type'}),
            'opening_balance': TextInput(attrs={'class': 'form-control', 'placeholder': ' Opening Balance'}),
            'opening_type': Select(attrs={'class': 'required form-control'}),
            'state': Select(attrs={'class': 'form-control', 'placeholder': 'State code'}),
            'district': TextInput(attrs={'class': 'form-control', 'placeholder': 'District'}),
            'country': TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),
            'gst_number': TextInput(attrs={'class': 'form-control', 'placeholder': 'Gst Number'}),

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


class SaleReturnForm(forms.ModelForm):

    class Meta:
        model = SaleReturn
        exclude = ['warehouse','creator', 'updater','deleted_reason', 'user', 'a_id',
                   'auto_id', 'amount_returned', 'returnable_amount']
        widgets = {
            'customer': autocomplete.ModelSelect2(url='customers:customer_autocomplete', attrs={'data-placeholder': 'Customer', 'data-minimum-input-length': 0},),
            'sale': autocomplete.ModelSelect2(url='sales:sale_autocomplete', forward=["customer"], attrs={'data-placeholder': 'Sale', 'data-minimum-input-length': 0, 'data-autocomplete-light-forward': 'customer'},),
            'time': TextInput(attrs={'placeholder': 'Enter Time', 'class': 'date-picker-dd required'}),
        }
        labels = {
            'sale': 'Against Sale Invoice',
        }


class SaleReturnItemForm(forms.ModelForm):

    class Meta:
        model = SaleReturnItem
        exclude = ['creator', 'updater','deleted_reason', 'user', 'sale_return', 'cost']
        widgets = {
            'product': autocomplete.ModelSelect2(url='products:product_autocomplete', attrs={'data-placeholder': 'Product', 'data-minimum-input-length': 0},),
            'qty': TextInput(attrs={'class': 'required form-control number qty', 'placeholder': 'Quantity'}),
            'cost': TextInput(attrs={'class': 'required form-control number', 'placeholder': 'Cost'}),
            'price': TextInput(attrs={'class': 'required form-control number', 'placeholder': 'Price'}),
        }



class SaleVoucherForm(forms.ModelForm):
    class Meta:
        model = ReceiptVoucher
        fields = [
            'cheque_number',
            'transfer_number',
            'draft_number',
            'cheque_date',
            'transfer_date',
            'draft_date',
            'transfer_type',
            'bank',
            # 'sub_ledger's.debter,
            # 'has_transferred',
        ]

        widgets = {
            'bank': autocomplete.ModelSelect2(url='finance:bankaccount_autocomplete', attrs={'data-placeholder': 'Select Bank', 'data-minimum-input-length': 0},),
            'transfer_type': Select(attrs={'class': 'selectpicker required form-control sale_id_class', 'placeholder': 'Type'}),

            'draft_number': TextInput(attrs={'class': ' form-control subtotal_class', 'placeholder': 'Draft No'}),
            'cheque_number': TextInput(attrs={'class': ' form-control subtotal_class', 'placeholder': 'Cheque No'}),
            'draft_date': TextInput(attrs={'class': ' date-picker-dd form-control', 'placeholder': 'Draft Date'}),
            'cheque_date': TextInput(attrs={'class': ' date-picker-dd form-control', 'placeholder': 'Cheque Date'}),
            'transfer_number': TextInput(attrs={'class': ' form-control subtotal_class', 'placeholder': 'Transaction No'}),
            'transfer_date': TextInput(attrs={'class': ' date-picker-dd form-control', 'placeholder': 'Transaction Date'}),
        }

        error_messages = {
            'title': {
                'required': _("Title field is required."),
            },
            'transfer_type': {
                'required': _("Type field is required."),
            },
        }

        labels = {
            'voucher_date': "Date"
        }

