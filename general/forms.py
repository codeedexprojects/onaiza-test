
from django import forms
from django.forms.widgets import TextInput, Textarea, CheckboxInput, Select, FileInput
from general.models import InvoiceDesign
from general.models import StockUpdateItem,StockUpdate
from products.models import ProductVariant
from general.models import DamagedProducts, Batch, StockTransfer, StockTransferItem
from dal import autocomplete
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError


class DamagedProductsForm(forms.ModelForm):

    class Meta:
        model = DamagedProducts
        exclude = ['creator', 'updater','deleted_reason', 'auto_id', 'is_deleted']
        widgets = {
            'quantity': TextInput(attrs={'class': ' required form-control', 'placeholder': 'Quantity'}),
            'date': TextInput(attrs={'class': 'required date-picker-dd form-control', 'placeholder': ' Date'}),
            'amount': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Amount'}),
            'description': Textarea(attrs={'class': ' required form-control', 'placeholder': 'Description'}),
            'product_variant': autocomplete.ModelSelect2(url='products:product_variant_autocomplete', forward=["warehouse"], attrs={'data-placeholder': 'Product Variant', 'class': 'required', 'data-minimum-input-length': 0}),
            'batch': Select(attrs={"class": " selectpicker product form-control", "data-live-search": "true"}),
            'warehouse': autocomplete.ModelSelect2(url='warehouses:warehouse_autocomplete', attrs={'class': 'required', 'data-placeholder': 'Warehouse', 'data-minimum-input-length': 0},),

        }

        error_messages = {
            'quantity': {
                'required': _("quantity field is required."),
            },
            'amount': {
                'required': _("amount field is required."),
            },
        }


class StockTransferForm(forms.ModelForm):

    class Meta:
        model = StockTransfer
        exclude = ['creator', 'updater','deleted_reason', 'deleted_reason', 'auto_id', 'is_deleted']
        widgets = {
            'date': TextInput(attrs={'class': 'required date-picker form-control', 'placeholder': 'Date'}),
            'warehouse': autocomplete.ModelSelect2(url='warehouses:warehouse_autocomplete', attrs={'class': 'required', 'data-placeholder': 'Warehouse', 'data-minimum-input-length': 0},),
            'to_warehouse': autocomplete.ModelSelect2(url='warehouses:towarehouse_autocomplete', forward=["warehouse"], attrs={'class': 'required', 'data-placeholder': 'To Warehouse', 'data-minimum-input-length': 0},),
        }

        error_messages = {
            'date': {
                'required': _("deal_date field is required."),
            },
            'warehouse': {
                'required': _("Warehouse field is required."),
            },
            'to_warehouse': {
                'required': _("To Warehouse field is required."),
            },
        }


class StockTransferItemForm(forms.ModelForm):

    class Meta:
        model = StockTransferItem
        exclude = ['creator', 'updater','deleted_reason', 'auto_id',
                   'is_deleted', 'stock_transfer']
        widgets = {
            'quantity': TextInput(attrs={'class': ' required form-control', 'placeholder': 'Quantity'}),
            'product_variant': autocomplete.ModelSelect2(url='products:product_variant_autocomplete', forward=["warehouse"], attrs={'data-placeholder': 'Product Variant', 'class': 'required', 'data-minimum-input-length': 0}),
            'batch': Select(attrs={"class": " selectpicker product form-control", "data-live-search": "true"}),
            'retail_price': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Retail Price'}),
            'whole_sale_price': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Whole Sale Price'}),
            'mrp': TextInput(attrs={'class': 'number required form-control', 'placeholder': 'Maximum Selling Price'}),
            'cost': TextInput(attrs={'class': 'number required form-control', 'placeholder': 'Cost'}),
            'manufacturing_date': TextInput(attrs={'type': 'date', 'class': ' required form-control', 'placeholder': 'Manufacturing Date'}),
            'expire_date': TextInput(attrs={'type': 'date', 'class': ' required form-control', 'placeholder': 'Expiry Date'}),
        }

        error_messages = {
            'quantity': {
                'required': _("quantity field is required."),
            },
            'amount': {
                'required': _("amount field is required."),
            },
        }


class InvoiceDesignForm(forms.ModelForm):

    class Meta:
        model = InvoiceDesign
        exclude = ['creator', 'updater','deleted_reason', 'auto_id', 'is_deleted']
        widgets = {
            'warehouse': autocomplete.ModelSelect2(url='warehouses:warehouse_autocomplete', attrs={'class': 'required', 'data-placeholder': 'Warehouse', 'data-minimum-input-length': 0},),
            'title': TextInput(attrs={'class': 'form-control ', 'placeholder': 'Title'}),
        }

        error_messages = {
            'quantity': {
                'required': _("quantity field is required."),
            },
            'amount': {
                'required': _("amount field is required."),
            },
        }



class StockUpdateForm(forms.ModelForm):

    class Meta:
        model = StockUpdate
        exclude = ['creator','updater','auto_id','is_deleted','a_id', 'deleted_reason', 'update_type']
        widgets = {
            'warehouse': autocomplete.ModelSelect2(url='warehouses:warehouse_autocomplete', attrs={'class': 'required', 'data-placeholder': 'Warehouse', 'data-minimum-input-length': 0},),
            'date': TextInput(attrs={'type':'date','class': 'required date-time-picker form-control','placeholder' : ' Date'}),
            'description': TextInput(attrs={'class': 'required form-control','placeholder' : 'Description'}),
        }


