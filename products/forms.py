from django import forms
from django.forms.widgets import TextInput, Textarea, HiddenInput, Select, FileInput
from products.models import Category, UnitOfMeasurement, SubCategory, Unit, Brand, HsnCodes, Product, ProductImages, ProductVariant
from dal import autocomplete
from general.models import Batch
from warehouses.models import Warehouse
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError


CATEGORY = (
    ('all', 'All'),
    ('category', 'Category'),
)

class ProductBarcodeForm(forms.Form):
    unit = forms.IntegerField(widget=forms.TextInput(attrs={"placeholder":"Number","class" : 'form-control required'}))
    skip_row = forms.IntegerField(widget=forms.TextInput(attrs={"placeholder":"Number","class" : ' form-control required'}))
    product_variant = forms.ModelChoiceField(queryset=Product.objects.filter(is_deleted=False), empty_label=None,widget=autocomplete.ModelSelect2(url='products:product_variant_autocomplete',attrs={'data-placeholder': 'Product Variant','data-minimum-input-length': 0}) )
    batch = forms.ModelChoiceField(queryset=Batch.objects.none(), widget=Select(attrs={'class': 'form-control', 'required':''}))
    warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.filter(is_deleted=False), widget=autocomplete.ModelSelect2(url='warehouses:warehouse_autocomplete', attrs={'data-placeholder': 'Warehouse', 'data-minimum-input-length': 0}) )
    best_before = forms.IntegerField(widget=forms.TextInput(attrs={"placeholder":"Number","class": 'form-control'}))
    expiry_date = forms.DateField(widget=forms.TextInput(attrs={"placeholder":"Date datepicker","class": 'form-control'}))


class CategoryForm(forms.ModelForm):

    class Meta:
        model = Category
        exclude = ['creator', 'updater','deleted_reason', 'auto_id', 'is_deleted', 'is_admin_approved']
        widgets = {
            'name': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Name'}),
            'malayalam_name': TextInput(attrs={'class': 'required form-control', 'placeholder': 'മലയാളം പേര് '}),
        }

        error_messages = {
            'name': {
                'required': _("Name field is required."),
            },
            'malayalam_name': {
                'required': _("Malayalam name field is required."),
            }
        }


class UnitOfMeasurementForm(forms.ModelForm):

    class Meta:
        model = UnitOfMeasurement
        # exclude = ['creator', 'updater','deleted_reason', 'auto_id', 'is_deleted']
        fields = ['unit_of_measurement']
        widgets = {
            'unit_of_measurement': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Unit Measurement'}),
        }
        error_messages = {
            'unit_of_measurement': {
                'required': _("Unit of Measurement field is required."),
            }
        }


class SubCategoryForm(forms.ModelForm):

    class Meta:
        model = SubCategory
        exclude = ['creator', 'updater','deleted_reason', 'auto_id', 'is_deleted', 'is_admin_approved']
        widgets = {
            'name': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Name'}),
            'category': autocomplete.ModelSelect2(url='products:category_autocomplete', attrs={'data-placeholder': 'Category', 'class': 'required', 'data-minimum-input-length': 0}),
            'malayalam_name': TextInput(attrs={'class': 'required form-control', 'placeholder': 'മലയാളം പേര് '}),
        }

        error_messages = {
            'name': {
                'required': _("Name field is required."),
            },
            'category': {
                'required': _("Category field is required."),
            },
        }


class UnitForm(forms.ModelForm):

    class Meta:
        model = Unit
        # exclude = ['creator', 'updater','deleted_reason', 'auto_id', 'is_deleted']
        fields = ['unit', 'unit_of_measurement']
        widgets = {
            'unit': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Unit'}),
            'unit_of_measurement': autocomplete.ModelSelect2(url='products:unit_measurement_autocomplete', attrs={'data-placeholder': 'Unit Measurement', 'class': 'required', 'data-minimum-input-length': 0}),
        }

        error_messages = {
            'unit': {
                'required': _("Unit field is required."),
            },
            'unit_of_measurement': {
                'required': _("Unit Measurement field is required."),
            },
        }


class BrandForm(forms.ModelForm):

    class Meta:
        model = Brand
        exclude = ['creator', 'updater','deleted_reason', 'auto_id', 'is_deleted', 'is_admin_approved']
        widgets = {
            'name': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Name'}),
            'malayalam_name': TextInput(attrs={'class': 'form-control', 'placeholder': 'മലയാളം പേര് '}),
        }
        error_messages = {
            'name': {
                'required': _("Name field is required."),
            }

        }


