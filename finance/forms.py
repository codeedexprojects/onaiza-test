from django import forms
from django.forms.fields import Field
from django.forms.widgets import Select, TextInput, Textarea, CheckboxInput
from django.utils.translation import ugettext_lazy as _
from customers.models import Customer
from delivery_agent.views import delivery_agent
from vendors.models import Vendor
from suppliers.models import Supplier
from delivery_agent.models import DeliveryAgents

from dal import autocomplete
from warehouses.models import Warehouse
from .models import *


class FinancialYearForm(forms.ModelForm):
    class Meta:
        model = FinancialYear
        fields = ['start_date', 'end_date', 'is_active']

        widgets = {
            'start_date': TextInput(attrs={'class': 'required date-picker-dd form-control', 'placeholder': 'Start Date'}),
            'end_date': TextInput(attrs={'class': 'required date-picker-dd form-control', 'placeholder': 'End Date'}),
        }


class InvoicePrefixForm(forms.ModelForm):
    class Meta:
        model = InvoicePrefix
        fields = ['whole_sale', 'retail_sale', 'order','purchase']

        widgets = {
            'whole_sale': TextInput(attrs={'class': 'required form-control subtotal_class', 'placeholder': 'whole Sale'}),
            'retail_sale': TextInput(attrs={'class': 'required form-control subtotal_class', 'placeholder': 'Retail Sale'}),
            'order': TextInput(attrs={'class': 'required form-control subtotal_class', 'placeholder': 'Order'}),
            'purchase': TextInput(attrs={'class': 'required form-control subtotal_class', 'placeholder': 'Purchase'}),
        }

        error_messages = {
            'whole_sale': {
                'required': _("whole_sale field is required."),
            },
            'retail_sale': {
                'required': _("retail_sale field is required."),
            },
        }



class AccountGroupForm(forms.ModelForm):
    class Meta:
        model = AccountGroup
        fields = ['name', 'group_type']

        widgets = {
            'name': TextInput(attrs={'class': 'required form-control subtotal_class', 'placeholder': 'Name'}),
            'group_type': Select(attrs={'class': 'required selectpicker form-control sale_id_class', 'placeholder': 'Type'}),
            # 'code': TextInput(attrs={'class': 'form-control subtotal_class', 'placeholder': 'Code'}),
        }

        error_messages = {
            'name': {
                'required': _("Name field is required."),
            },
            'types': {
                'required': _("Type field is required."),
            },
        }


class BankAccountForm(forms.ModelForm):

    class Meta:
        model = BankAccount
        exclude = ['creator', 'updater','deleted_reason', 'auto_id', 'is_deleted']

        widgets = {
            'warehouse': autocomplete.ModelSelect2(url='warehouses:warehouse_autocomplete', attrs={'class': 'required', 'data-placeholder': 'Warehouse', 'data-minimum-input-length': 0},),
            'bank_name': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Name'}),
            'account_number': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Account number'}),
            'account_holder': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Account holder'}),
            'branch': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Branch'}),
            'ifsc_code': TextInput(attrs={'class': 'required form-control', 'placeholder': 'IFSC'}),
            "opening_balance": TextInput(attrs={"class": "required form-control number", "placeholder": "Enter amount"}),
            'opening_balance_type': Select(attrs={'class': 'required form-control selectpicker'}),
            'account_type': Select(attrs={'class': 'required form-control selectpicker'}),
        }

        error_messages = {
            'bank_name': {
                'required': _("Name field is required."),
            },
            'ifsc_code': {
                'required': _("Ifsc field is required."),
            },
            'branch': {
                'required': _("Branch field is required."),
            },
            'account_type': {
                'required': _("Account Type field is required."),
            },
            'account_number': {
                'required': _("Account No field is required."),
            }
        }


