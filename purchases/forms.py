from django import forms
from django.forms.widgets import TextInput, Textarea, Select, FileInput
from django.utils.translation import ugettext_lazy as _
from dal import autocomplete
from finance.models import PaymentVoucher
from purchases.models import Purchase, PurchaseItem, PurchaseOrder, PurchaseOrderItem, PurchaseReturn, PurchaseReturnItem
# from general.models import Batch


class PurchaseForm(forms.ModelForm):

    class Meta:
        model = Purchase
        fields = ["purchase_id","purchase_prifix","warehouse", "date", 'supplier', 'balance', 'subtotal', 'paid', 'discount',
                  'add_gst', 'product_total', 'round_off']
        widgets = {
            'warehouse': autocomplete.ModelSelect2(url='warehouses:warehouse_autocomplete', attrs={'class': 'required', 'data-placeholder': 'Warehouse', 'data-minimum-input-length': 0},),
            'purchase_id': TextInput(attrs={'class': 'required form-control','readonly': 'readonly','placeholder': 'Purchase Id'}),
            'purchase_prifix': Select(attrs={'class': 'required form-control'}),

            'product_total': TextInput(attrs={'class': 'form-control', 'readonly': 'readonly', 'placeholder': 'Product Subtotal'}),
            'discount': TextInput(attrs={'class': 'form-control ', 'placeholder': 'Discount'}),
            'date': TextInput(attrs={'class': 'required form-control date-picker-dd', 'placeholder': 'Date'}),
            'supplier': autocomplete.ModelSelect2(url='suppliers:supplier_autocomplete', attrs={'data-placeholder': 'Supplier', 'data-minimum-input-length': 0},),
            'round_off': TextInput(attrs={'class': ' form-control ', 'placeholder': 'Round off', 'readonly': ''}),
            'subtotal': TextInput(attrs={'class': 'required form-control ', 'placeholder': 'Total Amount', 'id': 'subtotal', 'readonly': 'readonly'}),
            'balance': TextInput(attrs={'class': 'form-control ', 'placeholder': 'Balance', 'id': 'balance', 'readonly': 'readonly'}),
            'paid': TextInput(attrs={'class': ' form-control ', 'placeholder': 'Paid'}),
        }
        error_messages = {
            'date': {
                'required': _("Date field is required."),
            },
            'supplier': {
                'required': _("Supplier field is required."),
            },
            'subtotal': {
                'required': _("Subtotal field is required."),
            },
            'paid': {
                'required': _("paid field is required."),
            },
            'balance': {
                'required': _("Balance field is required."),
            },
        },
        labels = {
            'due_days': 'Due days',
            'other_charge': 'Other Charges',
            'product_total': 'Product Total',
            'discount': 'Discount(%)',
            'purchase_prifix': 'Purchase Prifix'

        }


class PurchaseItemForm(forms.ModelForm):

    class Meta:
        model = PurchaseItem
        exclude = [
            'gross_amount',
            'purchase',
            'return_qty'
        ]

        widgets = {
            'product_variant': autocomplete.ModelSelect2(url='products:product_variant_autocomplete', forward=["warehouse"], attrs={'data-placeholder': 'Product', 'data-minimum-input-length': 0},),
            'batch': Select(attrs={"class": "required selectpicker form-control", "data-live-search": "true"}),
            'batch_number': TextInput(attrs={'class': 'form-control', 'placeholder': 'Batch number', }),
            'hsn': TextInput(attrs={'class': 'form-control disabled', 'placeholder': 'HSN', 'readonly': ''}),
            'quantity': TextInput(attrs={'class': 'form-control ', 'placeholder': 'QTY'}),
            'mrp': TextInput(attrs={'class': 'form-control number', 'placeholder': 'MRP'}),
            'expire_date': TextInput(attrs={'type': 'date', 'class': 'form-control date-picker-1', 'placeholder': 'MM/DD/YYYY', }),
            'manufacturing_date': TextInput(attrs={'type': 'date', 'class': 'form-control date-picker-1', 'placeholder': 'MM/DD/YYYY'}),

            'amount': TextInput(attrs={'class': 'form-control ', 'placeholder': 'Rate'}),
            'net_rate': TextInput(attrs={'class': 'form-control ', 'placeholder': 'Net Amount', 'readonly': ''}),
            'discount': TextInput(attrs={'class': 'form-control '}),
            'tax_amount': TextInput(attrs={'class': 'form-control disabled', 'placeholder': 'Tax Amount', 'readonly': ''}),
            'tax': TextInput(attrs={'class': 'form-control ', 'placeholder': 'Tax', 'readonly': ''}),
            'cgst_amount': TextInput(attrs={'class': 'form-control disabled', 'placeholder': 'Tax Amount', 'readonly': ''}),
            'sgst_amount': TextInput(attrs={'class': 'form-control disabled', 'placeholder': 'Tax Amount', 'readonly': ''}),
            'igst_amount': TextInput(attrs={'class': 'form-control ', 'placeholder': 'Tax Amount', 'readonly': ''}),
            'retail_price': TextInput(attrs={'class': 'form-control', 'placeholder': 'Retail Price'}),
            'whole_sale_price': TextInput(attrs={'class': 'form-control', 'placeholder': 'Whole Sale Price'}),
            'total': TextInput(attrs={'class': 'form-control ', 'placeholder': 'Total Amount', 'style': 'width:4cm', }),
        }
        error_messages = {
            'product': {
                'required': _("Product field is required."),
            },
            'quantity': {
                'required': _("Quantity before field is required."),
            }, 'amount': {
                'required': _("Rate field is required."),
            }, 'tax': {
                'required': _("Tax field is required."),
            }, 'tax_amount': {
                'required': _("Tax Amount field is required."),
            },
            'gross_amount': {
                'required': _("Gross Amount field is required."),
            },
        }