class HsnCodesForm(forms.ModelForm):
    class Meta:
        model = HsnCodes
        fields = ["name", "description", "hsn_number", "igst_rate",
                  'sgst_rate', 'cgst_rate', 'unit']
        widgets = {
            'name': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Name'}),
            'description': TextInput(attrs={'class': 'form-control', 'placeholder': 'Description'}),
            'hsn_number': TextInput(attrs={'class': 'required form-control', 'placeholder': 'HSN number'}),
            'sgst_rate': TextInput(attrs={'class': 'required form-control ', 'placeholder': 'SGST rate'}),
            'cgst_rate': TextInput(attrs={'class': 'required form-control ', 'placeholder': 'CGST rate'}),
            'igst_rate': TextInput(attrs={'class': 'required form-control ', 'placeholder': 'IGST rate'}),
            'unit': autocomplete.ModelSelect2(url='products:unit_autocomplete', attrs={'data-placeholder': 'Unit', 'class': 'required', 'data-minimum-input-length': 0}),

        }
        error_messages = {
            'name': {
                'required': _("Name field is required."),
            },
            'category': {
                'required': _("Description field is required."),
            },
            'gst_rate': {
                'required': _("IGST rate field is required."),
            },
            'sgst_rate': {
                'required': _("SGST rate field is required."),
            },
            'cgst_rate': {
                'required': _("CGST rate field is required."),
            },
            'cess_rate': {
                'required': _("CESS rate field is required."),
            }
        }
        labels = {
            "gst_rate": "Gst rate"
        }


class ProductForm(forms.ModelForm):

    class Meta:
        model = Product
        exclude = ['creator', 'updater','deleted_reason', 'auto_id', 'is_deleted', 'is_deleted', 'is_admin_approved']

        widgets = {
            'name': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Name'}),
            'malayalam_name': TextInput(attrs={'class': 'required form-control', 'placeholder': 'മലയാളം പേര് '}),

            'description': Textarea(attrs={'class': 'form-control', 'placeholder': 'Description', 'autocomplete': 'off'}),
            'malayalam_description': Textarea(attrs={'class': 'form-control', 'placeholder': 'വിശദീകരണം', 'autocomplete': 'off'}),

            'meta_description': Textarea(attrs={'class': 'form-control', 'placeholder': 'Meta Description', 'autocomplete': 'off'}),
            'image': FileInput(attrs={'class': 'form-control dropify'}),
            'category': autocomplete.ModelSelect2(url='products:category_autocomplete', attrs={'data-placeholder': 'Category', 'data-minimum-input-length': 0},),
            'subcategory': Select(attrs={'class': 'form-control'}),
            'brand': autocomplete.ModelSelect2(url='products:brand_autocomplete', attrs={'data-placeholder': 'Brand', 'data-minimum-input-length': 0},),
            'hsn': autocomplete.ModelSelect2(url='products:hsn_code_autocomplete', attrs={'class': 'required', 'data-placeholder': 'HSN code', 'data-minimum-input-length': 0},),
            'vendor': autocomplete.ModelSelect2(url='vendors:vendor_autocomplete', attrs={'class': '', 'data-placeholder': 'Vendor', 'data-minimum-input-length': 0},),
            'unit_of_measurement': autocomplete.ModelSelect2(url='products:unit_measurement_autocomplete', attrs={'class': 'required', 'data-placeholder': 'Unit Measurement', 'data-minimum-input-length': 0},),
            'cancellable_duration': TextInput(attrs={'class': 'required form-control ', 'placeholder': 'Cancellable Duration'}),
            'returnable_duration': TextInput(attrs={'class': 'required form-control ', 'placeholder': 'Returnable Duration'}),
            'cancellable_duration_type': Select(attrs={'class': 'form-control'}),
            'returnable_duration_type': Select(attrs={'class': 'form-control'}),

        }

        error_messages = {
            'name': {
                'required': _("Name field is required."),
            },
            'vendor': {
                'required': _("Vendor type field is required."),
            },
            'image': {
                'required': _("Image field is required. "),
            },
            'category': {
                'required': _("Category field is required."),
            },
            'unit_of_measurement': {
                'required': _("Unit of measurement field is required."),
            },
        }