class AccountHeadForm(forms.ModelForm):
    BALANCE_CHOICES = (('debit', 'Debit'),('credit', 'Credit'),)
    opening_balance = forms.DecimalField(widget=forms.TextInput(attrs={'class':'form-control'}))
    opening_balance_type = forms.CharField(widget=forms.Select(choices=BALANCE_CHOICES, attrs={'class':'form-control selectpicker'}))
    warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.filter(is_deleted=False),
        widget=autocomplete.ModelSelect2(url='warehouses:warehouse_autocomplete', attrs={'class': '', 'data-placeholder': 'Warehouse', 'data-minimum-input-length': 0},)
    )

    class Meta:
        model = AccountHead
        fields = ['name', 'account_group']

        widgets = {
            'account_group': autocomplete.ModelSelect2(url='finance:account_group_autocomplete', attrs={'class': 'required', 'data-placeholder': 'Account Group', 'data-minimum-input-length': 0},),
            'name': TextInput(attrs={'class': 'required form-control subtotal_class', 'placeholder': 'Name'}),
            # 'code': TextInput(attrs={'class': 'form-control subtotal_class', 'placeholder': 'Code'}),
        }

        error_messages = {
            'name': {
                'required': _("Name field is required."),
            },
            'account_group': {
                'required': _("Account Group field is required."),
            },
        }


class AccountHeadEditForm(forms.ModelForm):
    BALANCE_CHOICES = (('debit', 'Debit'),('credit', 'Credit'),)
    opening_balance = forms.DecimalField(widget=forms.TextInput(attrs={'class':'form-control'}))
    opening_balance_type = forms.CharField(widget=forms.Select(choices=BALANCE_CHOICES, attrs={'class':'form-control selectpicker'}))
    account_group = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control'}))
    warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.filter(is_deleted=False),
        widget=autocomplete.ModelSelect2(url='warehouses:warehouse_autocomplete', attrs={'class': '', 'data-placeholder': 'Warehouse', 'data-minimum-input-length': 0},)
    )

    class Meta:
        model = AccountHead
        fields = ['name',]

        widgets = {
            'name': TextInput(attrs={'class': 'required form-control subtotal_class', 'readonly': '', 'placeholder': 'Name'}),
        }

        error_messages = {
            'name': {
                'required': _("Name field is required."),
            },
        }


class PaymentVoucherForm(forms.ModelForm):

    customer = forms.ModelChoiceField(
        required=False,
        queryset=Customer.objects.all(),
        widget=autocomplete.ModelSelect2(url='customers:customer_autocomplete', attrs={'class': '', 'data-placeholder': 'Customers', 'data-minimum-input-length': 0},)
    )
    vendor = forms.ModelChoiceField(
        required=False,
        queryset=Vendor.objects.all(),
        widget=autocomplete.ModelSelect2(url='vendors:vendor_autocomplete', attrs={'class': '', 'data-placeholder': 'Vendors', 'data-minimum-input-length': 0},)
    )
    supplier = forms.ModelChoiceField(
        required=False,
        queryset=Supplier.objects.all(),
        widget=autocomplete.ModelSelect2(url='suppliers:supplier_autocomplete', attrs={'class': '', 'data-placeholder': 'Suppliers', 'data-minimum-input-length': 0},)
    )
    delivery_agent = forms.ModelChoiceField(
        required=False,
        queryset=DeliveryAgents.objects.all(),
        widget=autocomplete.ModelSelect2(url='delivery_agent:delivery_agent_autocomplete', attrs={'class': '', 'data-placeholder': 'Suppliers', 'data-minimum-input-length': 0},)
    )
    class Meta:
        model = PaymentVoucher
        fields = [
            'warehouse',
            'account_head',
            'bank',
            'voucher_number',
            'voucher_date',
            'title',
            'description',
            'sub_ledger',
            'amount',
            # 'amount_type',
            'transfer_type',
            'cheque_number',
            'cheque_date',
            'draft_number',
            'draft_date',
            'transfer_number',
            'transfer_date',
        ]

        widgets = {
            'warehouse': autocomplete.ModelSelect2(url='warehouses:warehouse_autocomplete', attrs={'class': 'required', 'data-placeholder': 'Warehouse', 'data-minimum-input-length': 0},),
            'account_head': autocomplete.ModelSelect2(url='finance:account_head_autocomplete', attrs={'data-placeholder': 'Select Account Head', 'data-minimum-input-length': 0},),
            'bank': autocomplete.ModelSelect2(url='finance:bankaccount_autocomplete', attrs={'data-placeholder': 'Select Bank', 'data-minimum-input-length': 0},),
            'voucher_number': TextInput(attrs={'readonly': 'readonly', 'class': 'required form-control', 'placeholder': 'Voucher Number'}),
            'title': TextInput(attrs={'class': 'form-control', 'placeholder': 'Title'}),
            'description': TextInput(attrs={'class': 'form-control', 'placeholder': 'Description'}),
            'sub_ledger': TextInput(attrs={'class': 'form-control', 'placeholder': 'Sub Ledger'}),
            'amount': TextInput(attrs={'class': 'form-control', 'placeholder': 'Amount'}),
            # 'amount_type': Select(attrs={'class': 'selectpicker required form-control sale_id_class', 'placeholder': 'Amount Type'}),
            'transfer_type': Select(attrs={'class': 'selectpicker required form-control sale_id_class', 'placeholder': 'Type'}),
            'cheque_number': TextInput(attrs={'class': ' form-control', 'placeholder': 'Cheque No'}),
            'cheque_date': TextInput(attrs={'class': ' date-picker-dd form-control', 'placeholder': 'Cheque Date'}),
            'draft_number': TextInput(attrs={'class': ' form-control', 'placeholder': 'Draft No'}),
            'draft_date': TextInput(attrs={'class': ' date-picker-dd form-control', 'placeholder': 'Draft Date'}),
            'transfer_number': TextInput(attrs={'class': ' form-control', 'placeholder': 'Transaction No'}),
            'voucher_date': TextInput(attrs={'class': ' date-picker-dd form-control', 'placeholder': 'Voucher Date'}),
            'transfer_date': TextInput(attrs={'class': ' date-picker-dd form-control', 'placeholder': 'Transaction Date'}),
        }

        error_messages = {
            'name': {
                'required': _("Name field is required."),
            },
            'transfer_type': {
                'required': _("Type field is required."),
            },
        }