class PurchaseReturnForm(forms.ModelForm):
    class Meta:
        model = PurchaseReturn
        exclude = ['creator', 'updater','deleted_reason', 'auto_id', 'is_deleted',
                   'total', 'site', 'a_id', 'amount_returned', 'total']
        widgets = {
            # 'vendor': autocomplete.ModelSelect2(url='vendors:vendor_autocomplete', attrs={'data-placeholder': 'Vendor', 'data-minimum-input-length': 0},),
            'supplier': autocomplete.ModelSelect2(url='suppliers:supplier_autocomplete', attrs={'data-placeholder': 'Supplier', 'data-minimum-input-length': 0},),

            'date': TextInput(attrs={'class': 'required date-picker-dd form-control', 'readonly': '', 'placeholder': 'Date'}),
            'purchase': autocomplete.ModelSelect2(url='purchases:purchase_autocomplete', forward=["supplier"], attrs={'data-placeholder': 'Purchase', 'data-minimum-input-length': 0, 'data-autocomplete-light-forward': 'supplier'},),
            'total': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Total'}),
            'amount_returned': TextInput(attrs={'class': 'required form-control', 'readonly': '', 'value': 0, 'placeholder': 'Amount'}),
        }

        error_messages = {
            'date': {
                'required': _("Date field is required."),
            },
            'supplier': {
                'required': _("Supplier field is required."),
            },
            'total': {
                'required': _("Total field is required."),
            }
        }
        labels = {
            'purchase': 'Against Purchase Invoice',
        }


class PurchaseReturnItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseReturnItem
        exclude = ['total', 'is_deleted', 'return_qty']
        widgets = {
            'product': Select(attrs={'class': 'required form-control selectpicker', 'placeholder': 'Product'}),
            'quantity': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Quantity'}),
            'amount': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Amount'}),
        }
        error_messages = {
            'product': {
                'required': _("Product field is required."),
            },
            'quantity': {
                'required': _("Quantity field is required."),
            },
            'amount': {
                'required': _("Amount field is required."),
            }
        }


