# Standard libraries
from warehouses.models import Warehouse
import xlrd
import xlwt
import json
import requests
import datetime
from decimal import Decimal
# Third party libraries
from dal import autocomplete
# Django libraries
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.http.response import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q, F
from django.forms.formsets import formset_factory
from django.forms.models import inlineformset_factory
from django.template.loader import render_to_string
from django.db.models import Sum
from django.template.loader import render_to_string
# Local libraries
from main.decorators import role_required
from main.functions import generate_form_errors, get_auto_id, get_a_id, get_current_role, get_date_updated_request
from users.functions import get_warehouse
from general.models import Batch
from main.utils.export_to_excel import ExportToExcelUtils
from api.v1.general.serializers import VariantExportSerializer, ProductExportSerializer
from customers.utils.instances_manager import InstancesManager
from general.functions import render_to_pdf
from .functions import image_validation, get_exact_qty
from .models import Category, UnitOfMeasurement, SubCategory, Unit, Brand, HsnCodes, Product, ProductImages, ProductVariant
from .forms import ProductBarcodeForm, VaryingProductPriceForm, SubCategoryForm, CategoryForm, BrandForm, \
    ProductImagesForm, ProductForm, ProductVariantForm, HsnCodesForm, UnitOfMeasurementForm, UnitForm, VendorProductVariantForm, VendorVariantForm


class HSNcodeAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        items = HsnCodes.objects.filter(is_deleted=False, is_admin_approved=True)

        if self.q:
            items = items.filter(Q(hsn_number__istartswith=self.q))

        return items


class BrandAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        items = Brand.objects.filter(is_deleted=False, is_admin_approved=True)

        if self.q:
            items = items.filter(Q(auto_id__istartswith=self.q) | Q(name__istartswith=self.q))

        return items

    def create_object(self, text):
        if not Brand.objects.filter(is_deleted=False, name=text).exists():
            brand = Brand.objects.create(
                auto_id=get_auto_id(Brand),
                name=text,
                is_admin_approved=True,
                creator=self.request.user,
                updater=self.request.user
            )
            return brand


class CategoryAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        items = Category.objects.filter(is_deleted=False, is_admin_approved=True)

        if self.q:
            items = items.filter(Q(auto_id__istartswith=self.q) | Q(name__istartswith=self.q))

        return items

    def create_object(self, text):
        if not Category.objects.filter(is_deleted=False, name=text).exists():
            category = Category.objects.create(
                auto_id=get_auto_id(Category),
                name=text,
                is_admin_approved=True,
                creator=self.request.user,
                updater=self.request.user
            )
            return category


class SubcategoryAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        items = SubCategory.objects.filter(is_deleted=False, is_admin_approved=True)
        category = self.forwarded.get('category', None)

        if category:
            items = items.filter(category=category)
        if self.q:
            items = items.filter(Q(auto_id__istartswith=self.q) | Q(name__istartswith=self.q))

        return items


class UnitMeasurementAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        items = UnitOfMeasurement.objects.filter(is_deleted=False, is_admin_approved=True)

        if self.q:
            items = items.filter(Q(auto_id__istartswith=self.q) | Q(unit_of_measurement__istartswith=self.q))

        return items

    def create_object(self, text):
        # text = text.title()

        if not UnitOfMeasurement.objects.filter(is_deleted=False, unit_name=text):
            return UnitOfMeasurement.objects.create(
                auto_id=get_auto_id(UnitOfMeasurement),
                is_admin_approved=True,
                unit=text,
                creator=self.request.user,
                updater=self.request.user
            )


class UnitAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        items = Unit.objects.filter(is_deleted=False, is_admin_approved=True)

        if self.q:
            items = items.filter(Q(auto_id__istartswith=self.q) | Q(unit__istartswith=self.q))

        unit_of_measurement = self.forwarded.get('unit_of_measurement', None)
        if unit_of_measurement:
            items = items.filter(unit_of_measurement_id=unit_of_measurement)

        return items

    def create_object(self, text):
        # text = text.title()

        if not Unit.objects.filter(is_deleted=False, unit_name=text):
            auto_id = get_auto_id(Unit)
            return Unit.objects.create(
                auto_id=auto_id,
                unit_name=text,
                is_admin_approved=True,
                creator=self.request.user,
                updater=self.request.user
            )


class ProductAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        items = Product.objects.filter(is_deleted=False, is_admin_approved=True)

        if self.q:
            query = self.q
            items = items.filter(
                Q(auto_id__icontains=query) |
                Q(name__icontains=query) |
                Q(category__name__icontains=query) |
                Q(subcategory__name__icontains=query) |
                Q(brand__name__icontains=query)
            )

        brand = self.forwarded.get('brand', None)
        if brand:
            items = items.filter(brand_id=brand)

        if self.request.user.is_authenticated:
            if self.request.user.is_superuser:
                items = items.filter(vendor_created=False)

        return items


class ProductVariantAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        instances = ProductVariant.objects.filter(is_deleted=False, is_admin_approved=True)

        instances = instances.filter(product__vendor__isnull=True)

        if self.q:
            query = self.q
            instances = instances.filter(
                Q(auto_id__icontains=query) |
                Q(product__name__icontains=query) |
                Q(title__icontains=query) |
                Q(product__brand__name__icontains=query) |
                Q(unit__unit__icontains=query)
            )

        return instances