class ReceiptVoucherForm(forms.ModelForm):
    customer = forms.ModelChoiceField(
        required=False,
        queryset=Customer.objects.all(),
        widget=autocomplete.ModelSelect2(url='customers:customer_autocomplete', attrs={'class': '', 'data-placeholder': 'Customers', 'data-minimum-input-length': 0},)
    )
    vendor = forms.ModelChoiceField(
        required=False,
        queryset=Vendor.objects.all(),
        widget=autocomplete.ModelSelect2(url='vendors:vendor_autocomplete', attrs={'class': '', 'data-placeholder': 'Vendors', 'data-minimum-input-length': 0},)
    )
    supplier = forms.ModelChoiceField(
        required=False,
        queryset=Supplier.objects.all(),
        widget=autocomplete.ModelSelect2(url='suppliers:supplier_autocomplete', attrs={'class': '', 'data-placeholder': 'Suppliers', 'data-minimum-input-length': 0},)
    )
    delivery_agent = forms.ModelChoiceField(
        required=False,
        queryset=DeliveryAgents.objects.all(),
        widget=autocomplete.ModelSelect2(url='delivery_agent:delivery_agent_autocomplete', attrs={'class': '', 'data-placeholder': 'Suppliers', 'data-minimum-input-length': 0},)
    )
    class Meta:
        model = ReceiptVoucher
        fields = [
            'warehouse',
            'account_head',
            'bank',
            'voucher_number',
            'voucher_date',
            'title',
            'description',
            'sub_ledger',
            'amount',
            # 'amount_type',
            'transfer_type',
            'cheque_number',
            'cheque_date',
            'draft_number',
            'draft_date',
            'transfer_number',
            'transfer_date',
        ]

        widgets = {
            'warehouse': autocomplete.ModelSelect2(url='warehouses:warehouse_autocomplete', attrs={'class': 'required', 'data-placeholder': 'Warehouse', 'data-minimum-input-length': 0},),
            'account_head': autocomplete.ModelSelect2(url='finance:account_head_autocomplete', attrs={'data-placeholder': 'Select Account Head', 'data-minimum-input-length': 0},),
            'bank': autocomplete.ModelSelect2(url='finance:bankaccount_autocomplete', attrs={'data-placeholder': 'Select Bank', 'data-minimum-input-length': 0},),
            'voucher_date': TextInput(attrs={'class': ' date-picker-dd form-control', 'placeholder': 'Voucher Date'}),
            'voucher_number': TextInput(attrs={'readonly': 'readonly', 'class': 'required form-control', 'placeholder': 'Voucher Number'}),
            'title': TextInput(attrs={'class': 'form-control', 'placeholder': 'Title'}),
            'description': TextInput(attrs={'class': 'form-control', 'placeholder': 'Description'}),
            'sub_ledger': TextInput(attrs={'class': 'form-control', 'placeholder': 'Sub Ledger'}),
            'amount': TextInput(attrs={'class': 'form-control', 'placeholder': 'Amount'}),
            'amount_type': Select(attrs={'class': 'selectpicker required form-control sale_id_class', 'placeholder': 'Amount Type'}),
            'transfer_type': Select(attrs={'class': 'selectpicker required form-control sale_id_class', 'placeholder': 'Type'}),
            'cheque_number': TextInput(attrs={'class': ' form-control', 'placeholder': 'Cheque No'}),
            'cheque_date': TextInput(attrs={'class': ' date-picker-dd form-control', 'placeholder': 'Cheque Date'}),
            'draft_number': TextInput(attrs={'class': ' form-control', 'placeholder': 'Draft No'}),
            'draft_date': TextInput(attrs={'class': ' date-picker-dd form-control', 'placeholder': 'Draft Date'}),
            'transfer_number': TextInput(attrs={'class': ' form-control', 'placeholder': 'Transaction No'}),
            'transfer_date': TextInput(attrs={'class': ' date-picker-dd form-control', 'placeholder': 'Transaction Date'}),
        }

        error_messages = {
            'name': {
                'required': _("Name field is required."),
            },
            'transfer_type': {
                'required': _("Type field is required."),
            },
        }