class ProductImagesForm(forms.ModelForm):

    class Meta:
        model = ProductImages
        exclude = ['creator', 'updater','deleted_reason', 'auto_id', 'is_deleted', 'product_variant']
        widgets = {
            'image': FileInput(attrs={'class': 'form-control dropify'}),
        }
        error_messages = {
            'image': {
                'required': _("Image field is required."),
            }
        }


class ProductVariantForm(forms.ModelForm):
    images = forms.FileField(
        required=False,
        widget=FileInput(attrs={'class': 'form-control dropify', 'multiple': ''}),
    )

    class Meta:
        model = ProductVariant
        exclude = ['creator', 'updater','deleted_reason', 'auto_id', 'is_deleted', 'product', 'stock', 'current_rating', 'is_admin_approved']

        widgets = {
            'image': FileInput(attrs={'class': 'form-control dropify'}),
            'product': autocomplete.ModelSelect2(url='products:product_autocomplete', attrs={'class': 'required', 'data-placeholder': 'Product', 'data-minimum-input-length': 0},),
            'warehouse': autocomplete.ModelSelect2(url='warehouses:warehouse_autocomplete', attrs={'class': 'required', 'data-placeholder': 'Warehouse', 'data-minimum-input-length': 0},),
            'unit': autocomplete.ModelSelect2(url='products:unit_autocomplete', attrs={'class': 'required', 'data-placeholder': 'Unit', 'data-minimum-input-length': 0}, forward=["unit_of_measurement"]),
            'product_code': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Product Code'}),

            'batch_number': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Batch Number'}),
            'manufacturing_date': TextInput(attrs={'type': 'date', 'class': ' required form-control', 'placeholder': 'Manufacturing Date'}),
            'expire_date': TextInput(attrs={'type': 'date', 'class': ' required form-control', 'placeholder': 'Expiry Date'}),

            'title': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Title'}),
            'image': FileInput(attrs={'class': 'form-control dropify'}),

            'stock': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Stock'}),
            'retail_price': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Retail Price'}),
            'whole_sale_price': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Whole Sale Price'}),
            'low_stock_limit': TextInput(attrs={'class': 'number required form-control', 'placeholder': 'Stock limit'}),
            'mrp': TextInput(attrs={'class': 'number required form-control', 'placeholder': 'Maximum Selling Price'}),
            'cost': TextInput(attrs={'class': 'number required form-control', 'placeholder': 'Cost'}),
            'first_time_stock': TextInput(attrs={'class': 'number form-control', 'placeholder': 'Stock'}),

            'discount_limit': TextInput(attrs={'class': 'number form-control', 'placeholder': 'Discount Limit'}),
            'sgst': TextInput(attrs={'class': 'number form-control', 'placeholder': 'Sgst', 'readonly': ""}),
            'cgst': TextInput(attrs={'class': 'number form-control', 'readonly': "", 'placeholder': 'Cgst'}),
            'igst': TextInput(attrs={'class': 'number form-control', 'readonly': "", 'placeholder': 'Igst'}),
            'commission_percentage': TextInput(attrs={'class': 'number form-control', 'placeholder': 'Commission Percentage'}),
        }

        error_messages = {
            'image': {
                'required': _("Image field is required."),
            },
            'product': {
                'required': _("Product field is required."),
            },
            'batch': {
                'required': _("Batch field is required."),
            },
            'unit': {
                'required': _("Unit field is required."),
            },
            'image': {
                'required': _("Image field is required."),
            }
        }