@login_required
@role_required(['superadmin', 'warehouse_manager', 'vendor_user'])
def create(request):
    # ProductImagesFormset = formset_factory(ProductImagesForm, extra=3)
    ProductVariantFormset = formset_factory(ProductVariantForm, extra=1)

    if request.method == 'POST':
        ModifiedRequest = get_date_updated_request(request.POST.copy(), ['expire_date'])

        form = ProductForm(request.POST, request.FILES)
        # product_image_formset = ProductImagesFormset(request.POST, request.FILES, prefix='product_image_formset')
        product_variation_formset = ProductVariantFormset(request.POST, request.FILES, prefix='product_variation_formset', form_kwargs={'empty_permitted': False})

        # Check that product created by vendor
        current_role = get_current_role(request)
        if current_role == 'vendor_user':
            vendor_created = True
            is_admin_approved = None
            ProductVariantFormset = formset_factory(VendorVariantForm, extra=1)
            product_variation_formset = ProductVariantFormset(request.POST, request.FILES, prefix='product_variation_formset', form_kwargs={'empty_permitted': False})
            vendor = request.user.vendor
        else:
            vendor_created = False
            is_admin_approved = True

        # if form.is_valid() and product_image_formset.is_valid() and product_variation_formset.is_valid():
        if form.is_valid() and product_variation_formset.is_valid():
            error_messages = ''
            image = form.cleaned_data['image']
            product_name = form.cleaned_data['name']

            price_ok = True
            # is_ok, error_messages = image_validation(image)
            is_ok = True
            is_default_ok = False

            for form_item in product_variation_formset:
                mrp = form_item.cleaned_data['mrp']
                cost = form_item.cleaned_data['cost']
                retail_price = form_item.cleaned_data['retail_price']
                whole_sale_price = form_item.cleaned_data['whole_sale_price']
                product_name = form_item.cleaned_data['title']
                is_default = form_item.cleaned_data['is_default']

                if is_default:
                    is_default_ok = True

                # retail_price
                if (Decimal(mrp) - Decimal(retail_price)) < 0:
                    error_messages += f'Retail price is greater than MRP of variant {product_name}.\n'
                    price_ok = False
                if (Decimal(retail_price) - Decimal(cost)) < 0:
                    error_messages += f'Cost is greater than Retail price of variant {product_name}.\n'
                    price_ok = False

                # whole_sale_price
                if (Decimal(mrp) - Decimal(whole_sale_price)) < 0:
                    error_messages += f'Whole Sale price is greater than MRP of variant {product_name}.\n'
                    price_ok = False
                if (Decimal(whole_sale_price) - Decimal(cost)) < 0:
                    error_messages += f'Cost is greater than Whole Sale price of variant {product_name}.\n'
                    price_ok = False

            if is_ok and price_ok and is_default_ok:
                auto_id = get_auto_id(Product)
                name = form.cleaned_data['name']
                # name = name.title()

                if auto_id < 10:
                    product_code = "PR00%s" % str(auto_id)
                elif auto_id >= 10 and auto_id < 100:
                    product_code = "PR0%s" % str(auto_id)
                else:
                    product_code = "PR%s" % str(auto_id)

                # create product
                data = form.save(commit=False)

                data.is_admin_approved = True
                data.creator = request.user
                data.updater = request.user
                data.gst_included = True
                data.auto_id = auto_id
                data.name = name

                if current_role == 'vendor_user':
                    # Set that product created by vendor
                    data.vendor = vendor
                    data.vendor_created=vendor_created
                    data.is_admin_approved=is_admin_approved

                    warehouse = None
                    batch_number = "DEFAULT"
                    if Warehouse.objects.filter(location=vendor.location).exists():
                        warehouse = Warehouse.objects.filter(location=vendor.location).first()

                data.save()

                count = 0
                for i in product_variation_formset:
                    uploaded_files = request.FILES.getlist(f'product_variation_formset-{count}-images')

                    count += 1

                    if i.cleaned_data != {}:
                        image = i.cleaned_data['image']
                        title = i.cleaned_data['title']
                        stock = i.cleaned_data['first_time_stock']
                        cost = i.cleaned_data['cost']
                        mrp = i.cleaned_data['mrp']
                        is_default = i.cleaned_data['is_default']
                        manufacturing_date = i.cleaned_data['manufacturing_date']
                        expire_date = i.cleaned_data['expire_date']
                        low_stock_limit = i.cleaned_data.get('low_stock_limit',0)
                        retail_price = i.cleaned_data['retail_price']
                        whole_sale_price = i.cleaned_data['whole_sale_price']

                        product_code = i.cleaned_data['product_code']
                        unit = i.cleaned_data['unit']
                        discount_limit = i.cleaned_data['discount_limit']
                        sgst = i.cleaned_data['sgst']
                        cgst = i.cleaned_data['cgst']
                        igst = i.cleaned_data['igst']

                        if current_role != 'vendor_user':
                            warehouse = i.cleaned_data.get('warehouse', None)
                            batch_number = i.cleaned_data.get('batch_number', None)

                        product_variant = ProductVariant.objects.create(
                            warehouse=warehouse,
                            product=data,
                            unit=unit,

                            title=title,
                            is_default=is_default,
                            product_code=product_code,
                            image=image,

                            batch_number=batch_number,
                            manufacturing_date=manufacturing_date,
                            expire_date=expire_date,
                            stock=stock,
                            low_stock_limit=low_stock_limit,
                            first_time_stock=stock,
                            discount_limit=discount_limit,

                            sgst=sgst,
                            cgst=cgst,
                            igst=igst,
                            mrp=mrp,
                            cost=cost,
                            retail_price=retail_price,
                            whole_sale_price=whole_sale_price,

                            vendor_created=vendor_created,
                            is_admin_approved=is_admin_approved,

                            auto_id=get_auto_id(ProductVariant),
                            creator=request.user,
                            updater=request.user,
                        )

                        if len(uploaded_files) > 0:
                            for single_image in uploaded_files:
                                ProductImages.objects.create(
                                    product_variant = product_variant,
                                    image = single_image,

                                    auto_id=get_auto_id(ProductImages),
                                    creator=request.user,
                                    updater=request.user,
                                )

                        if warehouse and batch_number not in [None,'']:

                            Batch.objects.create(
                                auto_id=get_auto_id(Batch),
                                creator=request.user,
                                updater=request.user,

                                product=data,
                                product_variant=product_variant,
                                warehouse=warehouse,
                                batch_number=batch_number,

                                stock=stock,
                                cost=cost,
                                mrp=mrp,
                                retail_price=retail_price,
                                whole_sale_price=whole_sale_price,

                                expire_date=expire_date,
                                manufacturing_date=manufacturing_date,
                            )

                response_data = {
                    "status": "true",
                    "title": "Successfully Created",
                    "message": "Product created successfully.",
                    'redirect': 'true',
                    "redirect_url": reverse('products:product', kwargs={'pk': data.pk})
                }
            else:
                if not is_default_ok:
                    error_messages += "you have to set 1 variant as default"

                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": str(error_messages)
                }

            return HttpResponse(json.dumps(response_data), content_type='application/javascript')

        else:
            print(form.errors)
            print(product_variation_formset.errors)
            # print(product_image_formset.errors)
            message1 = generate_form_errors(form, formset=False)
            message3 = generate_form_errors(product_variation_formset, formset=True)
            # message2 = generate_form_errors(product_image_formset, formset=True)
            # message = str(message1) + str(message2) + str(message3)

            message = str(message1) + str(message3)

            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": str(message)
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        product_form = ProductForm()
        # product_image_formset = ProductImagesFormset(prefix='product_image_formset')
        warehouse = get_warehouse(request)
        product_variation_formset = ProductVariantFormset(prefix='product_variation_formset',
                                                          initial=[{'warehouse': warehouse}])

        context = {
            "title": "Create Product ",
            "form": product_form,
            "warehouse": warehouse,
            # "product_image_formset": product_image_formset,
            "product_variation_formset": product_variation_formset,
            "url": reverse('products:create'),
            'redirect': True,
            'is_edit': False,
            'is_no_need_autocomplete': True
        }

        return render(request, 'products/entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def products(request):
    brands = Brand.objects.filter(is_deleted=False)
    instances = Product.objects.filter(is_deleted=False)
    categories = Category.objects.filter(is_deleted=False)

    title = "Products"
    # filter block
    filter_data = {}
    query = request.GET.get("q")
    brand = request.GET.get("brand")
    category = request.GET.get("category")
    sub_category = request.GET.get("sub_category")

    if query:
        product_pks = []
        if ProductVariant.objects.filter(Q(product_code__istartswith=query) | Q(title__icontains=query)).exists():
            product_pks = ProductVariant.objects.filter(
                Q(product_code__istartswith=query) | Q(title__icontains=query)).values_list('product_id', flat=True)

        instances = instances.filter(Q(pk__in=product_pks) | Q(auto_id__icontains=query) | Q(name__icontains=query) | Q(
            category__name__icontains=query) | Q(subcategory__name__icontains=query) | Q(brand__name__icontains=query))
        title = "Products - %s" % query
        filter_data['q'] = query

    if brand:
        try:
            instances = instances.filter(brand_id=brand)
            filter_data['brand'] = brand
        except:
            pass

    if category:
        try:
            instances = instances.filter(category_id=category)
            filter_data['category'] = category
        except:
            pass

    if sub_category:
        try:
            instances = instances.filter(subcategory_id=sub_category)
            filter_data['sub_category'] = sub_category
        except:
            pass

    context = {"instances": instances, 'title': title, "brands": brands, "category": categories,
               "is_excel_export": True, "filter_data": filter_data, }

    return render(request, 'products/products.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager','vendor_user'])
def product(request, pk):
    instance = get_object_or_404(Product.objects.filter(pk=pk))
    # product_images = ProductImages.objects.filter(product=instance)
    product_variants = ProductVariant.objects.filter(product=instance, is_deleted=False)

    initial = {'igst': instance.hsn.igst_rate, 'cgst': instance.hsn.cgst_rate, 'sgst': instance.hsn.sgst_rate, }

    form = ProductVariantForm(instance=instance, initial=initial)

    context = {"form": form, "instance": instance,  # "product": product_images,
               "product_variants": product_variants, "title": "Product : " + instance.name, "single_page": True, }

    return render(request, 'products/product.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager','vendor_user'])