class JournalVoucherForm(forms.ModelForm):

    class Meta:
        model = JournalVoucher
        fields = ['voucher_date','voucher_number', 'title', 'description', 'sub_ledger']

        widgets = {
            'voucher_date': TextInput(attrs={'class': ' date-picker-dd form-control', 'placeholder': 'Voucher Date'}),
            'voucher_number': TextInput(attrs={'class': 'form-control', 'placeholder': 'Voucher Number', 'required': 'required', 'autocomplete': 'off'}),
            'title': TextInput(attrs={'class': 'form-control', 'placeholder': 'Title', 'autocomplete': 'off'}),
            'description': TextInput(attrs={'class': 'form-control', 'placeholder': 'Description', 'autocomplete': 'off'}),
            'sub_ledger': TextInput(attrs={'class': 'form-control', 'placeholder': 'Sub Ledger'}),
            # 'debit_amount': TextInput(attrs={'class': 'form-control', 'placeholder': 'Debit Amount'}),
            # 'credit_amount': TextInput(attrs={'class': 'form-control', 'placeholder': 'Credit Amount'}),

        }

        error_messages = {
            'voucher_date': {
                'required': _("Voucher date field is required."),
            }
        }


class JournalVoucherItemForm(forms.ModelForm):

    class Meta:
        model = JournalVoucherItem
        fields = ['account_head','warehouse','sub_ledger', 'amount', 'amount_type']
        widgets = {
            'account_head': autocomplete.ModelSelect2(url='finance:account_head_autocomplete', attrs={'data-placeholder': 'Select Account Head', 'data-minimum-input-length': 0},),
            'warehouse': autocomplete.ModelSelect2(url='warehouses:warehouse_autocomplete', attrs={'class': 'required', 'data-placeholder': 'Warehouse', 'data-minimum-input-length': 0},),

            # 'sub_ledger': Select(attrs={'class': 'selectpicker form-control'}),
            'sub_ledger': TextInput(attrs={'class': 'form-control', 'placeholder': 'Sub Ledger'}),
            'amount': TextInput(attrs={'class': 'form-control', 'placeholder': 'Amount', 'required': 'required', 'autocomplete': 'off'}),
            'amount_type': Select(attrs={'class': 'selectpicker required form-control'}),
        }
        error_messages = {
            'account_head': {
                'required': _("Account Head field is required."),
            }
        }