class VendorProductVariantForm(forms.ModelForm):
    images = forms.FileField(
        required=False,
        widget=FileInput(attrs={'class': 'form-control dropify', 'multiple': ''}),
    )

    class Meta:
        model = ProductVariant
        exclude = ['creator', 'updater','deleted_reason', 'auto_id', 'is_deleted', 'product', 'stock', 'current_rating', 'is_admin_approved','warehouse','low_stock_limit','commission_percentage','batch_number']

        widgets = {
            'image': FileInput(attrs={'class': 'form-control dropify'}),
            'product': autocomplete.ModelSelect2(url='products:product_autocomplete', attrs={'class': 'required', 'data-placeholder': 'Product', 'data-minimum-input-length': 0},),
            'warehouse': autocomplete.ModelSelect2(url='warehouses:warehouse_autocomplete', attrs={'class': 'required', 'data-placeholder': 'Warehouse', 'data-minimum-input-length': 0},),
            'unit': autocomplete.ModelSelect2(url='products:unit_autocomplete', attrs={'class': 'required', 'data-placeholder': 'Unit', 'data-minimum-input-length': 0}, forward=["unit_of_measurement"]),
            'product_code': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Product Code'}),

            'batch_number': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Batch Number'}),
            'manufacturing_date': TextInput(attrs={'type': 'date', 'class': ' required form-control', 'placeholder': 'Manufacturing Date'}),
            'expire_date': TextInput(attrs={'type': 'date', 'class': ' required form-control', 'placeholder': 'Expiry Date'}),

            'title': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Title'}),
            'image': FileInput(attrs={'class': 'form-control dropify'}),

            'stock': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Stock'}),
            'retail_price': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Retail Price'}),
            'whole_sale_price': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Whole Sale Price'}),
            'low_stock_limit': TextInput(attrs={'class': 'number required form-control', 'placeholder': 'Stock limit'}),
            'mrp': TextInput(attrs={'class': 'number required form-control', 'placeholder': 'Maximum Selling Price'}),
            'cost': TextInput(attrs={'class': 'number required form-control', 'placeholder': 'Cost'}),
            'first_time_stock': TextInput(attrs={'class': 'number form-control', 'placeholder': 'Stock'}),

            'discount_limit': TextInput(attrs={'class': 'number form-control', 'placeholder': 'Discount Limit'}),
            'sgst': TextInput(attrs={'class': 'number form-control', 'placeholder': 'Sgst', 'readonly': ""}),
            'cgst': TextInput(attrs={'class': 'number form-control', 'readonly': "", 'placeholder': 'Cgst'}),
            'igst': TextInput(attrs={'class': 'number form-control', 'readonly': "", 'placeholder': 'Igst'}),
            'commission_percentage': TextInput(attrs={'class': 'number form-control', 'readonly': "", 'placeholder': 'Commission Percentage'}),
        }

        error_messages = {
            'image': {
                'required': _("Image field is required."),
            },
            'product': {
                'required': _("Product field is required."),
            },
            'batch': {
                'required': _("Batch field is required."),
            },
            'unit': {
                'required': _("Unit field is required."),
            },
            'image': {
                'required': _("Image field is required."),
            }
        }



class VaryingProductPriceForm(forms.ModelForm):
    variant_id = forms.CharField(max_length=254, widget=forms.TextInput(attrs={'type':'hidden'}))

    class Meta:
        model = ProductVariant
        fields = [ 'title', 'retail_price', 'whole_sale_price', 'mrp']

        widgets = {
            'title': TextInput(attrs={'class': 'required form-control','readonly':'readonly', 'placeholder': 'Variant Name'}),
            'retail_price': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Retail Price'}),
            'whole_sale_price': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Whole Sale Price'}),
            'mrp': TextInput(attrs={'class': 'number required form-control', 'placeholder': 'Maximum Selling Price'}),
        }


class VendorSubCategoryForm(forms.ModelForm):

    class Meta:
        model = SubCategory
        exclude = ['creator', 'updater','deleted_reason', 'auto_id', 'is_deleted','is_admin_approved','vendor_created']
        widgets = {
            'name': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Name'}),
            'category': autocomplete.ModelSelect2(url='products:category_autocomplete', attrs={'data-placeholder': 'Category', 'class': 'required', 'data-minimum-input-length': 0}),
            'malayalam_name': TextInput(attrs={'class': 'required form-control', 'placeholder': 'മലയാളം പേര് '}),
        }

        error_messages = {
            'name': {
                'required': _("Name field is required."),
            },
            'category': {
                'required': _("Category field is required."),
            },
        }


class VendorUOMForm(forms.ModelForm):
    class Meta:
        model = UnitOfMeasurement
        exclude = ['creator', 'updater','deleted_reason', 'auto_id', 'is_deleted','is_admin_approved','vendor_created']
        widgets = {
            'unit_of_measurement': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Unit Measurement'}),
        }
        error_messages = {
            'unit_of_measurement': {
                'required': _("Unit of Measurement field is required."),
            }
        }