def edit(request, pk):
    instance = get_object_or_404(Product.objects.filter(pk=pk, is_deleted=False))

    current_role = get_current_role(request)


    if request.method == 'POST':
        response_data = {}
        post_request = get_date_updated_request(request.POST.copy(), ['expire_date'])
        form = ProductForm(post_request, request.FILES, instance=instance)

        if form.is_valid():
            name = form.cleaned_data['name']
            is_ok = True
            error_messages = ''

            if not is_ok:
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": str(error_messages)
                }

                return HttpResponse(json.dumps(response_data), content_type='application/javascript')

            # update product
            data = form.save(commit=False)

            data.updater = request.user
            data.date_updated = datetime.datetime.now()
            data.name = name



            data.save()

            referer_url = request.POST.get('referer_url')
            if not referer_url:
                referer_url = reverse('products:products')

            if current_role == 'vendor_user':
                referer_url = reverse('vendors:vendor_products')

            response_data = {"status": "true", "title": "Successfully Updated",
                             "message": "Product Successfully Updated.", "redirect": "true", "redirect_url": referer_url
                             # "redirect_url": reverse('products:product', kwargs={'pk': data.pk})
                             }
        else:
            message = generate_form_errors(form, formset=False)
            print(str(message))
            print(form.errors, "form=====")

            response_data = {"status": "false", "stable": "true", "title": "Form validation error", "message": message}

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        product_form = ProductForm(instance=instance)

        context = {
            "title": "Edit Product : " + instance.name,
            "form": product_form,
            "instance": instance,
            "url": reverse('products:edit', kwargs={'pk': instance.pk}),
            "redirect": True,
            "is_edit": True,
            'referer_url': request.META['HTTP_REFERER'],
        }

        if current_role == 'vendor_user':
            return render(request, 'vendor/product_entry.html', context)
        else:
            return render(request, 'products/entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete(request, pk):
    reason = request.GET.get('reason')
    instance = get_object_or_404(Product.objects.filter(pk=pk))
    instance.is_deleted = True
    instance.updater = request.user
    instance.deleted_reason = reason
    instance.date_updated = datetime.datetime.now()
    instance.save()

    variants = ProductVariant.objects.filter(product_id=pk, is_admin_approved=True)

    for item in variants:
        if not '__is_deleted'.upper() in item.product_code:
            item.product_code = f'{item.product_code}__is_deleted_{item.auto_id}'

        item.is_deleted = True
        item.deleted_reason = reason

        item.save()

    response_data = {"status": "true", "title": "Successfully Deleted", "message": "Product Successfully Deleted.",
                     "redirect": "true", "redirect_url": reverse('products:products')}
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager','vendor_user'])
def edit_variant(request, pk):
    instance = get_object_or_404(ProductVariant.objects.filter(pk=pk))

    current_role = get_current_role(request)

    old_stock = instance.first_time_stock
    image_instances = ProductImages.objects.filter(product_variant_id=pk)

    if image_instances.exists():
        extra = 0
        has_images = True
    else:
        has_images = False
        extra = 1

    ProductImagesFormset = inlineformset_factory(
        ProductVariant,
        ProductImages,
        can_delete=True,
        extra=extra,
        form=ProductImagesForm,
    )

    if request.method == 'POST':
        response_data = {}

        if current_role == 'vendor_user' or instance.product.vendor:
            form = VendorProductVariantForm(request.POST, request.FILES, instance=instance)
        else:
            form = ProductVariantForm(request.POST, request.FILES, instance=instance)

        product_image_formset = ProductImagesFormset(request.POST, request.FILES, prefix='product_image_formset', instance=instance)

        if form.is_valid() and product_image_formset.is_valid():
            product_code = request.POST.get('product_code')

            mrp = form.cleaned_data['mrp']
            cost = form.cleaned_data['cost']
            name = form.cleaned_data['title']
            warehouse = form.cleaned_data.get('warehouse',None)
            manufacturing_date = form.cleaned_data['manufacturing_date']
            retail_price = form.cleaned_data['retail_price']
            whole_sale_price = form.cleaned_data['whole_sale_price']
            is_ok = True
            error_messages = ''

            prd_code = form.cleaned_data['product_code']

            if ProductVariant.objects.filter(is_deleted=False, product_code=prd_code).exclude(pk=pk).exists():
                error_messages += f'A Variant with product code {prd_code} already exists. \n'
                is_ok = False

            if (Decimal(mrp) - Decimal(retail_price)) < 0:
                error_messages += f'Retail price is greater than MRP of product variant {name}.\n'
                is_ok = False
            if (Decimal(retail_price) - Decimal(cost)) < 0:
                error_messages += f'Cost is greater than Retail price of product variant {name}.\n'
                is_ok = False

            if (Decimal(mrp) - Decimal(whole_sale_price)) < 0:
                error_messages += f'Whole Sale price is greater than MRP of product variant {name}.\n'
                is_ok = False
            if (Decimal(whole_sale_price) - Decimal(cost)) < 0:
                error_messages += f'Cost is greater than Whole Sale price of product variant {name}.\n'
                is_ok = False

            if not is_ok:
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": str(error_messages)
                }

                return HttpResponse(json.dumps(response_data), content_type='application/javascript')

            data = form.save(commit=False)
            data.updater = request.user
            data.product_code = product_code
            data.date_updated = datetime.datetime.now()
            data.save()

            images = product_image_formset.save(commit=False)

            for image_item in images:
                if not image_item.auto_id:
                    image_item.creator = request.user
                    image_item.auto_id = get_auto_id(ProductImages)
                image_item.updater = request.user
                image_item.product_variant = instance
                image_item.save()

            for obj in product_image_formset.deleted_objects:
                print('------------------------deleted------------------------')
                obj.delete()

            batch_number = form.cleaned_data.get('batch_number',None)
            mrp = form.cleaned_data['mrp']
            cost = form.cleaned_data['cost']
            stock = form.cleaned_data['first_time_stock']
            retail_price = form.cleaned_data['retail_price']
            whole_sale_price = form.cleaned_data['whole_sale_price']
            expire_date = form.cleaned_data['expire_date']
            product_code = form.cleaned_data['product_code']

            igst_p = instance.product.hsn.igst_rate
            sgst_p = instance.product.hsn.sgst_rate
            cgst_p = instance.product.hsn.cgst_rate
            taxable_amount_batch = round(cost / (1 + (sgst_p / 100) + (cgst_p / 100)), 2)
            if batch_number not in [None,'']:
                if Batch.objects.filter(batch_number=batch_number, product_variant=data).exists():
                    Batch.objects.filter(batch_number=batch_number, product_variant=data).update(
                        mrp = mrp,
                        cost = cost,
                        retail_price = retail_price,
                        whole_sale_price = whole_sale_price,
                        stock = F('stock') - old_stock + stock,
                        expire_date = expire_date,
                        manufacturing_date = manufacturing_date,
                        warehouse = warehouse,
                    )

                else:
                    Batch.objects.create(
                        auto_id = get_auto_id(Batch),
                        creator = request.user,
                        updater = request.user,
                        product = data.product,
                        product_variant = data,
                        batch_number = batch_number,
                        stock = stock,
                        cost = cost,
                        mrp = mrp,
                        expire_date = expire_date,
                        manufacturing_date = manufacturing_date,
                        retail_price = retail_price,
                        whole_sale_price = whole_sale_price,
                        warehouse = warehouse,
                    )

            data.stock = data.total_stock()
            data.save()

            response_data = {
                "status": "true",
                "title": "Successfully Updated",
                "message": "Product Variation Successfully Updated.",
                "redirect": "true",
                "redirect_url": reverse('products:product', kwargs={'pk': data.product.pk})
            }
        else:

            message1 = generate_form_errors(form, formset=False)
            message2 = generate_form_errors(product_image_formset, formset=True)
            message = str(message1) + str(message2)
            print(form.errors, "/t/tform=====")
            print(product_image_formset.errors, "/t/tproduct_image_formset=====")

            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": str(message)
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        if current_role == 'vendor_user' or instance.product.vendor:
            form = VendorProductVariantForm(instance=instance)
        else:
            form = ProductVariantForm(instance=instance)
        product_image_formset = ProductImagesFormset(prefix='product_image_formset', instance=instance)

        context = {
            "form": form,
            "instance": instance,
            "has_images": has_images,
            "product": instance.product,
            "product_image_formset": product_image_formset,
            "title": "Update Product variant : " + instance.title,
            "redirect": True,
        }

        return render(request, 'products/entry_varients.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager', 'vendor_user'])
