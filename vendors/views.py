# Standard libraries
import datetime
import json
from decimal import Decimal
from customers.models import CustomerAddress
# third party libraries
from dal import autocomplete
# django libraries
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Max
from django.db.models.functions import Lower
from django.http.response import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.forms.formsets import formset_factory
# Local libraries
from main.decorators import ajax_required, role_required
from main.functions import get_auto_id, generate_form_errors, get_date_updated_request
from finance.models import AccountHead, InvoicePrefix
from sales.models import SaleItem
from products.functions import get_category_by_pk, get_vendor_by_pk, get_subcategory_by_pk
from products.forms import CategoryForm, BrandForm, VendorSubCategoryForm, VendorUOMForm, HsnCodesForm, VendorProductForm, VendorVariantForm
from products.models import Category, Brand, Product, SubCategory, UnitOfMeasurement, HsnCodes, ProductVariant, ProductImages, Batch
from orders.models import *
from vendors.models import Vendor
from vendors.forms import VendorForm
from vendors.utils.vendor_functions_manager import VendorFunctionsManager
from vendors.utils.vendor_utils import create_user_of_vendor
from vendors.utils.form_utils import FormUtils
from vendors.functions import get_vendor_categories, get_vendor_brands, if_vendor_is_user
from warehouses.models import Warehouse
from web.functions import get_order_prefix


class VendorAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        vendor = Vendor.objects.filter(is_deleted=False)

        if self.q:
            vendor = vendor.filter(Q(name__istartswith=self.q))

        return vendor


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def add_new_vendor(request):
    if request.method == 'POST':
        form = VendorForm(request.POST)

        if form.is_valid():
            name = form.cleaned_data['name']
            opening_type = form.cleaned_data['opening_type']
            opening_balance = form.cleaned_data['opening_balance']
            opening_type = form.cleaned_data['opening_type']
            opening_balance = form.cleaned_data['opening_balance']
            is_ok = True

            if is_ok:
                auto_id = get_auto_id(Vendor)
                name = name.title()

                data = form.save(commit=False)
                data.auto_id = auto_id
                data.opening_type = opening_type
                data.opening_balance = opening_balance
                data.name = name
                data.creator = request.user
                data.updater = request.user
                current_balance = 0
                if opening_type == 'debit':
                    current_balance += opening_balance
                elif opening_type == 'credit':
                    current_balance -= opening_balance
                data.current_balance = current_balance
                data.save()

                response_data = {
                    "status": "true",
                    "title": "Successfully Created",
                    "message": "Vendor created successfully.",
                    "redirect": "true",
                    "redirect_url": reverse('purchases:create_new_purchase')
                }
            else:
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": "Opening Debit and Opening Credit can't be positive at the same time."
                }

        else:
            message = generate_form_errors(form, formset=False)
            print(form.errors)
            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": str(message)
            }
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def create_vendor(request):
    if request.method == 'POST':
        form = VendorForm(request.POST, request.FILES)

        if form.is_valid():
            name = form.cleaned_data['name']
            opening_type = form.cleaned_data['opening_type']
            opening_balance = form.cleaned_data['opening_balance']

            # for creating user for vendor
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            is_ok = True
            error_message = ""
            if User.objects.filter(username=username).exists():
                is_ok = False
                error_message = "A user with this username already exist."

            if is_ok:
                auto_id = get_auto_id(Vendor)
                name = name.title()

                data = form.save(commit=False)
                data.auto_id = auto_id
                data.opening_type = opening_type
                data.opening_balance = opening_balance
                data.name = name
                data.creator = request.user
                data.updater = request.user
                data.password = password
                current_balance = 0

                if opening_type == 'debit':
                    current_balance += opening_balance
                elif opening_type == 'credit':
                    current_balance -= opening_balance

                data.current_balance = current_balance

                # create django user funtion
                user = create_user_of_vendor(username, password)
                data.user = user

                data.save()

                response_data = {
                    "status": "true",
                    "title": "Successfully Created",
                    "message": "Vendor created successfully.",
                    "redirect": "true",
                    "redirect_url": reverse('vendors:vendors')
                }
            else:
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": error_message
                }

        else:
            message = generate_form_errors(form, formset=False)
            print(form.errors)
            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": str(message)
            }
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = VendorForm()

        context = {
            "title": "Create Vendor",
            "form": form,
            "redirect": "true",
            "url": reverse('vendors:create_vendor'),
            "is_create": True,
        }

        return render(request, 'vendor/entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def vendors(request):
    instances = Vendor.objects.filter(is_deleted=False).order_by(Lower('name'))

    query = request.GET.get("q")
    sort_by = request.GET.get('sort_by')
    order_by = request.GET.get('order_by')

    instances = instances.annotate(
        lower_name=Lower('name'),
        lower_email=Lower('email'),
        lower_phone=Lower('phone'),
        lower_address=Lower('address')
    )

    if not order_by:
        order_by = 'asc'

    if not sort_by:
        sort_by = 'name'

    if sort_by == 'id':
        sort_by = 'auto_id'
        if order_by == 'asc':
            instances = instances.order_by('auto_id')
        else:
            instances = instances.order_by('-auto_id')

    elif sort_by == 'name':
        if order_by != 'asc':
            instances = instances.order_by('-lower_name')

    elif sort_by == 'email':
        if order_by == 'asc':
            instances = instances.order_by('lower_email')
        else:
            instances = instances.order_by('-lower_email')

    elif sort_by == 'phone':
        if order_by == 'asc':
            instances = instances.order_by('lower_phone')
        else:
            instances = instances.order_by('-lower_phone')

    elif sort_by == 'address':
        if order_by == 'asc':
            instances = instances.order_by('lower_address')
        else:
            instances = instances.order_by('-lower_address')

    if query:
        instances = instances.filter(
            Q(name__icontains=query) |
            Q(address__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query)
        )

    filter_data = {'query': query, 'sort_by': sort_by, 'order_by': order_by, }

    context = {
        "title": 'Vendors',
        'instances': instances,
        'filter_data': filter_data,
    }
    return render(request, 'vendor/vendors.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def edit_vendor(request, pk):
    instance = get_object_or_404(Vendor.objects.filter(pk=pk, is_deleted=False))

    current_balance = instance.current_balance
    old_opening_balance = instance.opening_balance
    if instance.opening_type == 'debit':
        current_balance -= old_opening_balance
    elif instance.opening_type == 'credit':
        current_balance += old_opening_balance

    if request.method == "POST":
        form = VendorForm(request.POST, request.FILES, instance=instance)

        if form.is_valid():
            # update vendor
            name = form.cleaned_data['name']
            opening_type = form.cleaned_data['opening_type']
            opening_balance = form.cleaned_data['opening_balance']
            name = name.title()

            is_ok = True
            error_message = ""

            if not instance.user:
                # for creating user for vendor
                username = form.cleaned_data['username']
                password = form.cleaned_data['password']

                if User.objects.filter(username=username).exists():
                    is_ok = False
                    error_message = "A user with this username already exist."

            if is_ok:
                data = form.save(commit=False)
                data.name = name
                data.updater = request.user
                data.date_updated = datetime.datetime.now()

                if opening_type == 'debit':
                    current_balance += opening_balance
                elif opening_type == 'credit':
                    current_balance -= opening_balance

                if not instance.user:
                    pass

                if not instance.user:
                    # create django user funtion
                    user = create_user_of_vendor(username, password)
                    data.user = user

                data.current_balance = current_balance
                data.save()

                response_data = {
                    "status": "true",
                    "title": "Successfully Updated",
                    "message": "Vendor updated successfully.",
                    "redirect": "true",
                    "redirect_url": reverse('vendors:vendors')
                }

            else:
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": error_message
                }
        else:
            message = generate_form_errors(form, formset=False)

            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        form = VendorForm(instance=instance)

        context = {
            "form": form,
            "redirect": "true",
            "is_create": False if instance.user else True,
            "instance": instance,
            "title": "Edit Vendor :" + instance.name,
            "url": reverse('vendors:edit_vendor', kwargs={'pk': instance.pk}),
        }

        return render(request, 'vendor/entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def vendor(request, pk):
    instance = get_object_or_404(Vendor.objects.filter(pk=pk, is_deleted=False))

    sale_items = SaleItem.objects.filter(product_variant__product__vendor=instance).order_by('-id')[:10]
    order_items = OrderItem.objects.filter(product_variant__product__vendor=instance).order_by('-id')[:10]
    products = Product.objects.filter(is_deleted=False, vendor_id=pk)

    context = {
        'title': 'Vendor',
        'instance': instance,
        'products': products,
        'sale_items': sale_items,
        'order_items': order_items,
    }

    return render(request, "vendor/vendor.html", context)


@login_required
@ajax_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_vendor(request, pk):
    reason = request.GET.get('reason')
    Vendor.objects.filter(pk=pk).update(is_deleted=True, deleted_reason=reason)

    response_data = {
        "status": "true",
        "title": "Successfully Deleted",
        "message": "Vendor deleted successfully.",
        "redirect": "true",
        "redirect_url": reverse('vendors:vendors')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@ajax_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_selected_vendors(request):
    pks = request.GET.get('pk')

    if pks:
        pks = pks[:-1]
        pks = pks.split(',')

        for pk in pks:
            instance = get_object_or_404(Vendor.objects.filter(pk=pk, is_deleted=False))
            Vendor.objects.filter(pk=pk).update(is_deleted=True, name=instance.name + "_deleted_" + str(instance.auto_id))

        response_data = {
            "status": "true",
            "title": "Successfully Deleted",
            "message": "Selected Vendor Successfully Deleted.",
            "redirect": "true",
            "redirect_url": reverse('vendors:vendors')
        }
    else:

        response_data = {
            "status": "false",
            "title": "Nothing selected",
            "message": "Please select some items first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@ajax_required
@login_required
def get_vendors(request):
    data = []
    if Vendor.objects.filter(is_deleted=False, ).exists():
        instances = Vendor.objects.filter(is_deleted=False, ).order_by('name').values_list('name', 'pk')

        for i in instances:
            obj = {'name': i[0], 'pk': str(i[1])}
            data.append(obj)

        response_data = {
            "status": "true",
            "model": 'Vendor',
            "instances": data
        }
    else:
        response_data = {
            "status": "false",
            "message": "No vendors found"
        }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


def get_vendor_data(request):
    pk = request.GET.get('id')

    if Vendor.objects.filter(pk=pk, is_deleted=False, ).exists():
        vendor = Vendor.objects.get(pk=pk)
        state = vendor.state
        commission_percentage = vendor.commission_percentage
        commission_type = vendor.commission_type

        response_data = {
            "status": 'true',
            "state": str(state),
            "commission_percentage": str(commission_percentage),
            "commission_type": str(commission_type),
        }

    else:
        response_data = {
            "status": "false",
            "message": "Vendor is not exists."
        }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
def get_balance(request):
    pk = request.GET.get('id')
    instance = Vendor.objects.get(pk=pk, is_deleted=False)
    # balance = get_vender_balance(instance.pk)

    head = AccountHead.objects.filter(name='Sundry Creditor (Vendor)', is_deleted=False).last()
    today = datetime.datetime.now().date()

    if instance:
        response_data = {
            "status": "true",
            'current_balance': float(instance.current_balance),
        }
    else:
        response_data = {
            "status": "false",
            "message": "Vendor not found"
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['vendor_user', ])
def vendor_categories(request):
    query = request.GET.get('query') or "category"
    condition = request.GET.get('condition') or "all"

    is_vendor = if_vendor_is_user(request)
    instances = Category.objects.filter(is_deleted=False)
    title = "All Categories"

    if condition != "all":
        if is_vendor:
            title = title.replace("All", 'My')
            instances = instances.filter(creator=request.user)

        if condition == "non-approved":
            instances = instances.filter(is_admin_approved=None)
        elif condition == "approved":
            instances = instances.filter(is_admin_approved=True)
        elif condition == "cancelled":
            instances = instances.filter(is_admin_approved=False)
    else:
        instances = instances.filter(is_admin_approved=True)

    context = {
        "title": title,
        "query": query,
        "is_vendor": is_vendor,
        "instances": instances,
        "condition": condition,
    }

    return render(request, 'vendor/vendors_activities.html', context)


@login_required
@role_required(['vendor_user'])
def vendor_sub_categories(request):
    query = request.GET.get('query') or "sub-category"
    condition = request.GET.get('condition') or "all"

    is_vendor = if_vendor_is_user(request)

    instances = SubCategory.objects.filter(is_deleted=False)
    title = "All Sub-categories"

    if condition != "all":
        if is_vendor:
            title = title.replace("All", 'My')
            instances = instances.filter(creator=request.user)

        if condition == "non-approved":
            instances = instances.filter(is_admin_approved=None)
        elif condition == "approved":
            instances = instances.filter(is_admin_approved=True)
        elif condition == "cancelled":
            instances = instances.filter(is_admin_approved=False)
    else:
        instances = instances.filter(is_admin_approved=True)

    context = {
        'title': title,
        "query": query,
        "is_vendor": is_vendor,
        "instances": instances,
        "condition": condition,
    }
    return render(request, 'vendor/vendors_activities.html', context)


@login_required
@role_required(['vendor_user'])
def vendor_brands(request):
    query = request.GET.get('query') or "brands"
    condition = request.GET.get('condition') or "all"

    is_vendor = if_vendor_is_user(request)

    instances = Brand.objects.filter(is_deleted=False)
    title = "All Brands"

    if condition != "all":
        if is_vendor:
            title = title.replace("All", 'My')
            instances = instances.filter(creator=request.user)

        if condition == "non-approved":
            instances = instances.filter(is_admin_approved=None)
        elif condition == "approved":
            instances = instances.filter(is_admin_approved=True)
        elif condition == "cancelled":
            instances = instances.filter(is_admin_approved=False)
    else:
        instances = instances.filter(is_admin_approved=True)

    context = {
        "query": query,
        'title': title,
        "condition": condition,
        "instances": instances,
        "is_vendor": is_vendor,
    }
    return render(request, 'vendor/vendors_activities.html', context)


@login_required
@role_required(['vendor_user'])
def vendor_products(request):
    query = request.GET.get('query') or "products"
    condition = request.GET.get('condition') or "all"

    is_vendor = if_vendor_is_user(request)

    instances = ProductVariant.objects.filter(is_deleted=False)
    title = "All Products"

    if is_vendor:
        title = title.replace("All", 'My')
        instances = instances.filter(Q(creator=request.user) | Q(product__vendor__user=request.user))

        if condition == "non-approved":
            instances = instances.filter(is_admin_approved=None)
        elif condition == "approved":
            instances = instances.filter(is_admin_approved=True)
        elif condition == "cancelled":
            instances = instances.filter(is_admin_approved=False)
    else:
        instances = None

    context = {
        "query": query,
        'title': title,
        "condition": condition,
        "instances": instances,
        "is_vendor": is_vendor,
    }
    return render(request, 'vendor/vendors_activities.html', context)


@login_required
@role_required(['vendor_user'])
def vendor_create_category(request):
    if request.method == 'POST':
        form_utils = FormUtils(request, CategoryForm, Category)
        response = form_utils.save_form_data()

        if response['status']:
            response_data = {
                "status": "true",
                "redirect": "true",
                "title": "Successfully Created",
                "message": "Product Category Created Successfully.",
                "redirect_url": reverse('products:vendor_categories') + "?query=pending"
            }
        else:
            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validatruetion error",
                "message": str(response['message'])
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = CategoryForm()
        context = {
            "title": "Create Product Category ",
            "form": form,
            "url": reverse('vendors:vendor_create_category'),
        }

        return render(request, 'products/category/category_entry.html', context)


@login_required
@role_required(['vendor_user'])
def vendor_create_brand(request):
    if request.method == 'POST':
        form_utils = FormUtils(request, BrandForm, Brand)
        response = form_utils.save_form_data()

        if response['status']:
            response_data = {
                "status": "true",
                "title": "Successfully Created",
                "message": "Brand Created Successfully.",
                "redirect": "true",
                "redirect_url": reverse('products:brand', kwargs={'pk': response['pk']})
            }
        else:
            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": str(response['message'])
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = BrandForm()
        context = {
            "title": "Create Brand ",
            "form": form,
            "stable": "true",
            "url": reverse('vendors:vendor_create_brand'),
        }

        return render(request, 'products/brand/brand_entry.html', context)


@login_required
@role_required(['vendor_user'])
def vendor_create_sub_category(request):
    if request.method == 'POST':
        form_utils = FormUtils(request, VendorSubCategoryForm, SubCategory)
        response = form_utils.save_form_data()

        if response['status']:
            response_data = {
                "status": "true",
                "title": "Successfully Created",
                "message": "Sub category Created Successfully.",
                "redirect": "true",
                "redirect_url": reverse('products:subcategory', kwargs={'pk': response['pk']})
            }
        else:
            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": str(response['message'])
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = VendorSubCategoryForm()
        context = {
            "title": "Create Sub Category ",
            "form": form,
            "url": reverse('vendors:vendor_create_sub_category'),
        }

        return render(request, 'create.html', context)


@login_required
@role_required(['vendor_user', ])
def vendor_create_product(request):
    ProductVariantFormset = formset_factory(VendorVariantForm, extra=1)

    if request.method == 'POST':
        ModifiedRequest = get_date_updated_request(request.POST.copy(), ['expire_date'])

        form = VendorProductForm(request.POST, request.FILES)
        product_variation_formset = ProductVariantFormset(request.POST, request.FILES, prefix='product_variation_formset', form_kwargs={'empty_permitted': False})

        if form.is_valid() and product_variation_formset.is_valid():
            error_messages = ''
            image = form.cleaned_data['image']
            product_name = form.cleaned_data['name']

            price_ok = True
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
                vendor = request.user.vendor
                # name = name.title()

                if auto_id < 10:
                    product_code = "PR00%s" % str(auto_id)
                elif auto_id >= 10 and auto_id < 100:
                    product_code = "PR0%s" % str(auto_id)
                else:
                    product_code = "PR%s" % str(auto_id)

                # create product
                data = form.save(commit=False)
                data.is_admin_approved = None
                data.vendor_created = True
                data.gst_included = True
                data.vendor = vendor

                data.creator = request.user
                data.updater = request.user
                data.auto_id = auto_id
                data.save()

                count = 0
                for i in product_variation_formset:
                    uploaded_files = request.FILES.getlist(f'product_variation_formset-{count}-images')

                    count += 1

                    if i.cleaned_data != {}:
                        image = i.cleaned_data['image']
                        title = i.cleaned_data['title']
                        cost = i.cleaned_data['cost']
                        mrp = i.cleaned_data['mrp']
                        is_default = i.cleaned_data['is_default']
                        retail_price = i.cleaned_data['retail_price']
                        whole_sale_price = i.cleaned_data['whole_sale_price']

                        discount_limit = i.cleaned_data['discount_limit']
                        product_code = i.cleaned_data['product_code']
                        unit = i.cleaned_data['unit']
                        sgst = i.cleaned_data['sgst']
                        cgst = i.cleaned_data['cgst']
                        igst = i.cleaned_data['igst']

                        stock = 0 # i.cleaned_data['first_time_stock']
                        batch_number = 0 # i.cleaned_data['batch_number']
                        manufacturing_date = datetime.datetime.now() # i.cleaned_data['manufacturing_date']
                        expire_date = datetime.datetime.now() # i.cleaned_data['expire_date']
                        low_stock_limit = 0 # i.cleaned_data['low_stock_limit']

                        product_variant = ProductVariant.objects.create(
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
                            vendor_created = True,

                            sgst=sgst,
                            cgst=cgst,
                            igst=igst,
                            mrp=mrp,
                            cost=cost,
                            retail_price=retail_price,
                            whole_sale_price=whole_sale_price,

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
            message1 = generate_form_errors(form, formset=False)
            message3 = generate_form_errors(product_variation_formset, formset=True)

            message = str(message1) + str(message3)

            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": str(message)
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        product_form = VendorProductForm()
        product_variation_formset = ProductVariantFormset(prefix='product_variation_formset',)

        context = {
            "title": "Create Product ",
            "form": product_form,
            "product_variation_formset": product_variation_formset,
            "url": reverse('products:create'),
            'redirect': True,
            'is_edit': False,
            'is_no_need_autocomplete': True
        }

    return render(request, 'vendor/product_entry.html', context)


@login_required
@role_required(['vendor_user', ])
def vendor_create_hsn_code(request):

    if request.method == 'POST':
        form_utils = FormUtils(request, HsnCodesForm, HsnCodes)
        response = form_utils.save_form_data()

        if response['status']:
            response_data = {
                "status": "true",
                "stable": "false",
                "title": "Successfully Created",
                "message": "HSN Code Created Successfully.",
                "redirect": "true",
                "redirect_url": reverse('products:hsn_code', kwargs={'pk': response['pk']})
            }
        else:
            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Please check twice",
                "message": str(response['message'])
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = HsnCodesForm()
        context = {
            "title": "Create HSN Code",
            "form": form,
            "stable": "true",
            "url": reverse('vendors:vendor_create_hsn_code'),
        }

        return render(request, 'create.html', context)


@login_required
@role_required(['vendor_user', ])
def vendor_view_hsn_code(request):
    vendor_functions = VendorFunctionsManager()
    instances = vendor_functions.get_hsn_codes(request.user)

    instances = instances.filter(creator=request.user)

    title = "Vendor HSN Codes"

    query = request.GET.get('query')
    condition = request.GET.get('condition')

    context = {
        "instances": instances,
        'title': title,
        "query": query,
        "condition": condition
    }
    return render(request, 'vendor/hsn_codes.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def vendor_activities(request):
    query = request.GET.get('query') or "products"
    condition = request.GET.get('condition') or "non-approved"
    is_vendor = if_vendor_is_user(request)

    if query == "category":
        instances = Category.objects.filter(is_deleted=False, vendor_created=True)
        title = "All Categories"
    elif query == "sub-category":
        instances = SubCategory.objects.filter(is_deleted=False, vendor_created=True)
        title = "All Sub-categories"
    elif query == "brands":
        instances = Brand.objects.filter(is_deleted=False, vendor_created=True)
        title = "All Brands"
    elif query == "products":
        instances = ProductVariant.objects.filter(is_deleted=False, vendor_created=True)
        title = "All Products"
    else:
        instances = Product.objects.none()
        title = "Vendor Activities"

    if condition != "all":
        if is_vendor:
            title = title.replace("All", 'My')
            if query == "products":
                instances = instances.filter(Q(creator=request.user) | Q(vendor__user=request.user))
            else:
                instances = instances.filter(creator=request.user)

        if condition == "non-approved":
            instances = instances.filter(is_admin_approved=None)
        elif condition == "approved":
            instances = instances.filter(is_admin_approved=True)
        elif condition == "cancelled":
            instances = instances.filter(is_admin_approved=False)

    context = {
        "title": title,
        "query": query,
        "is_vendor": is_vendor,
        "condition": condition,
        "instances": instances,
        "url": reverse('vendors:vendor_activities'),
    }

    return render(request, 'vendor/vendors_activities.html', context)


@ajax_required
@role_required(['superadmin', 'warehouse_manager'])
def approve_vendor_item(request, item_type, pk):
    try:
        if item_type == 'category':
            instance = Category.objects.get(pk=pk)
        elif item_type == 'sub-category':
            instance = SubCategory.objects.get(pk=pk)
        elif item_type == 'brands':
            instance = Brand.objects.get(pk=pk)
        elif item_type == 'products':
            instance = ProductVariant.objects.get(pk=pk)

        instance.date_updated = datetime.datetime.now()
        instance.is_admin_approved = True
        instance.updater = request.user
        instance.save()

        response_data = {
            "status": "true",
            "title": "Successfully Approved",
            "message": f"{instance} has been approved successfully.",
            "redirect": "true",
            "redirect_url": reverse('vendors:vendor_activities') + f"?query={item_type}"
        }
    except Exception as e:
        print('------------------------------\n',e)
        response_data = {
            "status": "false",
            "stable": "true",
            "title": "Failed to Approve",
            "message": f"There was an error finding the instance. \nPlease try again after refreshing",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@ajax_required
@role_required(['superadmin', 'warehouse_manager'])
def decline_vendor_item(request, item_type, pk):
    try:
        if item_type == 'category':
            instance = Category.objects.get(pk=pk)
        elif item_type == 'sub-category':
            instance = Category.objects.get(pk=pk)
        elif item_type == 'brands':
            instance = Brand.objects.get(pk=pk)
        elif item_type == 'products':
            instance = ProductVariant.objects.get(pk=pk)

        instance.date_updated = datetime.datetime.now()
        instance.is_admin_approved = False
        instance.updater = request.user
        instance.save()

        response_data = {
            "status": "true",
            "title": "Successfully Decalined",
            "message": f"{instance} has been declined successfully.",
            "redirect": "true",
            "redirect_url": reverse('vendors:vendor_activities') + f"?query={item_type}"
        }
    except Exception as e:
        print('------------------------------\n',e)

        response_data = {
            "status": "false",
            "stable": "true",
            "title": "Failed to Delete",
            "message": f"There was an error finding the instance. \nPlease try again after refreshing",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@ajax_required
@role_required(['superadmin', 'warehouse_manager'])
def approve_vendor_product(request, pk):
    instance = ProductVariant.objects.get(pk=pk)

    commission_percentage = request.POST.get('commission')

    instance.commission_percentage = commission_percentage
    instance.date_updated = datetime.datetime.now()
    instance.is_admin_approved = True
    instance.updater = request.user
    instance.save()

    product = instance.product
    product.is_active = True
    product.save()

    if product.vendor.location:
        warehouse = Warehouse.objects.filter(location=product.vendor.location).first()

        if not Batch.objects.filter(product=product, product_variant=instance).exists():
            Batch.objects.create(
                product = product,
                product_variant = instance,
                warehouse = warehouse,
                creator = request.user,
                updater = request.user,
                auto_id = get_auto_id(Batch),

                batch_number = "DFLT0",
                stock = instance.first_time_stock,
                mrp = instance.mrp,
                retail_price = instance.retail_price,
                whole_sale_price = instance.whole_sale_price,
                cost = instance.cost,
                manufacturing_date = instance.manufacturing_date,
                expire_date = instance.expire_date,
            )

    if not product.productvariant_set.filter(is_deleted=False).exclude(is_admin_approved=True).exists():
        Product.objects.filter(pk=instance.product_id).update(is_admin_approved=True)

    response_data = {
        "status": "true",
        "title": "Successfully Approved",
        "message": f"{instance} has been approved successfully.",
        "redirect": "true",
        "redirect_url": reverse('vendors:vendor_activities') + f"?query=products"
    }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@ajax_required
@role_required(['superadmin', 'warehouse_manager'])
def decline_vendor_product(request, pk):
    instance = ProductVariant.objects.get(pk=pk)

    instance.date_updated = datetime.datetime.now()
    instance.is_admin_approved = False
    instance.updater = request.user
    instance.save()

    response_data = {
        "status": "true",
        "title": "Successfully Declined",
        "message": f"{instance} has been declined successfully.",
        "redirect": "true",
        "redirect_url": reverse('vendors:vendor_activities') + f"?query=products"
    }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager', 'vendor_user'])
def received_orders(request, status):
    instances = OrderItem.objects.filter(product_variant__product__vendor__user=request.user, order__is_deleted=False)

    if status == 'pending':
        instances = instances.filter(order__order_status='10')
    elif status == 'shipped':
        instances = instances.filter(order__order_status='20')
    elif status == 'delivered':
        instances = instances.filter(order__order_status='30')
    elif status == 'cancelled':
        instances = instances.filter(order__order_status='40')

    context = {
        'title': f'My {status.title()} Orders',
        'status': status,
        'instances': instances,
    }

    return render(request, "vendor/order_items.html", context)


@login_required
@role_required(['superadmin', 'warehouse_manager', 'vendor_user'])
def received_order(request, pk):
    instance = get_object_or_404(OrderItem.objects.filter(pk=pk))

    context = {
        "title": "Order : " + str(instance.order.order_id),
        "instance": instance,
    }
    return render(request, 'vendor/order_item.html', context)


@ajax_required
@role_required(['superadmin', 'warehouse_manager','vendor_user'])
def update_order_status(request, status, pk):
    try:
        if status == '20':
            value = 20
        elif status == '30':
            value = 30
        elif status == '40':
            value = 40
       
        instance = OrderItem.objects.get(pk=pk)
        instance.status = value
        instance.save()

        response_data = {
            "status": "true",
            "title": "Successfully Updated",
            "message": f"{instance} has been successfully updated.",
        }
    except Exception as e:
        print('------------------------------\n',e)
        response_data = {
            "status": "false",
            "stable": "true",
            "title": "Failed to Update",
            "message": f"There was an error finding the instance. \nPlease try again after refreshing",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager', 'vendor_user'])
def bookings(request):
    instances = Booking.objects.filter(is_deleted=False, product_variant__product__vendor__user=request.user, status="pending")

    context = {
        "title": "All Bookings",
        "instances": instances,
        "pending_order": True,
    }
    return render(request, 'vendor/bookings/bookings.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager', 'vendor_user'])
def booking(request, pk):
    instance = get_object_or_404(Booking.objects.filter(pk=pk))

    context = {
        "title": "Booking : " + str(instance.order_id),
        "instance": instance,
    }
    return render(request, 'vendor/bookings/booking.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager', 'vendor_user'])
def accept_booking(request, pk, address_pk):
    booking_instance = Booking.objects.get(pk=pk)
    address_instance = CustomerAddress.objects.get(pk=address_pk)

    variant = booking_instance.product_variant
    pincode = address_instance.pincode.pincode
    customer_instance = address_instance.customer

    batch = None
    if variant.product.vendor:
        batch = Batch.objects.filter(is_deleted=False, warehouse__location__pincode=pincode, product_variant=variant).first()
    elif Batch.objects.filter(is_deleted=False, warehouse__location__pincode=pincode, product_variant=variant).exists():
        batch = Batch.objects.filter(is_deleted=False, warehouse__location__pincode=pincode, product_variant=variant).first()

    else:
        response_data = {
            "status": "false",
            "title": "Batch Not Found",
            "message": "Batch Not Found on Customers preferred location",
            "redirect": "true",
            "redirect_url": reverse('vendors:bookings')
        }
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    order_id = get_order_prefix()
    order_no = 0
    prefix = None

    if InvoicePrefix.objects.filter(is_active=True, is_deleted=False).exists():
        prefix = InvoicePrefix.objects.get(is_active=True, is_deleted=False)
        pr_orders = Orders.objects.filter(prefix=prefix)

        if pr_orders.filter(prefix=prefix).exists():
            order_no = pr_orders.filter(prefix=prefix).aggregate(Max('order_no'))['order_no__max']

        order_no += 1
        order_id = f"{prefix.order}{str(order_no).zfill(6)}"

    order = Orders.objects.create(
        auto_id=get_auto_id(Orders),
        creator=request.user,
        updater=request.user,
        customer=customer_instance,
        billing_name=address_instance.name,
        billing_phone=address_instance.phone,
        billing_address=address_instance.house_name,
        billing_street=address_instance.street,
        billing_landmark=address_instance.landmark,
        billing_city=address_instance.city,
        billing_state=address_instance.state,
        order_status=10,
        total_amt=variant.mrp,
        payment_method="cod",
        payment_status=10,
        order_no=order_no,
        order_id=order_id,
        prefix=prefix,
        warehouse=batch.warehouse,
    )

    OrderItem.objects.create(
        product_variant=variant,
        qty="1",
        price=variant.mrp,
        order=order,
        batch=batch,
    )

    booking_instance.status = "confirmed"
    booking_instance.save()

    response_data = {
        "status": "true",
        "title": "Accept Booking",
        "message": "Successfully Accepted Booking.",
        "redirect": "true",
        "redirect_url": reverse('orders:bookings')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager', 'vendor_user'])
def accepted_bookings(request):
    instances = Booking.objects.filter(is_deleted=False, product_variant__product__vendor__user=request.user, status="confirmed")

    context = {
        "title": "All Bookings",
        "instances": instances,
        "accepted_order": True
    }

    return render(request, 'vendor/bookings/bookings.html', context)