class PurchaseVoucherForm(forms.ModelForm):
    class Meta:
        model = PaymentVoucher
        fields = [
            'cheque_number',
            'transfer_number',
            'draft_number',
            'cheque_date',
            'transfer_date',
            'draft_date',
            'transfer_type',
            'bank',
            'sub_ledger',
        ]

        widgets = {
            'bank': autocomplete.ModelSelect2(url='finance:bankaccount_autocomplete', attrs={'data-placeholder': 'Select Bank', 'data-minimum-input-length': 0},),
            'transfer_type': Select(attrs={'class': 'selectpicker required form-control sale_id_class', 'placeholder': 'Type'}),

            'draft_number': TextInput(attrs={'class': ' form-control subtotal_class', 'placeholder': 'Draft No'}),
            'cheque_number': TextInput(attrs={'class': ' form-control subtotal_class', 'placeholder': 'Cheque No'}),
            'draft_date': TextInput(attrs={'class': ' date-picker-dd form-control', 'placeholder': 'Draft Date'}),
            'cheque_date': TextInput(attrs={'class': ' date-picker-dd form-control', 'placeholder': 'Cheque Date'}),
            'transfer_number': TextInput(attrs={'class': ' form-control subtotal_class', 'placeholder': 'Transfer No'}),
            'transfer_date': TextInput(attrs={'class': ' date-picker-dd form-control', 'placeholder': 'Transfer Date'}),
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

class PurchaseOrderForm(forms.ModelForm):

    class Meta:
        model = PurchaseOrder
        fields = ["warehouse", "date", 'supplier',  'subtotal',  'discount',
                   'add_gst','product_total', 'user', 'round_off']
        widgets = {
            'warehouse': autocomplete.ModelSelect2(url='warehouses:warehouse_autocomplete', attrs={'class': 'required', 'data-placeholder': 'Warehouse', 'data-minimum-input-length': 0},),
            # 'order_id': TextInput(attrs={'class': 'required form-control','readonly': 'readonly','placeholder': 'Purchase Id'}),
            # 'purchase_prifix': Select(attrs={'class': 'required form-control'}),

            'product_total': TextInput(attrs={'class': 'form-control', 'readonly': 'readonly', 'placeholder': 'Product Subtotal'}),
            'discount': TextInput(attrs={'class': 'form-control ', 'placeholder': 'Discount'}),
            'date': TextInput(attrs={'class': 'required form-control date-picker-dd', 'placeholder': 'Date'}),
            'supplier': autocomplete.ModelSelect2(url='suppliers:supplier_autocomplete', attrs={'data-placeholder': 'Supplier', 'data-minimum-input-length': 0},),
            'round_off': TextInput(attrs={'class': ' form-control ', 'placeholder': 'Round off', 'readonly': ''}),
            'subtotal': TextInput(attrs={'class': 'required form-control ', 'placeholder': 'Total Amount', 'id': 'subtotal', 'readonly': 'readonly'}),
            # 'paid': TextInput(attrs={'class': ' form-control ', 'placeholder': 'Paid'}),
            # 'balance': TextInput(attrs={'class': 'form-control ', 'placeholder': 'Balance', 'id': 'balance', 'readonly': 'readonly'}),
        }
        error_messages = {
            'date': {
                'required': _("Date field is required."),
            },
            'supplier': {
                'required': _("Supplier field is required."),
            },
            'subtotal': {
                'required': _("Subtotal field is required."),
            },
            'paid': {
                'required': _("paid field is required."),
            },
            'balance': {
                'required': _("Balance field is required."),
            },
        },
        labels = {
            'due_days': 'Due days',
            'other_charge': 'Other Charges',
            'product_total': 'Product Total',
            'discount': 'Discount(%)',
            'purchase_prifix': 'Purchase Prifix'

        }


class PurchaseOrderItemForm(forms.ModelForm):

    class Meta:
        model = PurchaseOrderItem
        exclude = [
            'gross_amount',
            'purchase_order',
            # 'return_qty'
        ]

        widgets = {
            'product_variant': autocomplete.ModelSelect2(url='products:product_variant_autocomplete', forward=["warehouse"], attrs={'data-placeholder': 'Product', 'data-minimum-input-length': 0},),
            'batch': Select(attrs={"class": "required selectpicker form-control", "data-live-search": "true"}),
            'batch_number': TextInput(attrs={'class': 'form-control', 'placeholder': 'Batch number', }),
            'hsn': TextInput(attrs={'class': 'form-control disabled', 'placeholder': 'HSN', 'readonly': ''}),
            'quantity': TextInput(attrs={'class': 'form-control ', 'placeholder': 'QTY'}),
            'mrp': TextInput(attrs={'class': 'form-control number', 'placeholder': 'MRP'}),
            'expire_date': TextInput(attrs={'type': 'date', 'class': 'form-control date-picker-1', 'placeholder': 'MM/DD/YYYY', }),
            'manufacturing_date': TextInput(attrs={'type': 'date', 'class': 'form-control date-picker-1', 'placeholder': 'MM/DD/YYYY'}),

            'amount': TextInput(attrs={'class': 'form-control ', 'placeholder': 'Rate'}),
            'net_rate': TextInput(attrs={'class': 'form-control ', 'placeholder': 'Net Amount', 'readonly': ''}),
            'discount': TextInput(attrs={'class': 'form-control '}),
            'tax_amount': TextInput(attrs={'class': 'form-control disabled', 'placeholder': 'Tax Amount', 'readonly': ''}),
            'tax': TextInput(attrs={'class': 'form-control ', 'placeholder': 'Tax', 'readonly': ''}),
            'cgst_amount': TextInput(attrs={'class': 'form-control disabled', 'placeholder': 'Tax Amount', 'readonly': ''}),
            'sgst_amount': TextInput(attrs={'class': 'form-control disabled', 'placeholder': 'Tax Amount', 'readonly': ''}),
            'igst_amount': TextInput(attrs={'class': 'form-control ', 'placeholder': 'Tax Amount', 'readonly': ''}),
            'retail_price': TextInput(attrs={'class': 'form-control', 'placeholder': 'Retail Price'}),
            'whole_sale_price': TextInput(attrs={'class': 'form-control', 'placeholder': 'Whole Sale Price'}),
            'total': TextInput(attrs={'class': 'form-control ', 'placeholder': 'Total Amount', 'style': 'width:4cm', }),
        }
        error_messages = {
            'product': {
                'required': _("Product field is required."),
            },
            'quantity': {
                'required': _("Quantity before field is required."),
            }, 'amount': {
                'required': _("Rate field is required."),
            }, 'tax': {
                'required': _("Tax field is required."),
            }, 'tax_amount': {
                'required': _("Tax Amount field is required."),
            },
            'gross_amount': {
                'required': _("Gross Amount field is required."),
            },
        }
class PurchaseOrderItemEditForm(forms.ModelForm):
    mrp = forms.CharField(widget= TextInput(attrs={'class': 'form-control number','value':0,'placeholder' : 'Mrp',}),required=False)
    price = forms.CharField(widget= TextInput(attrs={'class': 'form-control number','value':0,'placeholder' : 'Price',}),required=False)

    class Meta:
        model = PurchaseOrderItem
        fields = [
            "discount",
            "quantity",
            "amount",
            'tax',
            'tax_amount',
            'cgst_amount',
            'sgst_amount',
            'total',
            'net_rate',
            'product_variant',
            'batch',
            'expire_date',
            'add_new_batch',
            'is_purchased',
            'batch_number'
        ]

        widgets = {
            'batch': Select(attrs={"class":"required selectpicker form-control","data-live-search":"true"}),
            'product_variant': Select(attrs={"class":"selectpicker form-control","data-live-search":"true"}),

            'batch_number': TextInput(attrs={'class': 'form-control','placeholder' : 'Batch number',}),
            'expire_date': TextInput(attrs={'type':'date','class': 'form-control date-picker-1','placeholder' : 'MM/DD/YYYY',}),
            'quantity': TextInput(attrs={'class': 'form-control ','placeholder' : 'QTY'}),
            'amount': TextInput(attrs={'class': 'form-control ','placeholder' : 'Rate'}),
            'hsn': TextInput(attrs={'class': 'form-control disabled','placeholder' : 'HSN','readonly':''}),
            'tax': TextInput(attrs={'class': 'form-control ','placeholder' : 'Tax','readonly':''}),
            'discount': TextInput(attrs={'class': 'form-control '}),
            'net_rate': TextInput(attrs={'class': 'form-control ','placeholder' : 'Net Amount','readonly':''}),
            'tax_amount': TextInput(attrs={'class': 'form-control disabled','placeholder' : 'Tax Amount','readonly':''}),
            'cgst_amount': TextInput(attrs={'class': 'form-control disabled','placeholder' : 'Tax Amount','readonly':''}),
            'sgst_amount': TextInput(attrs={'class': 'form-control disabled','placeholder' : 'Tax Amount','readonly':''}),
            'sgst_amount': TextInput(attrs={'class': 'form-control disabled','placeholder' : 'Tax Amount','readonly':''}),
            'cess_amount': TextInput(attrs={'class': 'form-control disabled','placeholder' : 'CESS Amount','readonly':''}),
            'total': TextInput(attrs={'class': 'form-control ','placeholder' : 'Total Amount','style':'width:4cm',}),
        }

        error_messages = {
            'product' : {
                'required' : _("Product field is required."),
            },
            'quantity' : {
                'required' : _("Quantity before field is required."),
            },'amount' : {
                'required' : _("Rate field is required."),
            },'tax' : {
                'required' : _("Tax field is required."),
            },'tax_amount' : {
                'required' : _("Tax Amount field is required."),
            },
            'gross_amount' : {
                'required' : _("Gross Amount field is required."),
            },
        }