def create_variant(request, pk):
    instance = get_object_or_404(Product.objects.filter(pk=pk))
    ProductImagesFormset = formset_factory(ProductImagesForm, extra=2)
    current_role = get_current_role(request)

    if request.method == 'POST':
        response_data = {}

        if current_role == 'vendor_user' or instance.vendor:
            form = VendorProductVariantForm(request.POST, request.FILES)
        else:
            form = ProductVariantForm(request.POST, request.FILES)
        product_image_formset = ProductImagesFormset(request.POST, request.FILES, prefix='product_image_formset')

        if form.is_valid() and product_image_formset.is_valid():
            mrp = form.cleaned_data['mrp']
            cost = form.cleaned_data['cost']
            name = form.cleaned_data['title']
            manufacturing_date = form.cleaned_data['manufacturing_date']
            retail_price = form.cleaned_data['retail_price']
            whole_sale_price = form.cleaned_data['whole_sale_price']
            prd_code = form.cleaned_data['product_code']

            is_ok = True
            error_messages = ''

            if ProductVariant.objects.filter(is_deleted=False, product_code=prd_code).exists():
                error_messages += f'A Variant with product code {prd_code} already exists. \n'
                is_ok = False

            if (Decimal(mrp) - Decimal(retail_price)) < 0:
                error_messages += f'Retail price is greater than MRP of product variant {name}.\n'
                is_ok = False
            if (Decimal(retail_price) - Decimal(cost)) < 0:
                error_messages += f'Cost is greater than Retail price of product variant {name}.\n'
                is_ok = False

            if (Decimal(mrp) - Decimal(whole_sale_price)) < 0:
                error_messages += f'Whole Sale price is greater than MRP of product variant {name}.\n'
                is_ok = False
            if (Decimal(whole_sale_price) - Decimal(cost)) < 0:
                error_messages += f'Cost is greater than Whole Sale price of product variant {name}.\n'
                is_ok = False

            if not is_ok:
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": str(error_messages)
                }

                return HttpResponse(json.dumps(response_data), content_type='application/javascript')

            stock = form.cleaned_data['first_time_stock']
            expire_date = form.cleaned_data['expire_date']
            product_code = form.cleaned_data['product_code']

            if instance.vendor:
                warehouse = None
                batch_number = "DEFAULT"
                if Warehouse.objects.filter(location=instance.vendor.location).exists():
                    warehouse = Warehouse.objects.filter(location=instance.vendor.location).first()
            else:
                batch_number = form.cleaned_data['batch_number']
                warehouse = form.cleaned_data['warehouse']

            data = form.save(commit=False)
            data.auto_id = get_auto_id(ProductVariant)
            data.is_admin_approved = True
            data.updater = request.user
            data.creator = request.user
            data.product_code = product_code
            data.product = instance
            data.stock = stock
            data.save()

            for image_item in product_image_formset:
                if image_item.cleaned_data != {}:
                    image = image_item.cleaned_data['image']

                    ProductImages.objects.create(
                        image = image,
                        product_variant = data,

                        creator = request.user,
                        updater = request.user,
                        auto_id = get_auto_id(ProductImages),
                    )

            igst = instance.hsn.igst_rate
            sgst_p = instance.hsn.sgst_rate
            cgst_p = instance.hsn.cgst_rate
            taxable_amount_batch = round(cost / (1 + (sgst_p / 100) + (cgst_p / 100)), 2)

            Batch.objects.create(
                warehouse = warehouse,
                product_variant = data,
                product = instance,
                auto_id = get_auto_id(Batch),
                creator = request.user,
                updater = request.user,
                batch_number = batch_number,
                stock = stock,
                mrp = mrp,
                cost = cost,
                expire_date = expire_date,
                manufacturing_date = manufacturing_date,
                retail_price = retail_price,
                whole_sale_price = whole_sale_price,
            )

            response_data = {
                "status": "true",
                "title": "Successfully Created",
                "message": "Product Variation Successfully Created.", "redirect": "true",
                "redirect_url": reverse('products:product', kwargs={'pk': data.product.pk})
            }

        else:
            message = generate_form_errors(form, formset=False)
            message += generate_form_errors(product_image_formset, formset=True)

            print(str(message))
            print(form.errors, "form=====")
            print(product_image_formset.errors, "form=====")
            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        if current_role == 'vendor_user' or instance.vendor:
            form = VendorProductVariantForm(request.POST, request.FILES)
        else:
            form = ProductVariantForm(request.POST, request.FILES)
        product_image_formset = ProductImagesFormset(prefix='product_image_formset')

        context = {
            "form": form,
            "product": instance,
            "product_image_formset": product_image_formset,
            "title": "Create Product Variant : " + instance.name,
            "url": reverse('products:create_variant', kwargs={'pk': instance.pk}),
            "redirect": True,
        }

        return render(request, 'products/entry_varients.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_variant(request, pk):
    instance = get_object_or_404(ProductVariant.objects.filter(pk=pk))

    if not '__is_deleted' in instance.product_code:
        instance.product_code = f'{instance.product_code}__is_deleted_{instance.auto_id}'

    instance.is_deleted = True
    reason = request.GET.get('reason')
    instance.deleted_reason = reason
    instance.save()

    response_data = {"status": "true", "title": "Successfully Deleted",
                     "message": "Product Variant Successfully Deleted.", "redirect": "false", }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager', 'vendor_user'])
def view_variant(request, pk):
    instance = get_object_or_404(ProductVariant, pk=pk)

    sale_items = instance.saleitem_set.filter(sale__is_deleted=False).order_by('-id')[:10]
    order_items = instance.orderitem_set.filter(order__is_deleted=False).order_by('-date_added')[:10]
    batches = instance.batch_set.filter(is_deleted=False)

    context = {
        'title': f'Product : {instance}',
        'batches': batches,
        'instance': instance,
        'sale_items': sale_items,
        'order_items': order_items,
        'total_stock': batches.aggregate(Sum('stock')).get('stock__sum', 0),
    }

    return render(request, "products/product_variant.html", context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_selected_products(request):
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            Product.objects.filter(pk=pk).update(is_deleted=True)
            # instance = get_object_or_404(Product.objects.filter(pk=pk, is_deleted=False))
            # update_stock_register_delete(instance.pk,"opening",instance.pk)

        response_data = {
            "status": "true",
            "title": "Successfully Deleted",
            "message": "Selected Product(s) Successfully Deleted.",
            "redirect": "true",
            "redirect_url": reverse('products:products')
        }
    else:
        response_data = {
            "status": "false",
            "stable": "true",
            "title": "Nothing selected",
            "message": "Please select some items first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager', 'vendor_user'])
def get_category_details(request):
    pk = request.GET.get('id_category')
    if SubCategory.objects.filter(category__pk=pk).exists():
        subcategories = SubCategory.objects.filter(category__pk=pk, is_deleted=False)
        subcategory_datas = []
        for subcategory in subcategories:
            category_item = {'id': str(subcategory.pk), 'name': subcategory.name, }
            subcategory_datas.append(category_item)
        response_data = {"status": "true", "subcategory": subcategory_datas, }
    else:
        response_data = {"status": "false", "message": "Sub-Category not added"}
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


def export_filtered_products(request):
    query = request.GET.get("q")
    brand = request.GET.get("brand")
    category = request.GET.get("category")
    sub_category = request.GET.get("sub_category")

    instances = ProductVariant.objects.filter(is_deleted=False, is_admin_approved=True, product__is_deleted=False)

    if query:
        instances = instances.filter(
            Q(auto_id__icontains=query) | Q(title__icontains=query) | Q(product_code__icontains=query) | Q(
                product__name__icontains=query) | Q(product__brand__name__icontains=query) | Q(
                product__category__name__icontains=query) | Q(product__subcategory__name__icontains=query) | Q(
                product__brand__name__icontains=query))

        title = "Products - %s" % query

    if brand:
        try:
            instances = instances.filter(product__brand_id=brand)
        except:
            pass

    if category:
        try:
            instances = instances.filter(product__category_id=category)
        except:
            pass

    if sub_category:
        try:
            instances = instances.filter(product__subcategory_id=sub_category)
        except:
            pass

    date_string = datetime.datetime.strftime(datetime.datetime.now(), '%d-%m-%Y')

    warehouse = get_warehouse(request)

    title = "Products on " + date_string

    wb = xlwt.Workbook()
    ws = wb.add_sheet(title)

    ws.write(0, 0, "SL:No.")
    ws.write(0, 1, "Brand")
    ws.write(0, 2, "Product Name")
    ws.write(0, 3, "Variant Name")
    ws.write(0, 4, "Malayalam Name")
    ws.write(0, 5, "Product Code")
    ws.write(0, 6, "Category")
    ws.write(0, 7, "Sub Category")
    ws.write(0, 8, "Default or Not")
    ws.write(0, 9, "Vendor")
    ws.write(0, 10, "Description")
    ws.write(0, 11, "Cost")
    ws.write(0, 12, "Wholesale Price")
    ws.write(0, 13, "Retail Price")
    ws.write(0, 14, "MRP")
    ws.write(0, 15, "HSN Code")
    ws.write(0, 16, "SGST (%)")
    ws.write(0, 17, "CGST (%)")
    ws.write(0, 18, "IGST (%)")
    ws.write(0, 19, "CESS (%)")
    ws.write(0, 20, "First Time Stock")
    ws.write(0, 21, "Current Stock")
    ws.write(0, 22, "Low Stock Limit")
    ws.write(0, 23, "Discount Limit")
    ws.write(0, 24, "Current Rating")
    ws.write(0, 25, "Discount Limit")

    if instances:
        count = 1

        for instance in instances:
            batches = Batch.objects.filter(is_deleted=False, )

            if warehouse:
                batches = batches.filter(warehouse=warehouse)

            stock = 0
            if batches.exists():
                stock = batches.aggregate(Sum('stock'))['stock__sum']

            ws.write(count, 0, count)

            if instance.product.brand:
                ws.write(count, 1, instance.product.brand.name)

            ws.write(count, 2, instance.product.name)
            ws.write(count, 3, instance.title)
            if instance.product.malayalam_name:
                ws.write(count, 4, instance.product.malayalam_name)
            ws.write(count, 5, instance.product_code)

            if instance.product.category:
                ws.write(count, 6, instance.product.category.name)
                if instance.product.subcategory:
                    ws.write(count, 7, instance.product.subcategory.name)

            if instance.is_default:
                ws.write(count, 8, 'Default')

            if instance.product.vendor:
                ws.write(count, 9, instance.product.vendor.name)
            ws.write(count, 10, instance.product.description)
            ws.write(count, 11, instance.cost)

            if instance.product.vendor:
                ws.write(count, 12, instance.product.vendor.name)

            ws.write(count, 13, instance.retail_price)
            ws.write(count, 14, instance.whole_sale_price)
            ws.write(count, 15, instance.mrp)

            if instance.product.hsn:
                ws.write(count, 16, instance.product.hsn.hsn_number)

            ws.write(count, 17, instance.sgst)
            ws.write(count, 18, instance.cgst)
            # ws.write(count, 19, instance.cess)
            ws.write(count, 20, instance.first_time_stock)
            ws.write(count, 21, stock)
            ws.write(count, 22, instance.low_stock_limit)
            ws.write(count, 23, instance.discount_limit)
            ws.write(count, 24, instance.current_rating)
            ws.write(count, 25, instance.discount_limit)

            count += 1

    media_root = str(settings.MEDIA_ROOT) + '/products-excel.xls'
    wb.save(media_root)

    host_name = request.get_host()

    protocol = "http://"
    if request.is_secure():
        protocol = "https://"

    full_url = protocol + host_name + '/media/products-excel.xls'

    file_name = datetime.datetime.strftime(datetime.datetime.now(), '%d-%m-%Y - products-excel.xls')
    headers = {
        "Authorization": "Bearer ya29.A0ARrdaM_iYcNVNmnrzDV_2AJBlFMueWjSB5KaGqlx1PFTXMcnfbJj-32N9R1QPmIIM8YUFzfu0xc6UAAp1lPXE5jCIDFETWF3a9S3vmhnqwTil-S5E_1E-4I4ktInBJR8LIPRpQ9lV-peBZ3VKXKjBQgwT5qS"}
    parameters = {"name": file_name, "parents": ["1bRInRR0_4nDNO5EhJddFu-9F6BTZQ_Ps"]}

    files = {'data': ('metadata', json.dumps(parameters), 'application/json; charset=UTF-8'),
             'file': open(media_root, "rb")}
    post_function = requests.post("https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
                                  headers=headers, files=files)
    print(post_function.text)

    response_data = {"status": "true", "file_url": full_url}

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def get_product_hsn_detailes(request):
    pk = request.GET.get('hsn_id')
    if HsnCodes.objects.filter(pk=pk).exists():
        hsncode = HsnCodes.objects.filter(pk=pk)
        hsncodes = []
        for hsn in hsncode:
            hsncode_item = {'id': str(hsn.pk), 'igst': str(hsn.igst_rate), 'sgst': str(hsn.sgst_rate),
                            'cgst': str(hsn.cgst_rate), 'unit': str(hsn.unit.unit)}
            hsncodes.append(hsncode_item)
        response_data = {"status": "true", "hsncodes": hsncode_item, }
    else:
        response_data = {"status": "false", "message": "Students not added"}
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager','vendor_user'])
def create_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)

        if form.is_valid():
            auto_id = get_auto_id(Category)

            # create category
            data = form.save(commit=False)
            data.creator = request.user
            data.updater = request.user
            data.auto_id = auto_id
            data.is_admin_approved = True

            data.save()

            response_data = {"status": "true", "stable": "false", "title": "Successfully Created",
                             "message": "Product Category Created Successfully.", "redirect": "true",
                             "redirect_url": reverse('products:category', kwargs={'pk': data.pk})}

        else:
            message = generate_form_errors(form, formset=False)

            response_data = {"status": "false", "stable": "true", "title": "Form validatruetion error",
                             "message": str(message)}
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        print("HLOooooooooo")
        form = CategoryForm()
        context = {"title": "Create Product Category ", "form": form, "stable": "true",
                   "url": reverse('products:create_category'),

                   }
        return render(request, 'products/category/category_entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def categories(request):
    instances = Category.objects.filter(is_deleted=False)
    title = "Categories"
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(auto_id__icontains=query) | Q(name__icontains=query))
        title = "Categories - %s" % query

    context = {"instances": instances, 'title': title,

               }
    return render(request, 'products/category/categories.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def category(request, pk):
    instance = get_object_or_404(Category.objects.filter(pk=pk, is_deleted=False))
    instances = SubCategory.objects.filter(category=instance, is_deleted=False)
    initial = {'category': instance,

               }
    form = SubCategoryForm(initial=initial)
    context = {"form": form, "instance": instance, "instances": instances, "title": "Category : " + instance.name,
               "single_page": True,

               }
    return render(request, 'products/category/category.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def edit_category(request, pk):
    instance = get_object_or_404(Category.objects.filter(pk=pk, is_deleted=False))

    if request.method == 'POST':
        response_data = {}
        form = CategoryForm(request.POST, request.FILES, instance=instance)

        if form.is_valid():
            # update category
            data = form.save(commit=False)
            data.updater = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            response_data = {"status": "true", "title": "Successfully Updated",
                             "message": "Category Successfully Updated.", "redirect": "true",
                             "redirect_url": reverse('products:category', kwargs={'pk': data.pk})}
        else:
            message = generate_form_errors(form, formset=False)

            response_data = {"status": "false", "stable": "true", "title": "Form validation error",
                             "message": str(message)}

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:

        form = CategoryForm(instance=instance)

        context = {"form": form, "title": "Edit Category : " + instance.name, "instance": instance,
                   "url": reverse('products:edit_category', kwargs={'pk': instance.pk}), "redirect": True,

                   }
        return render(request, 'products/category/category_entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_category(request, pk):
    reason = request.GET.get('reason')
    instance = get_object_or_404(Category.objects.filter(pk=pk, is_deleted=False))

    if Product.objects.filter(is_deleted=False, category=instance).exists():
        response_data = {"status": "false", "stable": "true", "title": "Process Failed.!",
                         "message": "Category cannot be deleted since it has products. delete products first", }
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    if SubCategory.objects.filter(is_deleted=False, category=instance).exists():
        response_data = {"status": "false", "stable": "true", "title": "Process Failed.!",
                         "message": "Category cannot be deleted since it has sub-categories. delete Sub-categiee first", }
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    Category.objects.filter(pk=pk).update(is_deleted=True, name=instance.name + "_deleted_" + str(instance.auto_id),
                                          deleted_reason=reason)

    response_data = {"status": "true", "title": "Successfully Deleted", "message": "Category Successfully Deleted.",
                     "redirect": "true", "redirect_url": reverse('products:categories')}
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_selected_categories(request):
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(Category.objects.filter(pk=pk, is_deleted=False))
            Category.objects.filter(pk=pk).update(is_deleted=True,
                                                  name=instance.name + "_deleted_" + str(instance.auto_id))

        response_data = {"status": "true", "title": "Successfully Deleted",
                         "message": "Selected Categories Successfully Deleted.", "redirect": "true",
                         "redirect_url": reverse('products:categories')}
    else:
        response_data = {"status": "false", "title": "Nothing selected", "message": "Please select some items first.", }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


def get_subcategory(request):
    pk = request.GET.get('id')
    sale_type = request.GET.get('sale_type')

    if SubCategory.objects.filter(pk=pk).exists():
        subcategory = SubCategory.objects.get(pk=pk)
        name = subcategory.name
        category = subcategory.category
        category_pk = subcategory.category.pk

        response_data = {"status": 'true', "name": str(name), "category": str(category),
                         "category_pk": str(category_pk), }
    else:
        response_data = {"status": "false", "message": "SubCategory is not exists."}
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager','vendor_user'])
def create_subcategory(request):
    instances = SubCategory.objects.filter(is_deleted=False)
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(name__icontains=query) | Q(category__name=query))

    if request.method == 'POST':
        form = SubCategoryForm(request.POST)

        if form.is_valid():
            auto_id = get_auto_id(SubCategory)

            data = form.save(commit=False)
            data.is_admin_approved = True
            data.auto_id = auto_id
            data.creator = request.user
            data.updater = request.user

            data.save()

            response_data = {"status": "true", "title": "Successfully Created",
                             "message": "Product SubCategory Created Successfully.", "redirect": "true",
                             "redirect_url": reverse('products:subcategory', kwargs={'pk': data.pk})}
        else:
            message = generate_form_errors(form, formset=False)
            response_data = {"status": "false", "stable": "true", "title": "Form validation error",
                             "message": str(message)}

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        form = SubCategoryForm()

        context = {"title": "Create Product SubCategory", "form": form, "redirect": True,
                   "url": reverse('products:create_subcategory'), "products": True, "products": True, }
        return render(request, 'products/subcategory/subcategory_entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def subcategories(request):
    instances = SubCategory.objects.filter(is_deleted=False)
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(name__icontains=query) | Q(category__name=query))

    context = {'instances': instances, "title": 'subcategories', "products": True, "products": True, }
    return render(request, "products/subcategory/subcategories.html", context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def edit_subcategory(request, pk):
    instance = get_object_or_404(SubCategory.objects.filter(pk=pk, is_deleted=False))
    query = request.GET.get("q")
    if query:
        instance = instance.filter(Q(name__icontains=query) | Q(category__name=query))

    if request.method == "POST":
        form = SubCategoryForm(request.POST, instance=instance)

        if form.is_valid():
            data = form.save(commit=False)
            data.updater = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            response_data = {"status": "true", "title": "Successfully Updated",
                             "message": "SubCategory updated successfully.", "redirect": "true",
                             "redirect_url": reverse('products:subcategories')}
        else:
            message = generate_form_errors(form, formset=False)
            response_data = {"status": "false", "stable": "true", "title": "Form validation error",
                             "message": str(message)}

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        form = SubCategoryForm(instance=instance)

        context = {"instance": instance, "title": "Edit SubCategory :" + instance.name, "form": form, "redirect": True,
                   "url": reverse('products:edit_subcategory', kwargs={'pk': instance.pk}), "products": True,

                   }
        return render(request, 'products/subcategory/subcategory_entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def subcategory(request, pk):
    instance = get_object_or_404(SubCategory.objects.filter(pk=pk, is_deleted=False))

    context = {'instance': instance, 'title': 'SubCategory', "products": True, }
    return render(request, "products/subcategory/subcategory.html", context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_sub_category(request, pk):
    reason = request.GET.get('reason')
    instance = get_object_or_404(SubCategory.objects.filter(pk=pk, is_deleted=False))

    if Product.objects.filter(is_deleted=False, subcategory=instance).exists():
        response_data = {"status": "false", "stable": "true", "title": "Process Failed.!",
                         "message": "Subcategory cannot be deleted since it has products. delete products first", }
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    SubCategory.objects.filter(pk=pk).update(is_deleted=True, deleted_reason=reason)

    response_data = {"status": "true", "title": "Successfully Deleted", "message": "Sub Category Successfully Deleted.",
                     "redirect": "true", "redirect_url": reverse('products:subcategories')}
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_selected_subcategories(request):
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(SubCategory.objects.filter(pk=pk, is_deleted=False))
            SubCategory.objects.filter(pk=pk)

        response_data = {"status": "true", "title": "Successfully Deleted",
                         "message": "Selected Sub Category Successfully Deleted.", "redirect": "true",
                         "redirect_url": reverse('products:subcategories')}
    else:
        response_data = {"status": "false", "title": "Nothing selected", "message": "Please select some items first.", }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager','vendor_user'])
def create_brand(request):
    if request.method == 'POST':
        form = BrandForm(request.POST)

        if form.is_valid():
            auto_id = get_auto_id(Brand)

            # create brand
            data = form.save(commit=False)
            data.creator = request.user
            data.updater = request.user
            data.auto_id = auto_id
            data.is_admin_approved = True

            data.save()

            response_data = {"status": "true", "title": "Successfully Created",
                             "message": "Product Brand Created Successfully.", "redirect": "true",
                             "redirect_url": reverse('products:brand', kwargs={'pk': data.pk})}

        else:
            message = generate_form_errors(form, formset=False)

            response_data = {"status": "false", "stable": "true", "title": "Form validation error",
                             "message": str(message)}

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = BrandForm()
        context = {"title": "Create Product Brand ", "form": form, "url": reverse('products:create_brand'),

                   }
        return render(request, 'products/brand/brand_entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def brands(request):
    instances = Brand.objects.filter(is_deleted=False)
    title = "Brands"
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(auto_id__icontains=query) | Q(name__icontains=query))
        title = "Brands - %s" % query

    context = {"instances": instances, 'title': title,

               }
    return render(request, 'products/brand/brands.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def brand(request, pk):
    instance = get_object_or_404(Brand.objects.filter(pk=pk, is_deleted=False))
    context = {"instance": instance, "title": "Brand : " + instance.name, "single_page": True,

               }
    return render(request, 'products/brand/brand.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def edit_brand(request, pk):
    instance = get_object_or_404(Brand.objects.filter(pk=pk, is_deleted=False))

    if request.method == 'POST':
        response_data = {}
        form = BrandForm(request.POST, instance=instance)

        if form.is_valid():

            # update brand
            data = form.save(commit=False)
            data.updater = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            response_data = {"status": "true", "title": "Successfully Updated",
                             "message": "Brand Successfully Updated.", "redirect": "true",
                             "redirect_url": reverse('products:brand', kwargs={'pk': data.pk})}
        else:
            message = generate_form_errors(form, formset=False)

            response_data = {"status": "false", "stable": "true", "title": "Form validation error",
                             "message": str(message)}

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = BrandForm(instance=instance)

        context = {"form": form, "title": "Edit Brand : " + instance.name, "instance": instance,
                   "url": reverse('products:edit_brand', kwargs={'pk': instance.pk}), "redirect": True,

                   }
        return render(request, 'products/brand/brand_entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_brand(request, pk):
    reason = request.GET.get('reason')
    # instance = get_object_or_404(Brand.objects.filter(pk=pk, is_deleted=False))

    Brand.objects.filter(pk=pk).update(is_deleted=True, deleted_reason=reason)

    response_data = {"status": "true", "title": "Successfully Deleted", "message": "Brand Successfully Deleted.",
                     "redirect": "true", "redirect_url": reverse('products:brands')}
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_selected_brands(request):
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(Brand.objects.filter(pk=pk, is_deleted=False))
            Brand.objects.filter(pk=pk).update(is_deleted=True,
                                               name=instance.name + "_deleted_" + str(instance.auto_id))

        response_data = {"status": "true", "title": "Successfully Deleted",
                         "message": "Selected Brands Successfully Deleted.", "redirect": "true",
                         "redirect_url": reverse('products:brands')}
    else:
        response_data = {"status": "false", "title": "Nothing selected", "message": "Please select some items first.", }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def create_unit_measurement(request):
    if request.method == 'POST':
        form = UnitOfMeasurementForm(request.POST, request.FILES)

        if form.is_valid():
            auto_id = get_auto_id(UnitOfMeasurement)

            # create UnitOfMeasurementForm
            data = form.save(commit=False)
            data.creator = request.user
            data.updater = request.user
            data.auto_id = auto_id
            data.is_admin_approved = True

            data.save()

            response_data = {"status": "true", "stable": "false", "title": "Successfully Created",
                             "message": "Unit Measurement Created Successfully.", "redirect": "true",
                             "redirect_url": reverse('products:unit_measurement', kwargs={'pk': data.pk})}

        else:
            message = generate_form_errors(form, formset=False)

            response_data = {"status": "false", "stable": "true", "title": "Form validatruetion error",
                             "message": str(message)}
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        print("HLOooooooooo")
        form = UnitOfMeasurementForm()
        context = {"title": "Create Unit Measurement ", "form": form, "stable": "true",
                   "url": reverse('products:create_unit_measurement'),

                   }
        return render(request, 'products/unitmeasurement/unitmeasurement_entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def unit_measurements(request):
    instances = UnitOfMeasurement.objects.filter(is_deleted=False)
    title = "UnitOfMeasurement"
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(auto_id__icontains=query) | Q(unit_of_measurement__icontains=query))
        title = "UnitOfMeasurement - %s" % query

    context = {"instances": instances, 'title': title,

               }
    return render(request, 'products/unitmeasurement/unit_measurements.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def unit_measurement(request, pk):
    instance = get_object_or_404(UnitOfMeasurement.objects.filter(pk=pk, is_deleted=False))
    print(instance), "HHHHHHHHH"
    context = {"instance": instance, "title": "UnitOfMeasurement : " + instance.unit_of_measurement,
               "single_page": True,

               }
    return render(request, 'products/unitmeasurement/unit_measurement.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def edit_unit_measurement(request, pk):
    instance = get_object_or_404(UnitOfMeasurement.objects.filter(pk=pk, is_deleted=False))

    if request.method == 'POST':
        response_data = {}
        form = UnitOfMeasurementForm(request.POST, instance=instance)

        if form.is_valid():

            # update unit_measurement
            data = form.save(commit=False)
            data.updater = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            response_data = {"status": "true", "title": "Successfully Updated",
                             "message": "Unit Measurement Successfully Updated.", "redirect": "true",
                             "redirect_url": reverse('products:unit_measurement', kwargs={'pk': data.pk})}
        else:
            message = generate_form_errors(form, formset=False)

            response_data = {"status": "false", "stable": "true", "title": "Form validation error",
                             "message": str(message)}

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:

        form = UnitOfMeasurementForm(instance=instance)

        context = {"form": form, "title": "Edit Unit Measurement : " + instance.unit_of_measurement,
                   "instance": instance, "url": reverse('products:edit_unit_measurement', kwargs={'pk': instance.pk}),
                   "redirect": True,

                   }
        return render(request, 'products/unitmeasurement/unitmeasurement_entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_unit_measurement(request, pk):
    reason = request.GET.get('reason')
    instance = get_object_or_404(UnitOfMeasurement.objects.filter(pk=pk, is_deleted=False))

    instance.is_deleted = True
    instance.deleted_reason = reason
    instance.save()

    response_data = {"status": "true", "title": "Successfully Deleted",
                     "message": "Unit Measurement Successfully Deleted.", "redirect": "true",
                     "redirect_url": reverse('products:unit_measurements')}
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_selected_unit_measurement(request):
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(UnitOfMeasurement.objects.filter(pk=pk, is_deleted=False))
            instance.is_deleted = True
            instance.save()

        response_data = {"status": "true", "title": "Successfully Deleted",
                         "message": "Selected Unit Measurement Successfully Deleted.", "redirect": "true",
                         "redirect_url": reverse('products:unit_measurements')}
    else:
        response_data = {"status": "false", "title": "Nothing selected", "message": "Please select some items first.", }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def create_unit(request):
    instances = Unit.objects.filter(is_deleted=False)
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(unit__icontains=query) | Q(unit_of_measurement__unit_of_measurement=query))

    if request.method == 'POST':
        form = UnitForm(request.POST)

        if form.is_valid():
            auto_id = get_auto_id(Unit)

            data = form.save(commit=False)
            data.auto_id = auto_id
            data.creator = request.user
            data.updater = request.user
            data.is_admin_approved = True

            data.save()

            response_data = {"status": "true", "title": "Successfully Created", "message": "Unit Created Successfully.",
                             "redirect": "true", "redirect_url": reverse('products:unit', kwargs={'pk': data.pk})}
        else:
            message = generate_form_errors(form, formset=False)
            response_data = {"status": "false", "stable": "true", "title": "Form validation error",
                             "message": str(message)}

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        form = UnitForm()

        context = {"title": "Create Unit", "form": form, "redirect": True, "url": reverse('products:create_unit'), }
        return render(request, 'products/unit/unit_entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def units(request):
    instances = Unit.objects.filter(is_deleted=False)
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(unit__icontains=query) | Q(unit_of_measurement__unit_of_measurement=query))

    context = {'instances': instances, "title": 'units', }
    return render(request, "products/unit/units.html", context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def edit_unit(request, pk):
    instance = get_object_or_404(Unit.objects.filter(pk=pk, is_deleted=False))
    query = request.GET.get("q")
    if query:
        instance = instance.filter(Q(unit__icontains=query) | Q(unit_of_measurement__unit_of_measurement=query))

    if request.method == "POST":
        form = UnitForm(request.POST, instance=instance)

        if form.is_valid():
            data = form.save(commit=False)
            data.updater = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            response_data = {"status": "true", "title": "Successfully Updated", "message": "Unit updated successfully.",
                             "redirect": "true", "redirect_url": reverse('products:units')}
        else:
            message = generate_form_errors(form, formset=False)
            response_data = {"status": "false", "stable": "true", "title": "Form validation error",
                             "message": str(message)}

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        form = UnitForm(instance=instance)

        context = {"instance": instance, "title": "Edit Unit :" + instance.unit, "form": form, "redirect": True,
                   "url": reverse('products:edit_unit', kwargs={'pk': instance.pk}), "products": True,

                   }
        return render(request, 'products/unit/unit_entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def unit(request, pk):
    instance = get_object_or_404(Unit.objects.filter(pk=pk, is_deleted=False))

    context = {'instance': instance, 'title': 'Unit', "products": True, }
    return render(request, "products/unit/unit.html", context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_unit(request, pk):
    instance = get_object_or_404(Unit.objects.filter(pk=pk, is_deleted=False))

    instance.delete = True
    reason = request.GET.get('reason')
    instance.deleted_reason = reason
    instance.save()

    response_data = {"status": "true", "title": "Successfully Deleted", "message": "Unit Successfully Deleted.",
                     "redirect": "true", "redirect_url": reverse('products:units')}
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_selected_unit(request):
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(Unit.objects.filter(pk=pk, is_deleted=False))
            instance.is_deleted = True
            instance.save()

        response_data = {"status": "true", "title": "Successfully Deleted",
                         "message": "Selected Unit Successfully Deleted.", "redirect": "true",
                         "redirect_url": reverse('products:units')}
    else:
        response_data = {"status": "false", "title": "Nothing selected", "message": "Please select some items first.", }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def hsn_codes_create(request):
    if request.method == 'POST':
        form = HsnCodesForm(request.POST)

        if form.is_valid():
            auto_id = get_auto_id(HsnCodes)
            data = form.save(commit=False)
            data.creator = request.user
            data.updater = request.user
            data.auto_id = auto_id
            data.is_admin_approved = True

            data.save()

            # data = form.save(commit=False)
            # data.save()

            response_data = {"status": "true", "title": "Successfully Created",
                             "message": "HSN code created successfully.", "redirect": "true",
                             "redirect_url": reverse('products:hsn_code', kwargs={'pk': data.pk}), }

        else:
            message = generate_form_errors(form, formset=False)
            response_data = {"status": "false", "stable": "true", "title": "Form validation error",
                             "message": str(message)}

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = HsnCodesForm
        context = {"title": "Create HSNcode", "form": HsnCodesForm, "url": reverse('products:create_hsn_codes'),
                   "redirect": True,

                   }
        return render(request, 'products/hsn_codes/hsn_entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def hsn_codes(request):
    instances = HsnCodes.objects.filter(is_deleted=False)

    title = "HSN codes"
    query = request.GET.get("q")
    if query:
        instances = instances.filter(Q(name__icontains=query))
        title = "HSN code - %s" % query

    context = {"instances": instances, 'title': title,

               }
    return render(request, 'products/hsn_codes/hsn_codes.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def hsn_code(request, pk):
    instance = get_object_or_404(HsnCodes.objects.filter(pk=pk, is_deleted=False))
    context = {"instance": instance, "title": "HSN code : " + instance.name, "single_page": True,

               }
    return render(request, 'products/hsn_codes/hsn_code.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def edit_hsn_code(request, pk):
    instance = get_object_or_404(HsnCodes.objects.filter(pk=pk, is_deleted=False))

    if request.method == 'POST':
        response_data = {}
        form = HsnCodesForm(request.POST, instance=instance)

        if form.is_valid():

            # update brand
            data = form.save(commit=False)
            data.save()

            response_data = {"status": "true", "title": "Successfully Updated",
                             "message": "HSN code Successfully Updated.", "redirect": "true",
                             "redirect_url": reverse('products:hsn_code', kwargs={'pk': data.pk})}
        else:
            message = generate_form_errors(form, formset=False)

            response_data = {"status": "false", "stable": "true", "title": "Form validation error",
                             "message": str(message)}

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:

        form = HsnCodesForm(instance=instance)

        context = {"form": form, "title": "Edit HSN code : " + instance.name, "instance": instance,
                   "url": reverse('products:edit_hsn_code', kwargs={'pk': instance.pk}), "redirect": True,

                   }
        return render(request, 'products/hsn_codes/hsn_entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager','vendor_user'])
def delete_hsn_code(request, pk):
    reason = request.GET.get('reason')
    instance = get_object_or_404(HsnCodes.objects.filter(pk=pk, is_deleted=False))

    HsnCodes.objects.filter(pk=pk).update(is_deleted=True, name=instance.name + "_deleted_" + str(instance.id),
                                          deleted_reason=reason)

    response_data = {"status": "true", "title": "Successfully Deleted", "message": "HSN code Successfully Deleted.",
                     "redirect": "true", "redirect_url": reverse('products:hsn_codes_all')}
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_selected_hsn_codes(request):
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(HsnCodes.objects.filter(pk=pk, is_deleted=False))
            HsnCodes.objects.filter(pk=pk).update(is_deleted=True, name=instance.name + "_deleted_" + str(instance.id))

        response_data = {"status": "true", "title": "Successfully Deleted",
                         "message": "Selected HSC code Successfully Deleted.", "redirect": "true",
                         "redirect_url": reverse('products:hsn_codes_all')}
    else:
        response_data = {"status": "false", "title": "Nothing selected", "message": "Please select some items first.", }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def create_barcode(request):
    warehouse = None
    product_variant = None
    qty = request.GET.get('qty')
    product_pk = request.GET.get('product')
    variant_pk = request.GET.get('product_variant')

    if variant_pk:
        product_variant = get_object_or_404(ProductVariant.objects.filter(pk=variant_pk))

    unit = 10
    if qty:
        if qty.isdigit():
            unit = qty
    warehouse = get_warehouse(request)

    form = ProductBarcodeForm(initial={"unit": unit, "product_variant": product_variant, 'warehouse': warehouse})

    context = {'title': "Create Barcode", "form": form, }

    return render(request, 'products/create_barcode.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def print_barcodes(request):
    date = datetime.datetime.now().date()
    unit = request.GET.get('unit')
    if not unit:
        unit = 1
    else:
        unit = int(unit)

    skip_row = request.GET.get('skip_row')
    if not skip_row:
        skip_row = 0
    else:
        skip_row = int(skip_row)

    variant_pk = request.GET.get('product_variant')
    batch_pk = request.GET.get('batch')
    instance = None
    product_name = ''
    batch_instance = None

    if variant_pk and batch_pk:
        instance = get_object_or_404(ProductVariant.objects.filter(pk=variant_pk, is_deleted=False))
        batch_instance = get_object_or_404(Batch.objects.filter(pk=batch_pk, is_deleted=False))

        title = "Barcodes : " + instance.title
        product_name = instance.product.name + " - " + instance.title

    n_range = range(0, unit)

    padding_top = 10.9
    additional_padding = skip_row * 21.2
    padding_top += additional_padding

    context = {'title': title, 'date': date, "instance": instance, "batch_instance": batch_instance,
               "product_name": product_name, "n_range": n_range, "padding_top": padding_top

               }
    return render(request, 'products/print_barcodes.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def update_varying_product_price(request):
    VaryingProductPriceFormset = formset_factory(VaryingProductPriceForm, extra=0)

    product_variants = ProductVariant.objects.filter(is_deleted=False, is_admin_approved=True, product__is_varying_price=True)
    batches = Batch.objects.filter(is_deleted=False, stock__gt=0, product_variant__in=product_variants)

    if request.method == 'POST':
        product_varying_formset = VaryingProductPriceFormset(request.POST, prefix='product_varying_formset',
                                                             form_kwargs={'empty_permitted': False})

        if product_varying_formset.is_valid():
            error_messages = ''
            price_ok = True

            # for varying_product in product_varying_formset:
            for i in product_varying_formset:
                variant_id = i.cleaned_data['variant_id']
                retail_price = i.cleaned_data['retail_price']
                whole_sale_price = i.cleaned_data['whole_sale_price']
                mrp = i.cleaned_data['mrp']
                variant = product_variants.get(pk=variant_id)

                # retail_price
                if (Decimal(mrp) - Decimal(retail_price)) < 0:
                    error_messages += f'Retail price is greater than MRP of variant {variant}.\n'
                    price_ok = False

                # whole_sale_price
                if (Decimal(mrp) - Decimal(whole_sale_price)) < 0:
                    error_messages += f'Whole Sale price is greater than MRP of variant {variant}.\n'
                    price_ok = False

            if not price_ok:
                response_data = {"status": "false", "stable": "true", "title": "Form validation error",
                                 "message": str(error_messages)}

                return HttpResponse(json.dumps(response_data), content_type='application/javascript')

            for i in product_varying_formset:
                variant_id = i.cleaned_data['variant_id']
                retail_price = i.cleaned_data['retail_price']
                whole_sale_price = i.cleaned_data['whole_sale_price']
                mrp = i.cleaned_data['mrp']

                batches.filter(product_variant_id=variant_id).update(mrp=mrp, retail_price=retail_price,
                                                                     whole_sale_price=whole_sale_price)

            response_data = {"status": "true", "title": "Successfully Updated",
                             "message": "Selected Price Successfully Updated.", "redirect": "true",
                             "redirect_url": reverse('products:update_varying_product_price')}
            return HttpResponse(json.dumps(response_data), content_type='application/javascript')

        else:
            print(product_varying_formset.errors, "ghhhhhhh")
            message = generate_form_errors(product_varying_formset, formset=True)

            response_data = {"status": "false", "stable": "true", "title": "Form validation error",
                             "message": str(message)}

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        initial = []

        for variant in product_variants:
            batch = batches.filter(product_variant_id=variant.pk).first()

            if batch:
                retail_price = batch.retail_price
                whole_sale_price = batch.whole_sale_price
                mrp = batch.mrp
            else:
                retail_price = variant.retail_price
                whole_sale_price = variant.whole_sale_price
                mrp = variant.mrp

            dic = {"variant_id": variant.pk, "title": str(variant), "retail_price": retail_price,
                   "whole_sale_price": whole_sale_price, "mrp": mrp, }
            initial.append(dic)

        product_varying_formset = VaryingProductPriceFormset(prefix='product_varying_formset', initial=initial)

        context = {"title": "Update Varying Prices ",

                   "product_varying_formset": product_varying_formset,
                   "url": reverse('products:update_varying_product_price'), 'redirect': True,
                   'is_no_need_autocomplete': True}

        return render(request, 'products/update_varying_product_price.html', context)


@login_required
def export_variants(request, pk):
    instances = ProductVariant.objects.filter(product__pk=pk, is_admin_approved=True)
    export_to_excel_utils = ExportToExcelUtils(ProductVariant, VariantExportSerializer, request,
                                               "product_variants_export")
    returned_file_url = export_to_excel_utils.export_to_excel_single_objects(instances)
    return HttpResponseRedirect(returned_file_url)


@login_required
def export_products(request):
    instances = Product.objects.filter(is_deleted=False)
    export_to_excel_utils = ExportToExcelUtils(instances, ProductExportSerializer, request, "product_export")
    returned_file_url = export_to_excel_utils.export_to_excel()
    return HttpResponseRedirect(returned_file_url)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def enable_or_disable_product(request, pk):
    try:
        instance = get_object_or_404(Product.objects.filter(pk=pk, is_deleted=False))

        instance.is_active = not instance.is_active
        instance.save()

        update_type = "Enabled" if instance.is_active else "Disabled"

        response_data = {
            "status": "true",
            "reload": 'true',
            "title": f"Successfully {update_type}",
            "message": f"{instance} has been successfully {update_type}",
        }
    except:
        response_data = {}
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
def export_variants_to_pdf(request, pk):
    instance = Product.objects.get(pk=pk)
    instances_manager = InstancesManager(request)
    variants = instances_manager.get_product_variant_instances_depend_on_params(instance)

    context = {"product": instance, "variants": variants,}

    return render_to_pdf('products/variant_pdf.html', context)


@login_required
@role_required(['superadmin', 'vendor_user'])
def update_variant_stock(request,pk):
    product_variant = ProductVariant.objects.get(pk=pk)
    batches = Batch.objects.filter(product_variant=product_variant)

    if request.method == 'POST':
        stock = request.POST.get('stock', 0)

        if product_variant.product.vendor:
            try:
                stock = Decimal(stock)
                if batches.count() == 1:
                    batches.update(stock = stock)
                else:
                    batch = batches.first()
                    batch.stock = stock
                    batch.save()

                product_variant.stock = stock
                product_variant.save()

                response_data = {
                    "status": "true",
                    "title": "Successfully Updated",
                    "message": "Product stock updated successfully.",
                    "reload": "true"
                }
            except Exception as e:
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Validation Failed",
                    "message": f"Incorrect input value in Available Stock.\n {e}",
                }
        else:
            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Validation Failed",
                "message": f"Cannot update stock of products that doesn't belong to any vendor",
            }

    else:
        template_name = 'products/includes/stock_modal.html'
        context = {
            'batches': batches,
            'product_variant':product_variant,
        }
        html_content = render_to_string(template_name, context, request=request)

        response_data = {
            "status": "true",
            "modal":html_content
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')