class CreditNoteVoucherForm(forms.ModelForm):
    class Meta:
        model = CreditNoteVoucher
        fields = [
            # 'warehouse',
            'sale_return',
            'customer',
            'bank',
            'voucher_number',
            'voucher_date',
            'title',
            'description',
            'amount',
            'transfer_type',
            'cheque_number',
            'cheque_date',
            'draft_number',
            'draft_date',
        ]

        widgets = {
            # 'warehouse': autocomplete.ModelSelect2(url='warehouses:warehouse_autocomplete', attrs={'class': 'required', 'data-placeholder': 'Warehouse', 'data-minimum-input-length': 0},),
            'sale_return': autocomplete.ModelSelect2(url='sales:sale_return_autocomplete', attrs={'class': 'required', 'data-placeholder': 'Sales Return', 'data-minimum-input-length': 0},forward=["customer"]),
            'customer': autocomplete.ModelSelect2(url='customers:customer_autocomplete',attrs={'data-placeholder': 'Customer','data-minimum-input-length': 0},),
            'bank': autocomplete.ModelSelect2(url='finance:bankaccount_autocomplete', attrs={'data-placeholder': 'Select Bank', 'data-minimum-input-length': 0},),
            'voucher_date': TextInput(attrs={'class': ' date-picker-dd form-control', 'placeholder': 'Voucher Date'}),
            'voucher_number': TextInput(attrs={'readonly': 'readonly', 'class': 'required form-control ', 'placeholder': 'Voucher Number'}),
            'title': TextInput(attrs={'class': 'form-control ', 'placeholder': 'Title'}),
            'description': TextInput(attrs={'class': 'form-control ', 'placeholder': 'Description'}),
            'amount': TextInput(attrs={'class': 'form-control', 'placeholder': 'Amount'}),
            'transfer_type': Select(attrs={'class': 'selectpicker form-control sale_id_class', 'placeholder': 'Type'}),
            'cheque_number': TextInput(attrs={'class': ' form-control ', 'placeholder': 'Cheque No'}),
            'cheque_date': TextInput(attrs={'class': ' date-picker-dd form-control', 'placeholder': 'Cheque Date'}),
            'draft_number': TextInput(attrs={'class': ' form-control ', 'placeholder': 'Draft No'}),
            'draft_date': TextInput(attrs={'class': ' date-picker-dd form-control', 'placeholder': 'Draft Date'}),

         }

        error_messages = {
            'transfer_type': {
                'required': _("Type field is required."),
            },
        }

        labels = {
            'amount': "Returned Amount",
        }


class DebitNoteVoucherForm(forms.ModelForm):
    class Meta:
        model = DebitNoteVoucher
        fields = [
            # 'warehouse',
            'purchase_return',
            'supplier',
            'bank',
            'voucher_number',
            'voucher_date',
            'title',
            'description',
            'amount',
            'transfer_type',
            'cheque_number',
            'cheque_date',
            'draft_number',
            'draft_date',
        ]

        widgets = {
            # 'warehouse': autocomplete.ModelSelect2(url='warehouses:warehouse_autocomplete', attrs={'class': 'required', 'data-placeholder': 'Warehouse', 'data-minimum-input-length': 0},),
            'purchase_return': autocomplete.ModelSelect2(url='purchases:purchase_return_autocomplete', attrs={'class': 'required', 'data-placeholder': 'Sales Return', 'data-minimum-input-length': 0},forward=["supplier"],),
            'supplier': autocomplete.ModelSelect2(url='suppliers:supplier_autocomplete',attrs={'data-placeholder': 'Supplier','data-minimum-input-length': 0},),
            'bank': autocomplete.ModelSelect2(url='finance:bankaccount_autocomplete', attrs={'data-placeholder': 'Select Bank', 'data-minimum-input-length': 0},),
            'voucher_date': TextInput(attrs={'class': ' date-picker-dd form-control', 'placeholder': 'Voucher Date'}),
            'voucher_number': TextInput(attrs={'readonly': 'readonly', 'class': 'required form-control ', 'placeholder': 'Voucher Number'}),
            'title': TextInput(attrs={'class': 'form-control ', 'placeholder': 'Title'}),
            'description': TextInput(attrs={'class': 'form-control ', 'placeholder': 'Description'}),
            'amount': TextInput(attrs={'class': 'form-control', 'placeholder': 'Amount'}),
            'transfer_type': Select(attrs={'class': 'selectpicker form-control sale_id_class', 'placeholder': 'Type'}),
            'cheque_number': TextInput(attrs={'class': ' form-control ', 'placeholder': 'Cheque No'}),
            'cheque_date': TextInput(attrs={'class': ' date-picker-dd form-control', 'placeholder': 'Cheque Date'}),
            'draft_number': TextInput(attrs={'class': ' form-control ', 'placeholder': 'Draft No'}),
            'draft_date': TextInput(attrs={'class': ' date-picker-dd form-control', 'placeholder': 'Draft Date'}),

         }

        error_messages = {
            'transfer_type': {
                'required': _("Type field is required."),
            },
        }

        labels = {
            'amount': "Returned Amount",
        }

