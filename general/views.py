import xlwt
import json
import datetime
from decimal import Decimal
from itertools import product
from operator import attrgetter, itemgetter
# third party libraries
from dal import autocomplete
# django libraries
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import formats
from django.conf import settings
from django.urls import reverse
from django.http.response import HttpResponseRedirect, HttpResponse
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.db.models import Q, F, Sum, Count, FloatField, ExpressionWrapper
from django.http import JsonResponse
from django.forms.formsets import formset_factory
from django.forms.models import inlineformset_factory
# local libraries
from main.decorators import check_mode, ajax_required
from main.functions import get_auto_id, generate_form_errors, get_date_updated_request
from sales.functions import update_batch_stock
from products.models import ProductVariant,Product
from general.models import DamagedProducts, Batch, StockTransfer, StockTransferItem
from general.forms import DamagedProductsForm, StockTransferItemForm, StockTransferForm
from main.decorators import role_required
from general.models import StockUpdateItem,StockUpdate,InvoiceDesign
from general.forms import StockUpdateForm,StockUpdateItemForm,StockInwardItemEditForm,StockOutWardItemForm,InvoiceDesignForm


@login_required
def create_damaged_product(request):
    if request.method == 'POST':
        ModifiedRequest = get_date_updated_request(request.POST.copy(), ['date'])
        form = DamagedProductsForm(ModifiedRequest)

        if form.is_valid():
            auto_id = get_auto_id(DamagedProducts)
            amount = form.cleaned_data['amount']
            batch = form.cleaned_data['batch']
            quantity = form.cleaned_data['quantity']
            product_variant = form.cleaned_data['product_variant']

            error_message = ''
            is_ok = True
            if batch:
                if quantity > batch.stock:
                    is_ok = False
                    error_message += f'Not Enough Stock in batch - {batch}'
            else:
                is_ok = False
                error_message += 'Please choose a batch\n'

            if is_ok:
                data = form.save(commit=False)
                data.creator = request.user
                data.updater = request.user
                data.auto_id = auto_id

                data.product_variant = product_variant
                data.save()

                try:
                    Batch.objects.filter(pk=batch.pk).update(
                        stock=F('stock') - quantity
                    )
                except:
                    print(
                        '-\n-\n-\n-\n-\n-\n stock updation failed at create damaged product\n-\n-\n-\n-\n-\n-')

                if product_variant:
                    product_variant.stock = product_variant.total_stock()
                    product_variant.save()

                response_data = {
                    "status": "true",
                    "title": "Successfully Created",
                    "message": "Damaged Product created successfully.",
                    "redirect": "true",
                    "redirect_url": reverse('general:damaged_product', kwargs={'pk': data.pk})
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
        initial = {
            'date': datetime.datetime.strftime(datetime.datetime.now(), '%d/%m/%Y')
        }
        form = DamagedProductsForm(initial=initial)

        form.fields['product_variant'].queryset = ProductVariant.objects.none()
        form.fields['batch'].queryset = Batch.objects.none()

        context = {
            "title": "Create Damaged Product ",
            "form": form,
            "url": reverse('general:create_damaged_product'),
            "redirect": True,
        }
        return render(request, 'general/damaged-products/entry_damaged_product.html', context)


@login_required
def damaged_products(request):
    instances = DamagedProducts.objects.all()
    title = "Damaged Products"
    filter_data = {}

    query = request.GET.get("q")
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    if from_date and to_date:
        filter_data = {
            'from_date': from_date,
            'to_date': to_date
        }
        from_date = datetime.datetime.strptime(from_date, '%d/%m/%Y')
        to_date = datetime.datetime.strptime(to_date, '%d/%m/%Y')
        instances = instances.filter(date__date__range=[from_date, to_date])

    if query:
        title = "Damaged Products - %s" % query
        instances = instances.filter(
            Q(product__name__icontains=query)
        )

    context = {
        'title': title,
        "instances": instances,
        'filter_data': filter_data,
        "total_amount": "",
    }

    return render(request, 'general/damaged-products/damaged_products.html', context)


@login_required
def damaged_product(request, pk):
    instance = get_object_or_404(
        DamagedProducts.objects.filter(pk=pk))

    context = {
        "instance": instance,
        "title": "Damaged Product : #" + str(instance.auto_id),
    }

    return render(request, 'general/damaged-products/damaged_product.html', context)


@login_required
def edit_damaged_product(request, pk):
    instance = get_object_or_404(
        DamagedProducts.objects.filter(pk=pk, is_deleted=False))
    old_batch = instance.batch
    old_quantity = instance.quantity
    error_message = ''

    if request.method == 'POST':
        form = DamagedProductsForm(
            request.POST, instance=instance)

        if form.is_valid():
            is_ok = True
            batch = form.cleaned_data['batch']
            quantity = form.cleaned_data['quantity']

            if batch == old_batch:
                batch_stock = batch.stock + old_quantity
                if quantity > batch_stock:
                    is_ok = False
                    error_message += f'Not Enough Stock in batch - {batch}'

            else:
                if quantity > batch.stock:
                    is_ok = False
                    error_message += f'Not Enough Stock in batch - {batch}'

            if is_ok:
                # returning old stock to batch
                Batch.objects.filter(pk=old_batch.pk).update(
                    stock=F('stock') + old_quantity
                )

                if old_batch.product_variant:
                    old_batch.product_variant.stock = old_batch.product_variant.total_stock()
                    old_batch.product_variant.save()

                data = form.save(commit=False)
                data.updater = request.user
                data.is_updated = True
                data.date_updated = datetime.datetime.now()
                data.save()

                try:
                    Batch.objects.filter(pk=batch.pk).update(
                        stock=F('stock') - quantity
                    )
                except:
                    print(
                        '-\n-\n-\n-\n-\n-\n stock updation failed at edit damaged product\n-\n-\n-\n-\n-\n-')

                response_data = {
                    "status": "true",
                    "title": "Successfully Updated",
                    "message": "Damaged Product Successfully Updated.",
                    "redirect": "true",
                    "redirect_url": reverse('general:damaged_product', kwargs={'pk': data.pk})
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
        initial = {
            'date': datetime.datetime.strftime(instance.date, '%d/%m/%Y')
        }

        form = DamagedProductsForm(
            instance=instance, initial=initial)

        form.fields['product_variant'].queryset = ProductVariant.objects.none()
        form.fields['batch'].queryset = Batch.objects.none()

        context = {
            "form": form,
            "title": "Edit Damaged Product : " + str(instance.auto_id),
            "instance": instance,
            "url": reverse('general:edit_damaged_product', kwargs={'pk': instance.pk}),
            "is_edit": True,
        }

        return render(request, 'general/damaged-products/entry_damaged_product.html', context)


@login_required
def delete_damaged_product(request, pk):
    reason = request.GET.get('reason')
    instance = get_object_or_404(
        DamagedProducts.objects.filter(pk=pk, is_deleted=False))
    instance.is_deleted = True
    instance.deleted_reason = reason
    instance.save()

    quantity = instance.quantity

    if instance.batch:
        Batch.objects.filter(pk=instance.batch_id).update(
            stock=F('stock') + quantity
        )

        if instance.product_variant:
            instance.product_variant.stock = instance.product_variant.total_stock()
            instance.product_variant.save()

    response_data = {
        "status": "true",
        "title": "Successfully Deleted",
        "message": "Damaged Product Successfully Deleted.",
        "redirect": "true",
        "redirect_url": reverse('general:damaged_products')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


def get_batch_data(request):
    pk = request.GET.get('id')
    sale_type = request.GET.get('sale_type')
    print(sale_type, "*********************")

    if Batch.objects.filter(pk=pk).exists():
        batch = Batch.objects.get(pk=pk)
        sgst_p = batch.product_variant.product.hsn.sgst_rate
        cgst_p = batch.product_variant.product.hsn.cgst_rate
        cost = batch.cost
        taxable_amount_batch = round(cost/(1+(sgst_p/100)+(cgst_p/100)), 2)

        if sale_type == "b2b":
            price = str(round(batch.whole_sale_price, 2))
        elif sale_type == "b2c":
            price = str(round(batch.retail_price, 2))
        else:
            price = ""

        response_data = {
            "status": 'true',
            "stock": str(batch.stock),
            "mrp": str(batch.mrp),
            "price": price,
            "price": price,
            "cost": str(batch.cost),
            "last_cost": str(taxable_amount_batch),
            "expire_date": str(batch.expire_date),
            "manufacturing_date": str(batch.manufacturing_date),
            "retail_price": str(batch.retail_price),
            "whole_sale_price": str(batch.whole_sale_price),
        }
    else:
        response_data = {
            "status": "false",
            "message": "Batch is not exists."
        }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def create_stock_transfer(request):
    StockTransferItemFormset = formset_factory(StockTransferItemForm, extra=1)

    if request.method == 'POST':
        form = StockTransferForm(request.POST)
        stock_transfer_formset = StockTransferItemFormset(
            request.POST, prefix='stock_transfer_formset', form_kwargs={'empty_permitted': False})

        if form.is_valid() and stock_transfer_formset.is_valid():
            to_warehouse = form.cleaned_data['to_warehouse']
            warehouse = form.cleaned_data['warehouse']

            stock_items = {}  # to check stock availability
            stock_ok = True
            error_message = ''

            for f in stock_transfer_formset:
                if f.cleaned_data != {}:
                    batch = f.cleaned_data['batch']
                    product_variant = f.cleaned_data['product_variant']

                    if batch:
                        product_variant = f.cleaned_data['product_variant']
                        batch = f.cleaned_data['batch']
                        qty = f.cleaned_data['quantity']

                        obj = {
                            'batch': batch,
                            "quantity": qty,
                        }

                        # to check stock availability
                        if str(batch.pk) in stock_items:
                            stock_items[str(batch.pk)]['quantity'] += qty
                        else:
                            stock_items[str(batch.pk)] = obj

                    else:
                        if Batch.objects.filter(is_deleted=False, product_variant=product_variant, warehouse=warehouse, stock__gt=0).exists():
                            error_message = "Please choose a batch before submission."

                        else:
                            name = product_variant.product.name + product_variant.title
                            error_message = f"{name} is out of stock."

                        response_data = {
                            "status": "false",
                            "stable": "true",
                            "title": "Form validation error",
                            "message": error_message
                        }
                        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

            for key, value in stock_items.items():
                batch = Batch.objects.get(pk=key)
                product = batch.product
                product_variant = batch.product
                stock = batch.stock
                name = product.name

                quantity = value['quantity']

                if quantity > stock:
                    stock_ok = False
                    error_message += f"{name} has only {stock} quantity in batch {batch}, You entered {quantity} quantity\n"

            if stock_ok:
                auto_id = get_auto_id(StockTransfer)

                # create stock_transfer
                data = form.save(commit=False)
                data.creator = request.user
                data.updater = request.user
                data.auto_id = auto_id

                data.save()

                for i in stock_transfer_formset:
                    stock_transfer_auto_id = get_auto_id(StockTransferItem)

                    if i.cleaned_data != {}:
                        product_variant = i.cleaned_data['product_variant']
                        batch = i.cleaned_data['batch']
                        quantity = i.cleaned_data['quantity']
                        manufacturing_date = i.cleaned_data['manufacturing_date']
                        expire_date = i.cleaned_data['expire_date']
                        mrp = i.cleaned_data['mrp']
                        retail_price = i.cleaned_data['retail_price']
                        whole_sale_price = i.cleaned_data['whole_sale_price']
                        cost = i.cleaned_data['cost']

                        StockTransferItem.objects.create(
                            stock_transfer=data,
                            quantity=quantity,

                            product_variant=product_variant,
                            batch=batch,
                            manufacturing_date=manufacturing_date,
                            expire_date=expire_date,
                            mrp=mrp,
                            cost=cost,
                            retail_price=retail_price,
                            whole_sale_price=whole_sale_price,

                            auto_id=stock_transfer_auto_id,
                            creator=request.user,
                            updater=request.user,
                        )

                        # subtracting stock from from_warehouse
                        update_batch_stock(batch.pk, quantity, "decrease")

                        # adding stock to to_warehouse
                        if Batch.objects.filter(is_deleted=False, batch_number=batch.batch_number, product_variant=product_variant, warehouse=to_warehouse).exists():
                            Batch.objects.filter(is_deleted=False, batch_number=batch.batch_number, product_variant=product_variant, warehouse=to_warehouse).update(
                                stock=F('stock') + quantity,
                                mrp=mrp,
                                cost=cost,
                                retail_price=retail_price,
                                whole_sale_price=whole_sale_price,
                                expire_date=expire_date,
                                manufacturing_date=manufacturing_date,
                            )

                            batch = Batch.objects.get(
                                is_deleted=False, batch_number=batch.batch_number, product_variant=product_variant, warehouse=to_warehouse)

                        else:
                            batch = Batch.objects.create(
                                auto_id=get_auto_id(Batch),
                                creator=request.user,
                                updater=request.user,
                                warehouse=to_warehouse,
                                product_variant=product_variant,
                                product=product_variant.product,

                                stock=quantity,
                                batch_number=batch.batch_number,
                                mrp=mrp,
                                retail_price=retail_price,
                                whole_sale_price=whole_sale_price,
                                cost=cost,
                                expire_date=expire_date,
                                manufacturing_date=manufacturing_date,
                            )

                response_data = {
                    "status": "true",
                    "title": "Successfully Created",
                    "message": "Stock Transfer Created Successfully.",
                    "redirect": "true",
                    "redirect_url": reverse('general:stock_transfer', kwargs={'pk': data.pk})
                }
            else:
                message = 'Sorry..! Not Enough Stock '
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
                "message": str(message)
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = StockTransferForm()
        stock_transfer_formset = StockTransferItemFormset(
            prefix='stock_transfer_formset')

        context = {
            "title": "Create Stock Transfer ",
            "form": form,
            "stock_transfer_formset": stock_transfer_formset,
            "url": reverse('general:create_stock_transfer'),
        }

        return render(request, 'general/stock_transfer/stock_transfer_entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def stock_transfers(request):
    instances = StockTransfer.objects.filter(is_deleted=False)
    title = "Stock Transfer"
    query = request.GET.get("q")
    if query:
        instances = instances.filter(
            Q(auto_id__icontains=query) | Q(name__icontains=query))
        title = "Stock Transfer - %s" % query

    context = {
        "instances": instances,
        'title': title,

    }
    return render(request, 'general/stock_transfer/stock_transfers.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def stock_transfer(request, pk):
    instance = get_object_or_404(
        StockTransfer.objects.filter(pk=pk, is_deleted=False))
    stock_transfers = StockTransferItem.objects.filter(
        stock_transfer=instance, is_deleted=False)

    context = {
        "instance": instance,
        "stock_transfers": stock_transfers,
        "title": "Stock Transfer : " + str(instance.auto_id),
        "single_page": True,

    }
    return render(request, 'general/stock_transfer/stock_transfer.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def edit_stock_transfer(request, pk):
    instance = get_object_or_404(StockTransfer, pk=pk)
    old_stockupdate_items = StockTransferItem.objects.filter(
        stock_transfer_id=pk)

    if StockTransferItem.objects.filter(stock_transfer_id=instance).exists():
        extra = 0
    else:
        extra = 1

    StockTransferItemFormset = inlineformset_factory(
        StockTransfer,
        StockTransferItem,
        can_delete=True,
        extra=extra,
        form=StockTransferItemForm
    )

    old_warehouse = instance.warehouse
    old_to_warehouse = instance.to_warehouse

    if request.method == 'POST':
        response_data = {}
        form = StockTransferForm(request.POST, instance=instance)
        stock_transfer_formset = StockTransferItemFormset(
            request.POST, prefix='stock_transfer_formset', form_kwargs={'empty_permitted': False})

        if form.is_valid() and stock_transfer_formset.is_valid():
            warehouse = form.cleaned_data['warehouse']
            to_warehouse = form.cleaned_data['to_warehouse']

            stock_ok = True
            stock_items = {}
            error_message = ''

            for f in stock_transfer_formset:
                if f.cleaned_data != {}:
                    batch = f.cleaned_data['batch']
                    qty = f.cleaned_data['quantity']

                    obj = {
                        'batch': batch,
                        "quantity": qty,
                    }

                    # to check stock availability
                    if str(batch.pk) in stock_items:
                        stock_items[str(batch.pk)]['quantity'] += qty

                    else:
                        stock_items[str(batch.pk)] = obj

            for key, value in stock_items.items():
                batch = Batch.objects.get(pk=key)

                stock = batch.stock
                product_variant = batch.product_variant

                old_qty = 0
                if old_stockupdate_items.filter(batch=batch).exists():
                    old_qty = old_stockupdate_items.filter(
                        batch=batch).aggregate(Sum('quantity'))['quantity__sum']

                stock = stock + old_qty
                quantity = value['quantity']

                if quantity > stock:
                    stock_ok = False
                    error_message += f"{product_variant} has only {stock} in stock in batch {batch}, You entered {quantity} quantity\n"

            if stock_ok:
                for stock_transfer in old_stockupdate_items:
                    # increasing transfered stock in from_warehouse
                    quantity = stock_transfer.quantity
                    batch = stock_transfer.batch
                    update_batch_stock(batch.pk, quantity, "increase")

                    # decreasing received stock in to_warehouse
                    to_batch = Batch.objects.get(
                        batch_number=batch.batch_number, product_variant=stock_transfer.product_variant, warehouse=old_to_warehouse)
                    update_batch_stock(to_batch.pk, quantity, "decrease")

                old_stockupdate_items.delete()

                # update stock_transfer
                data = form.save(commit=False)
                data.updater = request.user
                data.date_updated = datetime.datetime.now()
                data.save()

                for i in stock_transfer_formset:
                    stock_transfer_auto_id = get_auto_id(StockTransferItem)

                    if i.cleaned_data != {}:
                        quantity = i.cleaned_data['quantity']
                        cost = i.cleaned_data['cost']
                        mrp = i.cleaned_data['mrp']
                        batch = i.cleaned_data['batch']
                        manufacturing_date = i.cleaned_data['manufacturing_date']
                        expire_date = i.cleaned_data['expire_date']
                        retail_price = i.cleaned_data['retail_price']
                        whole_sale_price = i.cleaned_data['whole_sale_price']
                        product_variant = i.cleaned_data['product_variant']

                        stock_transfer_data = StockTransferItem.objects.create(
                            stock_transfer=data,
                            quantity=quantity,

                            product_variant=product_variant,
                            batch=batch,
                            manufacturing_date=manufacturing_date,
                            expire_date=expire_date,
                            mrp=mrp,
                            cost=cost,
                            retail_price=retail_price,
                            whole_sale_price=whole_sale_price,

                            auto_id=stock_transfer_auto_id,
                            creator=request.user,
                            updater=request.user,
                        )
                        update_batch_stock(batch.pk, quantity, "decrease")

                        if Batch.objects.filter(is_deleted=False, batch_number=batch.batch_number, product_variant=product_variant, warehouse=to_warehouse).exists():
                            Batch.objects.filter(is_deleted=False, batch_number=batch.batch_number, product_variant=product_variant, warehouse=to_warehouse).update(
                                stock=F('stock') + quantity,
                                mrp=mrp,

                                cost=cost,
                                retail_price=retail_price,
                                whole_sale_price=whole_sale_price,
                                expire_date=expire_date,
                                manufacturing_date=manufacturing_date,
                            )

                            batch = Batch.objects.get(
                                is_deleted=False, batch_number=batch.batch_number, product_variant=product_variant, warehouse=to_warehouse)

                        else:
                            batch = Batch.objects.create(
                                auto_id=get_auto_id(Batch),
                                creator=request.user,
                                updater=request.user,

                                warehouse=to_warehouse,
                                product_variant=product_variant,
                                product=product_variant.product,

                                batch_number=batch.batch_number,
                                stock=quantity,
                                mrp=mrp,
                                retail_price=retail_price,
                                whole_sale_price=whole_sale_price,
                                cost=cost,
                                expire_date=expire_date,
                                manufacturing_date=manufacturing_date,
                            )

                response_data = {
                    "status": "true",
                    "title": "Successfully Updated",
                    "message": "StockTransfer Successfully Updated.",
                    "redirect": "true",
                    "redirect_url": reverse('general:stock_transfer', kwargs={'pk': data.pk})
                }
            else:
                message = 'Sorry..! Not Enough Stock '
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": error_message
                }

            response_data = {
                "status": "true",
                "title": "Successfully Updated",
                "message": "Stock Transfer Successfully Updated.",
                "redirect": "true",
                "redirect_url": reverse('general:stock_transfer', kwargs={'pk': data.pk})
            }
        else:
            message = generate_form_errors(form, formset=False)
            print(stock_transfer_formset.errors)

            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": str(message)
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = StockTransferForm(instance=instance)
        stock_transfer_formset = StockTransferItemFormset(
            prefix='stock_transfer_formset', instance=instance)

        context = {
            "form": form,
            "instance": instance,
            "title": "Edit Stock Transfer : " + str(instance.auto_id),
            'stock_transfer_formset': stock_transfer_formset,
            "url": reverse('general:edit_stock_transfer', kwargs={'pk': instance.pk}),
            "redirect": True,
            "is_edit": True,
        }

        return render(request, 'general/stock_transfer/stock_transfer_entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_stock_transfer(request, pk):
    reason = request.GET.get('reason')
    instance = get_object_or_404(
        StockTransfer.objects.filter(pk=pk, is_deleted=False))
    transfer_items = StockTransferItem.objects.filter(stock_transfer=instance)

    warehouse = instance.warehouse
    to_warehouse = instance.to_warehouse

    # to check stock availability in received warehouse
    stock_items = {}
    stock_ok = True
    error_message = ''

    for item in transfer_items:
        product_variant = item.product_variant
        qty = item.quantity
        batch = item.batch

        obj = {
            'batch': batch,
            "quantity": qty,
        }

        # to check stock availability
        if str(batch.pk) in stock_items:
            stock_items[str(batch.pk)]['quantity'] += qty

        else:
            stock_items[str(batch.pk)] = obj

    # Checking the stock available for this product
    for key, value in stock_items.items():
        batch = Batch.objects.get(pk=key)
        product_variant = batch.product_variant

        to_batch = Batch.objects.get(is_deleted=False, batch_number=batch.batch_number,
                                     product_variant=product_variant, warehouse=to_warehouse)

        stock = to_batch.stock
        quantity = value['quantity']

        if quantity > stock:
            stock_ok = False

            error_message += f"{product_variant} has only {stock} in stock in batch {to_batch}, You entered {quantity} quantity\n"

    if stock_ok:
        StockTransfer.objects.filter(pk=pk).update(is_deleted=True,deleted_reason=reason)

        for item in transfer_items:
            batch = item.batch

            to_batch = Batch.objects.get(is_deleted=False, batch_number=batch.batch_number,
                                         product_variant=product_variant, warehouse=to_warehouse)
            update_batch_stock(to_batch.pk, quantity, "decrease")
            update_batch_stock(batch.pk, quantity, "increase")

        response_data = {
            "status": "true",
            "title": "Successfully Deleted",
            "message": "Stock Transfer Successfully Deleted.",
            "redirect": "true",
            "redirect_url": reverse('general:stock_transfers')
        }

    else:
        response_data = {
            "status": "false",
            "stable": "true",
            "title": "Cancellation Failed..!",
            "message": error_message
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


def create_inward_stock(request):
    StockUpdateItemFormset = formset_factory(StockUpdateItemForm,extra=1)

    if request.method == 'POST':
        batch_ok = False
        form = StockUpdateForm(request.POST)
        stock_update_item_formset = StockUpdateItemFormset(request.POST,prefix="stock_update_item_formset")

        if form.is_valid() and stock_update_item_formset.is_valid():
            warehouse = form.cleaned_data['warehouse']

            for f in stock_update_item_formset:
                mrp = f.cleaned_data['mrp']
                cost = f.cleaned_data['cost']
                retail_price = f.cleaned_data['retail_price']
                whole_sale_price = f.cleaned_data['whole_sale_price']
                product_variant = f.cleaned_data['product_variant']
                error_message = ''
                batch_ok = True

                if product_variant:
                    product_name = str(product_variant)


                if (Decimal(mrp) - Decimal(retail_price)) < 0 :
                    error_message += f'Selling Retail Price is greater than MRP of {product_name}.\n'
                    batch_ok = False
                if (Decimal(retail_price) - Decimal(cost)) < 0:
                    error_message += f'Cost is greater than selling retail Price of {product_name}.\n'
                    batch_ok = False

                if (Decimal(mrp) - Decimal(whole_sale_price)) < 0 :
                    error_message += f'Selling Whole Sale Price is greater than MRP of {product_name}.\n'
                    batch_ok = False
                if (Decimal(whole_sale_price) - Decimal(cost)) < 0:
                    error_message += f'Cost is greater than selling Whole Sale Price of {product_name}.\n'
                    batch_ok = False

            if not batch_ok:
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": str(error_message)
                }

                return HttpResponse(json.dumps(response_data), content_type='application/javascript')

            auto_id = get_auto_id(StockUpdate)

            data = form.save(commit=False)
            data.creator = request.user
            data.updater = request.user
            data.auto_id = auto_id
            data.save()

            for f in stock_update_item_formset:
                batch = f.cleaned_data['batch']
                batch_number = f.cleaned_data['batch_number']
                add_new_batch = f.cleaned_data['add_new_batch']
                product_variant = f.cleaned_data['product_variant']

                mrp = f.cleaned_data['mrp']
                cost = f.cleaned_data['cost']
                retail_price = f.cleaned_data['retail_price']
                whole_sale_price = f.cleaned_data['whole_sale_price']
                quantity = f.cleaned_data['stock']
                expire_date = f.cleaned_data['expire_date']
                manufacturing_date = f.cleaned_data['manufacturing_date']

                # cess = product.hsn.cess_rate
                cgst = product_variant.product.hsn.cgst_rate
                sgst = product_variant.product.hsn.sgst_rate

                total_tax_rate =  cgst + sgst
                taxable_amount = (cost / (1 + (total_tax_rate / 100)))

                if add_new_batch:
                    batch = None
                    if not batch_number:
                        batch_number = '0DEFLT'
                else:
                    if batch:
                        batch_number = batch.batch_number
                    else:
                        batch_number = '0DEFLT'
                # batch_number = batch_number.upper()

                if Batch.objects.filter(batch_number=batch_number, product_variant=product_variant).exists():
                    Batch.objects.filter(batch_number=batch_number, product_variant=product_variant).update(
                        stock = F('stock') + quantity,
                        mrp = mrp,
                        retail_price=retail_price,
                        whole_sale_price=whole_sale_price,
                        cost = cost,
                        expire_date = expire_date,
                        manufacturing_date = manufacturing_date
                    )

                    batch = Batch.objects.get(batch_number=batch_number, product_variant=product_variant)

                else:
                    batch = Batch.objects.create(
                        auto_id=get_auto_id(Batch),
                        mrp=mrp,
                        stock=quantity,
                        creator=request.user,
                        updater=request.user,
                        warehouse=warehouse,
                        # selling_price=batch_price,
                        batch_number=batch_number,
                        product_variant=product_variant,
                        product=product_variant.product,
                        cost = cost,
                        retail_price=retail_price,
                        whole_sale_price=whole_sale_price,
                        expire_date=expire_date,
                        manufacturing_date=manufacturing_date,
                    )

                if product_variant:
                    product_variant.stock = product_variant.total_stock()
                    product_variant.save()

                stock_item = f.save(commit=False)
                stock_item.stockupdate = data
                stock_item.batch = batch
                stock_item.taxable_amount = taxable_amount
                stock_item.save()

            response_data = {
                "status" : "true",
                "title" : "Successfully Created",
                "message" : "Inward stock added successfully.",
                "redirect" : "true",
                "redirect_url" : reverse('general:stock_updates')
            }

        else:
            message = generate_form_errors(form,formset=False)
            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : str(message)
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = StockUpdateForm(initial={'date': datetime.datetime.now().date()})
        stock_update_item_formset = StockUpdateItemFormset(prefix="stock_update_item_formset")

        for form_item in stock_update_item_formset:
            # form_item.fields['product'].queryset = Product.objects.filter(is_deleted=False)
            form_item.fields['product_variant'].queryset = ProductVariant.objects.none()
            form_item.fields['batch'].queryset = Batch.objects.none()

        context = {
            "title" : "Create Inward Stock",
            "form" : form,
            "stock_update_item_formset" : stock_update_item_formset,
            "url" : reverse('general:create_inward_stock'),
            "redirect" : True,

        }
        return render(request,'general/entry_batch.html',context)


def create_outward_stock(request):
    StockOutwardItemFormset = formset_factory(StockOutWardItemForm, extra=1)

    if request.method == 'POST':
        form = StockUpdateForm(request.POST)
        stock_update_item_formset = StockOutwardItemFormset(request.POST,prefix="stock_update_item_formset")

        if form.is_valid() and stock_update_item_formset.is_valid():
            error_message = ''
            stock_items = {}
            stock_ok = True

            for f in stock_update_item_formset:
                if f.cleaned_data != {}:
                    batch = f.cleaned_data['batch']
                    qty = f.cleaned_data['stock']

                    obj = {
                        'batch' : batch,
                        "quantity": qty,
                    }

                    # to check stock availability
                    if str(batch.pk) in stock_items:
                        stock_items[str(batch.pk)]['quantity'] += qty

                    else:
                        stock_items[str(batch.pk)] = obj

            for key, value in stock_items.items():
                batch = Batch.objects.get(pk=key)
                product = batch.product
                product_varient = None
                is_varient = False

                stock = batch.stock
                name = product.name

                if batch.product_variant:
                    product_varient = batch.product_variant
                    name = product_varient.title
                    is_varient = True

                quantity = value['quantity']

                if quantity > stock:
                    stock_ok = False
                    error_message += f"{name} has only {stock} in stock in batch {batch}, You entered {quantity} quantity\n"

            if stock_ok:
                auto_id = get_auto_id(StockUpdate)
                data = form.save(commit=False)
                data.creator = request.user
                data.updater = request.user
                data.auto_id = auto_id
                data.update_type = 'outward'
                data.save()

                for f in stock_update_item_formset:
                    batch = f.cleaned_data['batch']
                    # product = f.cleaned_data['product']
                    product_variant = f.cleaned_data['product_variant']
                    quantity = f.cleaned_data['stock']
                    mrp = f.cleaned_data['mrp']
                    cost = f.cleaned_data['cost']
                    retail_price = f.cleaned_data['retail_price']
                    whole_sale_price = f.cleaned_data['whole_sale_price']

                    expire_date = f.cleaned_data['expire_date']

                    if Batch.objects.filter(pk=batch.pk, product_variant=product_variant).exists():
                        Batch.objects.filter(pk=batch.pk, product_variant=product_variant).update(
                            stock = F('stock') - quantity,
                        )

                    if product_variant:
                        product_variant.stock = product_variant.total_stock()
                        product_variant.save()

                    data1 = f.save(commit=False)
                    data1.stockupdate = data
                    data1.save()

                response_data = {
                    "status" : "true",
                    "title" : "Successfully Created",
                    "message" : "Stock updated successfully.",
                    "redirect" : "true",
                    "redirect_url" : reverse('general:stock_updates')
                }

            else:
                message = 'Sorry..! Not Enough Stock '
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": error_message
                }

        else:
            message = generate_form_errors(form,formset=False)
            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : str(message)
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = StockUpdateForm(initial={'date': datetime.datetime.now().date()})
        stock_update_item_formset = StockOutwardItemFormset(prefix="stock_update_item_formset")

        for form_item in stock_update_item_formset:
            # form_item.fields['product'].queryset = Product.objects.filter(is_deleted=False)
            form_item.fields['product_variant'].queryset = ProductVariant.objects.none()
            form_item.fields['batch'].queryset = Batch.objects.none()

        context = {
            "form" : form,
            "title" : "Create Outward Stock",
            "stock_update_item_formset" : stock_update_item_formset,
            "url" : reverse('general:create_outward_stock'),
            "redirect" : True,

        }

        return render(request,'general/entry_outward_stock.html',context)


def update_stock(request,pk):
    instance = get_object_or_404(StockUpdate.objects.filter(pk=pk,is_deleted=False))

    stock_update_item = StockUpdateItem.objects.filter(stockupdate=instance)

    context = {
        "instance" : instance,
        "title" : "Stock Update",
        "stock_update_item" : stock_update_item,
    }

    return render(request,'general/update_stock.html',context)


def edit_update_stock(request,pk):
    instance = get_object_or_404(StockUpdate.objects.filter(pk=pk,is_deleted=False))
    old_stockupdate_items = StockUpdateItem.objects.filter(stockupdate_id=pk)

    if StockUpdateItem.objects.filter(stockupdate=instance).exists():
        extra = 0
    else:
        extra= 1

    if instance.update_type == 'inward':
        print('inward')
        item_form = StockInwardItemEditForm
        template_name = 'general/entry_batch.html'
    else:
        print('inward123')
        item_form = StockOutWardItemForm
        template_name = 'general/entry_outward_stock.html'

    StockUpdateItemFormset = inlineformset_factory(
        StockUpdate,
        StockUpdateItem,
        can_delete = True,
        extra = extra,
        form = item_form
    )

    if request.method == 'POST':
        form = StockUpdateForm(request.POST, instance=instance)
        stock_update_item_formset = StockUpdateItemFormset(request.POST, instance=instance, prefix="stock_update_item_formset")

        if form.is_valid() and stock_update_item_formset.is_valid():
            stock_ok = True
            stock_items = {}
            error_message = ''

            if instance.update_type == 'outward':
                for f in stock_update_item_formset:
                    if f.cleaned_data != {}:
                        batch = f.cleaned_data['batch']
                        qty = f.cleaned_data['stock']

                        obj = {
                            'batch' : batch,
                            "quantity": qty,
                        }

                        # to check stock availability
                        if str(batch.pk) in stock_items:
                            stock_items[str(batch.pk)]['quantity'] += qty

                        else:
                            stock_items[str(batch.pk)] = obj

                for key, value in stock_items.items():
                    batch = Batch.objects.get(pk=key)
                    product = batch.product
                    product_varient = None
                    is_varient = False

                    stock = batch.stock
                    name = product.name

                    if batch.product_variant:
                        product_varient = batch.product_variant
                        name = product_varient.title
                        is_varient = True

                    old_qty = 0
                    if StockUpdateItem.objects.filter(batch=batch, stockupdate=instance).exists():
                        old_qty = StockUpdateItem.objects.filter(batch=batch, stockupdate=instance).last().stock

                    stock = stock + old_qty
                    quantity = value['quantity']

                    if quantity > stock:
                        stock_ok = False
                        error_message += f"{name} has only {stock} in stock in batch {batch}, You entered {quantity} quantity\n"
            else:
                for f in stock_update_item_formset:
                    mrp = f.cleaned_data['mrp']
                    cost = f.cleaned_data['cost']
                    retail_price = f.cleaned_data['retail_price']
                    whole_sale_price = f.cleaned_data['whole_sale_price']
                    # product = f.cleaned_data['product']
                    product_variant = f.cleaned_data['product_variant']
                    product_name = ""
                    if product_variant:
                        product_name = str(product_variant)

                    if (Decimal(mrp) - Decimal(retail_price)) < 0 :
                        error_message += f'Retail price is greater than MRP of {product_name}.\n'
                        stock_ok = False
                    if (Decimal(retail_price) - Decimal(cost)) < 0:
                        error_message += f'Cost is greater than Retail price of {product_name}.\n'
                        stock_ok = False

                    if (Decimal(mrp) - Decimal(whole_sale_price)) < 0 :
                        error_message += f'Whole Sale price is greater than MRP of {product_name}.\n'
                        stock_ok = False
                    if (Decimal(whole_sale_price) - Decimal(cost)) < 0:
                        error_message += f'Cost is greater than Whole Sale price of {product_name}.\n'
                        stock_ok = False

            if stock_ok:
                data = form.save(commit=False)
                data.updater = request.user
                data.date_updated = datetime.datetime.now()
                data.save()

                for item in old_stockupdate_items:
                    batch = item.batch
                    # product = item.product
                    quantity = item.stock

                    if instance.update_type == 'inward':
                        if item.product_variant:
                            if Batch.objects.filter(batch_number=batch.batch_number, product_variant=item.product_variant).exists():
                                Batch.objects.filter(batch_number=batch.batch_number, product_variant=item.product_variant).update(
                                    stock = F('stock') - quantity,
                                )

                            item.product_variant.stock = item.product_variant.total_stock()
                            item.product_variant.save()

                    else:
                        if item.product_variant:
                            if Batch.objects.filter(batch_number=batch.batch_number, product_variant=item.product_variant, product=product).exists():
                                Batch.objects.filter(batch_number=batch.batch_number, product_variant=item.product_variant, product=product).update(
                                    stock = F('stock') + quantity,
                                )

                            item.product_variant.stock = item.product_variant.total_stock()
                            item.product_variant.save()

                old_stockupdate_items.delete()

                for f in stock_update_item_formset:
                    if instance.update_type == 'inward':
                        batch = f.cleaned_data['batch']
                        batch_number = f.cleaned_data['batch_number']
                        add_new_batch = f.cleaned_data['add_new_batch']

                        # product = f.cleaned_data['product']
                        product_variant = f.cleaned_data['product_variant']

                        mrp = f.cleaned_data['mrp']
                        cost = f.cleaned_data['cost']
                        retail_price = f.cleaned_data['retail_price']
                        whole_sale_price = f.cleaned_data['whole_sale_price']
                        quantity = f.cleaned_data['stock']
                        expire_date = f.cleaned_data['expire_date']
                        manufacturing_date = f.cleaned_data['manufacturing_date']
                        is_update_batch_data = f.cleaned_data['update_batch_data']

                        # tot = (quantity * price)
                        # cess = product.hsn.cess_rate
                        cgst = product.hsn.cgst_rate
                        sgst = product.hsn.sgst_rate

                        total_tax_rate =  cgst + sgst
                        taxable_amount = (cost / (1 + (total_tax_rate / 100)))

                        if add_new_batch:
                            batch = None
                            if not batch_number:
                                batch_number = '0DEFLT'
                        else:
                            if batch:
                                batch_number = batch.batch_number
                            else:
                                batch_number = '0DEFLT'
                        # batch_number = batch_number.upper()

                        if Batch.objects.filter(batch_number=batch_number, product_variant=product_variant, product=product).exists():
                            if is_update_batch_data:
                                Batch.objects.filter(batch_number=batch_number, product_variant=product_variant, product=product).update(
                                    stock = F('stock') + quantity,
                                    mrp = mrp,
                                    retail_price=retail_price,
                                    whole_sale_price=whole_sale_price,
                                    cost = cost,
                                    expire_date = expire_date,
                                    manufacturing_date = manufacturing_date,
                                )
                            else:
                                Batch.objects.filter(batch_number=batch_number, product_variant=product_variant).update(
                                    stock = F('stock') + quantity,
                                )

                            batch = Batch.objects.get(batch_number=batch_number, product_variant=product_variant)

                        else:
                            batch = Batch.objects.create(
                                auto_id=get_auto_id(Batch),
                                mrp = mrp,
                                stock = quantity,
                                creator=request.user,
                                updater=request.user,
                                warehouse=data.warehouse,
                                batch_number = batch_number,
                                product_variant = product_variant,
                                cost = cost,

                                retail_price=retail_price,
                                whole_sale_price=whole_sale_price,
                                expire_date=expire_date,
                                manufacturing_date=manufacturing_date,
                            )

                        if product_variant:
                            product_variant.stock = product_variant.total_stock()
                            product_variant.save()

                        stock_item = f.save(commit=False)
                        stock_item.stockupdate = data
                        stock_item.batch = batch
                        stock_item.taxable_amount = taxable_amount
                        stock_item.save()

                    else:
                        batch = f.cleaned_data['batch']
                        # product = f.cleaned_data['product']
                        product_variant = f.cleaned_data['product_variant']
                        quantity = f.cleaned_data['stock']
                        mrp = f.cleaned_data['mrp']
                        cost = f.cleaned_data['cost']
                        retail_price = f.cleaned_data['retail_price']
                        whole_sale_price = f.cleaned_data['whole_sale_price']
                        expire_date = f.cleaned_data['expire_date']
                        manufacturing_date = f.cleaned_data['manufacturing_date']

                        if Batch.objects.filter(pk=batch.pk, product_variant=product_variant).exists():
                            Batch.objects.filter(pk=batch.pk, product_variant=product_variant).update(
                                stock = F('stock') - quantity,
                            )

                        if product_variant:
                            product_variant.stock = product_variant.total_stock()
                            product_variant.save()

                        data1 = f.save(commit=False)
                        data1.stockupdate = data
                        data1.save()

                response_data = {
                    "status" : "true",
                    "title" : "Successfully Updated",
                    "message" : "Stock updated successfully.",
                    "redirect" : "true",
                    # "redirect_url" : reverse('general:update_stock',kwargs={'pk':data.pk})
                    "redirect_url" : reverse('general:stock_updates')
                }

            else:
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": error_message
                }

        else:
            message = generate_form_errors(form,formset=False)
            print(form.errors)
            print("-----")
            print(stock_update_item_formset.errors)
            response_data = {
                "status" : "false",
                "stable" : "true",
                "title" : "Form validation error",
                "message" : str(message)
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = StockUpdateForm(instance=instance, initial={'date': (instance.date.date()+datetime.timedelta(days=1))})
        stock_update_item_formset = StockUpdateItemFormset(prefix="stock_update_item_formset", instance=instance)

        for form_item in stock_update_item_formset:
            # form_item.fields['product'].queryset = Product.objects.filter(is_deleted=False)
            form_item.fields['product_variant'].queryset = ProductVariant.objects.none()
            form_item.fields['batch'].queryset = Batch.objects.none()

        context = {
            "title" : f"Edit {instance.update_type} stock",
            "form" : form,
            "stock_update_item_formset" : stock_update_item_formset,
            "url" : request.path,
            "redirect" : True,
            "is_edit" : True,
        }

        return render(request, template_name, context)


def stock_updates(request):
    instances = StockUpdate.objects.filter(is_deleted=False).order_by('-auto_id')
    title = "Update stocks"

    context = {
        "instances" : instances,
        'title' : title,
    }

    return render(request,'general/update_stocks.html',context)


def delete_stock_update(request, pk):
    instance = StockUpdate.objects.get(pk=pk)
    stock_update_items = StockUpdateItem.objects.filter(stockupdate_id=pk)

    # update stock
    for item in stock_update_items:
        batch = item.batch
        product = item.product
        quantity = item.stock

        if instance.update_type == 'inward':
            if item.product_variant:
                if Batch.objects.filter(batch_number=batch.batch_number, product_variant=item.product_variant, product=product).exists():
                    Batch.objects.filter(batch_number=batch.batch_number, product_variant=item.product_variant, product=product).update(
                        stock = F('stock') - quantity,
                    )

                item.product_variant.stock = item.product_variant.total_stock()
                item.product_variant.save()

        else:
            if item.product_variant:
                if Batch.objects.filter(batch_number=batch.batch_number, product_variant=item.product_variant, product=product).exists():
                    Batch.objects.filter(batch_number=batch.batch_number, product_variant=item.product_variant, product=product).update(
                        stock = F('stock') + quantity,
                    )

                item.product_variant.stock = item.product_variant.total_stock()
                item.product_variant.save()

    instance.is_deleted = True
    instance.save()

    response_data = {
        "status": "true",
        "title": "Successfully Removed",
        "message": f"{instance.update_type.title()} Stock Successfully removed.",
        "redirect": "true",
        "redirect_url": reverse('general:stock_updates')
    }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')




@login_required
@role_required(['superadmin', 'warehouse_manager'])
def create_invoice_design(request):
    instances = InvoiceDesign.objects.filter(is_deleted=False,is_active=True)
    if request.method == 'POST':
        form = InvoiceDesignForm(request.POST,request.FILES)
        if not instances:
            if form.is_valid():

                auto_id = get_auto_id(InvoiceDesign)
                # create invoice_design
                data = form.save(commit=False)
                data.creator = request.user
                data.updater = request.user
                data.auto_id = auto_id

                data.save()

                response_data = {
                    "status": "true",
                    "title": "Successfully Created",
                    "message": "Invoice Design Created Successfully.",
                    "redirect": "true",
                    "redirect_url": reverse('general:invoice_design', kwargs={'pk': data.pk})
                }

            else:
                message = generate_form_errors(form, formset=False)

                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": str(message)
                }

            return HttpResponse(json.dumps(response_data), content_type='application/javascript')
        else:
            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": str("Active Invoice Design Exists")
            }

            return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = InvoiceDesignForm()
        context = {
            "title": "Create Invoice Design ",
            "form": form,
            "url": reverse('general:create_invoice_design'),


        }
        return render(request, 'general/invoice_design/invoice_design_entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def invoice_designs(request):
    instances = InvoiceDesign.objects.filter(is_deleted=False)
    title = "InvoiceDesigns"
    query = request.GET.get("q")
    if query:
        instances = instances.filter(
            Q(auto_id__icontains=query) | Q(title__icontains=query))
        title = "Invoice Designs - %s" % query

    context = {
        "instances": instances,
        'title': title,

    }
    return render(request, 'general/invoice_design/invoice_designs.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def invoice_design(request, pk):
    instance = get_object_or_404(InvoiceDesign.objects.filter(pk=pk, is_deleted=False))
    context = {
        "instance": instance,
        "title": "InvoiceDesign : " + instance.title,
        "single_page": True,

    }
    return render(request, 'general/invoice_design/invoice_design.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def edit_invoice_design(request, pk):
    instance = get_object_or_404(InvoiceDesign.objects.filter(pk=pk, is_deleted=False))

    if request.method == 'POST':
        response_data = {}
        form = InvoiceDesignForm(request.POST,request.FILES, instance=instance)

        if form.is_valid():

            # update invoice_design
            data = form.save(commit=False)
            data.updater = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            response_data = {
                "status": "true",
                "title": "Successfully Updated",
                "message": "Invoice Design Successfully Updated.",
                "redirect": "true",
                "redirect_url": reverse('general:invoice_design', kwargs={'pk': data.pk})
            }
        else:
            message = generate_form_errors(form, formset=False)

            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": str(message)
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = InvoiceDesignForm(instance=instance)

        context = {
            "form": form,
            "title": "Edit Invoice Design : " + instance.name,
            "instance": instance,
            "url": reverse('general:edit_invoice_design', kwargs={'pk': instance.pk}),
            "redirect": True,

        }
        return render(request, 'general/invoice_design/invoice_design_entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_invoice_design(request, pk):
    reason = request.GET.get('reason')
    print(reason,"POOOOOOOO")
    instance = get_object_or_404(InvoiceDesign.objects.filter(pk=pk, is_deleted=False))

    InvoiceDesign.objects.filter(pk=pk).update(
        is_deleted=True, deleted_reason=reason)

    response_data = {
        "status": "true",
        "title": "Successfully Deleted",
        "message": "Invoice Design Successfully Deleted.",
        "redirect": "true",
        "redirect_url": reverse('general:invoice_designs')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_selected_invoice_designs(request):
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(
                InvoiceDesign.objects.filter(pk=pk, is_deleted=False))
            InvoiceDesign.objects.filter(pk=pk).update(
                is_deleted=True, name=instance.name + "_deleted_" + str(instance.auto_id))

        response_data = {
            "status": "true",
            "title": "Successfully Deleted",
            "message": "Selected Invoice Designs Successfully Deleted.",
            "redirect": "true",
            "redirect_url": reverse('general:invoice_designs')
        }
    else:
        response_data = {
            "status": "false",
            "title": "Nothing selected",
            "message": "Please select some items first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')