class VendorProductForm(forms.ModelForm):
    class Meta:
        model = Product

        exclude = [
            'creator',
            'updater',
            'deleted_reason',
            'auto_id',
            'is_deleted',
            'vendor',
            'vendor_created',
            'is_admin_approved'
        ]

        widgets = {
            'name': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Name'}),
            'malayalam_name': TextInput(attrs={'class': 'required form-control', 'placeholder': 'മലയാളം പേര് '}),
            'description': Textarea(attrs={'class': 'form-control', 'placeholder': 'Description', 'autocomplete': 'off'}),
            'malayalam_description': Textarea(attrs={'class': 'form-control', 'placeholder': 'വിശദീകരണം', 'autocomplete': 'off'}),

            'meta_description': Textarea(attrs={'class': 'form-control', 'placeholder': 'Meta Description', 'autocomplete': 'off'}),
            'image': FileInput(attrs={'class': 'form-control dropify'}),

            'category': autocomplete.ModelSelect2(url='products:category_autocomplete', attrs={'data-placeholder': 'Category', 'data-minimum-input-length': 0},),
            'subcategory': Select(attrs={'class': 'form-control'}),
            'brand': autocomplete.ModelSelect2(url='products:brand_autocomplete', attrs={'data-placeholder': 'Brand', 'data-minimum-input-length': 0},),
            'hsn': autocomplete.ModelSelect2(url='products:hsn_code_autocomplete', attrs={'class': 'required', 'data-placeholder': 'HSN code', 'data-minimum-input-length': 0},),
            'unit_of_measurement': autocomplete.ModelSelect2(url='products:unit_measurement_autocomplete', attrs={'class': 'required', 'data-placeholder': 'Unit Measurement', 'data-minimum-input-length': 0},),

            'cancellable_duration': TextInput(attrs={'class': 'required form-control ', 'placeholder': 'Cancellable Duration'}),
            'returnable_duration': TextInput(attrs={'class': 'required form-control ', 'placeholder': 'Returnable Duration'}),
            'cancellable_duration_type': Select(attrs={'class': 'form-control'}),
            'returnable_duration_type': Select(attrs={'class': 'form-control'}),
        }


class VendorVariantForm(forms.ModelForm):
    images = forms.FileField(
        required=False,
        widget=FileInput(attrs={'class': 'form-control dropify', 'multiple': ''}),
    )

    class Meta:
        model = ProductVariant
        exclude = [
            'creator',
            'updater',
            'deleted_reason',
            'auto_id',
            'is_deleted',
            'product',
            'stock',
            'current_rating',
            'vendor_created',
            'is_admin_approved',
            'low_stock_limit',
            'commission_percentage',

            'batch_number',
            # 'manufacturing_date',
            # 'first_time_stock',
            # 'expire_date',
            'warehouse'
        ]

        widgets = {
            # 'warehouse': autocomplete.ModelSelect2(url='warehouses:warehouse_autocomplete', attrs={'class': 'required', 'data-placeholder': 'Warehouse', 'data-minimum-input-length': 0},),
            'unit': autocomplete.ModelSelect2(url='products:unit_autocomplete', attrs={'class': 'required', 'data-placeholder': 'Unit', 'data-minimum-input-length': 0}, forward=["unit_of_measurement"]),

            'batch_number': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Batch Number'}),
            'manufacturing_date': TextInput(attrs={'type': 'date', 'class': ' required form-control', 'placeholder': 'Manufacturing Date'}),
            'expire_date': TextInput(attrs={'type': 'date', 'class': ' required form-control', 'placeholder': 'Expiry Date'}),

            'title': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Title'}),
            'product_code': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Product Code'}),
            'image': FileInput(attrs={'class': 'form-control dropify'}),

            'retail_price': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Retail Price'}),
            'whole_sale_price': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Whole Sale Price'}),
            'mrp': TextInput(attrs={'class': 'number required form-control', 'placeholder': 'Maximum Selling Price'}),
            'cost': TextInput(attrs={'class': 'number required form-control', 'placeholder': 'Cost'}),
            'first_time_stock': TextInput(attrs={'class': 'number form-control', 'placeholder': 'Available Stock'}),

            'discount_limit': TextInput(attrs={'class': 'number form-control', 'placeholder': 'Discount Limit'}),
            'sgst': TextInput(attrs={'class': 'number form-control', 'placeholder': 'SGST', 'readonly': ""}),
            'cgst': TextInput(attrs={'class': 'number form-control', 'placeholder': 'CGST', 'readonly': ""}),
            'igst': TextInput(attrs={'class': 'number form-control', 'placeholder': 'IGST', 'readonly': ""}),
        }

        error_messages = {
            'image': {
                'required': _("Image field is required."),
            },
            'product': {
                'required': _("Product field is required."),
            },
            'batch': {
                'required': _("Batch field is required."),
            },
            'unit': {
                'required': _("Unit field is required."),
            },
            'image': {
                'required': _("Image field is required."),
            }
        }