class StockUpdateItemForm(forms.ModelForm):
    class Meta:
        model = StockUpdateItem
        exclude = ['is_deleted', 'taxable_amount', 'stockupdate']
        widgets = {
            'product': autocomplete.ModelSelect2(url='products:product_autocomplete',attrs={'data-placeholder': 'Product','data-minimum-input-length': 0},),
            # 'product': Select(attrs={"class":"product_item required selectpicker product form-control","data-live-search":"true"}),
            # 'product_variant': Select(attrs={"class":"selectpicker form-control","data-live-search":"true"}),
            'product_variant': autocomplete.ModelSelect2(url='products:product_variant_autocomplete', forward=["warehouse"], attrs={'data-placeholder': 'Product', 'data-minimum-input-length': 0},),

            'batch': Select(attrs={"class":"required selectpicker form-control","data-live-search":"true"}),

            'batch_number': TextInput(attrs={'class': 'required form-control','placeholder' : 'batch number','onkeyup':"this.value = this.value.toUpperCase();"}),
            'stock': TextInput(attrs={'class': 'required number form-control','placeholder' : 'stock'}),
            'mrp': TextInput(attrs={'class': 'required number form-control','placeholder' : 'mrp'}),
            'retail_price': TextInput(attrs={'class': 'form-control', 'placeholder': 'Retail Price'}),
            'whole_sale_price': TextInput(attrs={'class': 'form-control', 'placeholder': 'Whole Sale Price'}),
            'cost': TextInput(attrs={'class': 'required number form-control','placeholder' : 'cost'}),
            'manufacturing_date': TextInput(attrs={'type':'date','class': ' required form-control','placeholder' : 'Manufacturing Date'}),
            'expire_date': TextInput(attrs={'type':'date','class': ' required form-control','placeholder' : 'Expiry Date'}),
        }


class StockInwardItemEditForm(forms.ModelForm):
    update_batch_data = forms.BooleanField(widget=CheckboxInput(), required=False)

    class Meta:
        model = StockUpdateItem
        exclude = ['is_deleted', 'taxable_amount', 'stockupdate']
        widgets = {
            # 'product': autocomplete.ModelSelect2(url='products:product_autocomplete',attrs={'data-placeholder': 'Product','data-minimum-input-length': 0},),
            # 'product': Select(attrs={"class":"product_item required selectpicker product form-control","data-live-search":"true"}),
            # 'product_variant': Select(attrs={"class":"selectpicker form-control","data-live-search":"true"}),
            'product_variant': autocomplete.ModelSelect2(url='products:product_variant_autocomplete', forward=["warehouse"], attrs={'data-placeholder': 'Product', 'data-minimum-input-length': 0},),

            'batch': Select(attrs={"class":"required selectpicker form-control","data-live-search":"true"}),

            'batch_number': TextInput(attrs={'class': 'required form-control','placeholder' : 'batch number','onkeyup':"this.value = this.value.toUpperCase();"}),
            'stock': TextInput(attrs={'class': 'required number form-control','placeholder' : 'stock'}),
            'mrp': TextInput(attrs={'class': 'required number form-control','placeholder' : 'mrp'}),
            'retail_price': TextInput(attrs={'class': 'form-control', 'placeholder': 'Retail Price'}),
            'whole_sale_price': TextInput(attrs={'class': 'form-control', 'placeholder': 'Whole Sale Price'}),
            'cost': TextInput(attrs={'class': 'required number form-control','placeholder' : 'cost'}),
            'manufacturing_date': TextInput(attrs={'type':'date','class': ' required form-control','placeholder' : 'Manufacturing Date'}),
            'expire_date': TextInput(attrs={'type':'date','class': ' required form-control','placeholder' : 'Expiry Date'}),
        }


class StockOutWardItemForm(forms.ModelForm):
    class Meta:
        model = StockUpdateItem
        exclude = ['is_deleted','taxable_amount','stockupdate', 'batch_number', 'add_new_batch']
        widgets = {
            # 'product': Select(attrs={"class":"product_item required selectpicker product form-control","data-live-search":"true"}),
            # 'product': autocomplete.ModelSelect2(url='products:product_autocomplete',attrs={'data-placeholder': 'Product','data-minimum-input-length': 0},),
            # 'product_variant': Select(attrs={"class":"selectpicker form-control","data-live-search":"true"}),
            'product_variant': autocomplete.ModelSelect2(url='products:product_variant_autocomplete', forward=["warehouse"], attrs={'data-placeholder': 'Product', 'data-minimum-input-length': 0},),

            'batch':  Select(attrs={"class":"selectpicker form-control","data-live-search":"true"}),
            'stock': TextInput(attrs={'class': 'required number form-control','placeholder' : 'stock'}),

            'mrp': TextInput(attrs={'class': 'required number form-control','placeholder' : 'mrp'}),
            'retail_price': TextInput(attrs={'class': 'form-control', 'placeholder': 'Retail Price'}),
            'whole_sale_price': TextInput(attrs={'class': 'form-control', 'placeholder': 'Whole Sale Price'}),            'cost': TextInput(attrs={'class': 'required number form-control','placeholder' : 'cost'}),
            'manufacturing_date': TextInput(attrs={'type':'date','class': ' required form-control','placeholder' : 'Manufacturing Date'}),
            'expire_date': TextInput(attrs={'type':'date','class': ' required form-control','placeholder' : 'Expiry Date'}),
        }

