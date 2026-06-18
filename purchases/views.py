import json
from decimal import Decimal
from datetime import datetime, timedelta
# Third party libraries
from dal import autocomplete
# Django libraries
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.forms.widgets import TextInput, Textarea, Select, HiddenInput, CheckboxInput
from django.forms.models import inlineformset_factory, formset_factory
from django.http.response import HttpResponseRedirect, HttpResponse
from django.template.loader import render_to_string
from django.db.models import Sum, Q, F, Max
# Local libraries
from main.decorators import ajax_required, role_required
from main.functions import get_auto_id, generate_form_errors, generate_form_errors, get_purchase_no, get_date_updated_request, get_purchase_order_no
from users.functions import get_warehouse
from staffs.models import Staff
from warehouses.models import Warehouse
from suppliers.models import Supplier
from suppliers.forms import SupplierCreateFromForm
from sales.functions import update_batch_stock
from products.models import Product, ProductVariant
from general.models import Batch
from reports.functions import get_ledger_data
from finance.models import AccountHead, AccountGroup, PaymentVoucher, InvoicePrefix, FinancialYear
from purchases.models import Purchase, PurchaseItem, PurchaseOrder, PurchaseOrderItem, PurchaseReturn, PurchaseReturnItem
from purchases.forms import PurchaseForm, PurchaseItemForm, PurchaseOrderForm, PurchaseOrderItemEditForm, PurchaseOrderItemForm, PurchaseReturnForm, PurchaseReturnItemForm, PurchaseVoucherForm
from purchases.filters import PurchaseFilter
from suppliers.functions import get_all_suppliers

from api.v1.general.serializers import PurchaseExportSerializer
from main.utils.export_to_excel import ExportToExcelUtils


class PurchaseReturnAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self, *args, **kwargs):
        items = PurchaseReturn.objects.filter(is_deleted=False)
        supplier = self.forwarded.get('supplier', None)
        if Staff.objects.filter(user=self.request.user).exists():
            warehouse = Staff.objects.get(user=self.request.user).warehouse
            items = items.filter(warehouse=warehouse)

        if supplier:
            items = items.filter(supplier=supplier)

        if self.q:
            items = items.filter(Q(auto_id__istartswith=self.q) |
                                 Q(supplier__name__istartswith=self.q) |
                                 Q(supplier__address__istartswith=self.q) |
                                 Q(supplier__email__istartswith=self.q) |
                                 Q(supplier__phone__istartswith=self.q)
                                 )

        return items


class PurchaseAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self, *args, **kwargs):
        items = Purchase.objects.filter(is_deleted=False)
        supplier = self.forwarded.get('supplier', None)
        if supplier:
            items = items.filter(supplier=supplier)

        if self.q:
            items = items.filter(Q(auto_id__istartswith=self.q) |
                                 Q(supplier__name__istartswith=self.q) |
                                 Q(supplier__address__istartswith=self.q) |
                                 Q(supplier__email__istartswith=self.q) |
                                 Q(supplier__phone__istartswith=self.q)
                                 )

        return items


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def get_purchase_items(request):
    pk = request.GET.get('id')
    template_name = 'purchases/includes/purchase_item.html'
    instance = get_object_or_404(Purchase, pk=pk)
    instances = PurchaseItem.objects.filter(purchase__pk=pk)

    if instances:
        context = {
            'sale_items': instances,
        }
        html_content = render_to_string(template_name, context)
        response_data = {
            "status": "true",
            'template': html_content,
            'supplier': str(instance.supplier.pk),
            'supplier_name': instance.supplier.name,
        }
    else:
        response_data = {
            "status": "false",
            "message": "Product not found"
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@ajax_required
@login_required
@role_required(['superadmin', 'warehouse_manager'])
def get_customer(request):
    pk = request.GET.get('id')
    instance = Purchase.objects.get(pk=pk, is_deleted=False)

    if instance.supplier:
        debit = 0
        credit = 0
        if instance.supplier.opening_type == "debit":
            debit = instance.supplier.opening_balance
            credit = 0
        if instance.supplier.opening_type == "credit":
            credit = instance.supplier.opening_balance
            debit = 0
        if instance.supplier.is_deleted == True:
            response_data = {
                "status": "true",
                'credit': float(0.00),
                'debit': float(0.00),
            }
        else:
            response_data = {
                "status": "true",
                'credit': float(credit),
                'debit': float(debit),
            }
    else:
        response_data = {
            "status": "false",
            "message": "Credit Error"
        }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def create_new_purchase(request):
    PurchaseItemFormset = formset_factory(PurchaseItemForm, extra=1)

    if request.method == "POST":
        # ModifiedRequest = get_date_updated_request(
        #     request.POST.copy(), ['date'])
        ModifiedRequest = get_date_updated_request(request.POST.copy(), ['date', 'cheque_date', 'draft_date', 'transfer_date'])

        form = PurchaseForm(ModifiedRequest)
        voucher_form = PurchaseVoucherForm(ModifiedRequest)
        purchase_item_formset = PurchaseItemFormset(request.POST, prefix="purchase_item_formset")

        if form.is_valid() and purchase_item_formset.is_valid() and voucher_form.is_valid():
            date = form.cleaned_data['date']
            supplier = form.cleaned_data['supplier']
            paid = form.cleaned_data['paid']
            balance = form.cleaned_data['balance']
            product_total = form.cleaned_data['product_total']
            total_amount = form.cleaned_data['subtotal']
            discount_rate = form.cleaned_data['discount']
            add_gst = form.cleaned_data['add_gst']
            warehouse = form.cleaned_data['warehouse']
            transfer_type = voucher_form.cleaned_data['transfer_type']

            balance_ok = True
            items_count = 0
            today = datetime.now().date()

            for f in purchase_item_formset:
                items_count += 1

            if items_count == 0:
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": "No purchase items enterd"
                }

                return HttpResponse(json.dumps(response_data), content_type='application/javascript')

            if voucher_form.cleaned_data['transfer_type'] != 30 and not paid:
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": "Please enter paid amount or change payment method to credit."
                }
                return HttpResponse(json.dumps(response_data), content_type='application/javascript')

            elif voucher_form.cleaned_data['transfer_type'] == 30 and paid:
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": "Please choose a payment method if a payment is in progress."
                }
                return HttpResponse(json.dumps(response_data), content_type='application/javascript')

            if transfer_type == 10:
                head = AccountHead.objects.get(code='cash_account')
                ledger_data = get_ledger_data(head, today, today, None, 'current balance', [warehouse.pk])
                current_balance = ledger_data['closing_balance']

                if paid:
                    if current_balance < paid:
                        balance_ok = False
                else:
                    balance_ok = False

            elif transfer_type == 30:
                if paid:
                    balance_ok = False

            else:
                bank = voucher_form.cleaned_data['bank']
                if not bank:
                    balance_ok = False
                else:
                    test = AccountHead.objects.filter()
                    for i in test:
                        print(i.code,bank.pk)

                    head = AccountHead.objects.get(bank_account=bank)
                    ledger_data = get_ledger_data(head, today, today, None, 'current balance', [warehouse.pk])
                    current_balance = ledger_data['closing_balance']

                    if paid:
                        if current_balance < paid:
                            balance_ok = False
                    else:
                        balance_ok = False

            if FinancialYear.objects.filter(is_deleted=False, is_active=True, start_date__date__lte=date, end_date__date__gte=date).exists():
                financial_year = FinancialYear.objects.get(is_deleted=False, is_active=True, start_date__date__lte=date, end_date__date__gte=date)

                if balance_ok:
                    if not paid:
                        paid = 0
                    if discount_rate:
                        discount = product_total*discount_rate/100
                    else:
                        discount = 0

                    tot = 0
                    total = 0
                    subtotal = 0
                    items = {}
                    batch_ok = True
                    error_message = ''
                    check_already_array = []

                    for f in purchase_item_formset:
                        if f.cleaned_data != {}:
                            # product = f.cleaned_data['product']
                            product_variant = f.cleaned_data['product_variant']

                            batch_number = f.cleaned_data['batch_number']
                            add_new_batch = f.cleaned_data['add_new_batch']
                            current_batch = f.cleaned_data['batch']

                            obj = {
                                # 'product': product,
                                'product_variant': product_variant,
                                'current_batch': current_batch,
                                'add_new_batch': add_new_batch,
                                'batch_number': batch_number,
                            }

                            if product_variant:
                                product_name = str(product_variant)
                            else:
                                pass
                                # product_name = str(product)

                            if obj in check_already_array:
                                batch_ok = False
                                error_message += f'same batch of {product_name} is used more than once.\n'

                            else:
                                check_already_array.append(obj)

                            mrp = f.cleaned_data['mrp']
                            cost = f.cleaned_data['amount']
                            retail_price = f.cleaned_data['retail_price']
                            whole_sale_price = f.cleaned_data['whole_sale_price']

                            if (Decimal(mrp) - Decimal(retail_price)) < 0:
                                error_message += f'Retail price is greater than MRP of {product_name}.\n'
                                batch_ok = False

                            if (Decimal(retail_price) - Decimal(cost)) < 0:
                                error_message += f'Cost(amount) is greater than Retail price of {product_name}.\n'
                                batch_ok = False

                            if (Decimal(mrp) - Decimal(whole_sale_price)) < 0:
                                error_message += f'Whole sale price is greater than MRP of {product_name}.\n'
                                batch_ok = False

                            if (Decimal(whole_sale_price) - Decimal(cost)) < 0:
                                error_message += f'Cost(amount) is greater than Whole sale price of {product_name}.\n'
                                batch_ok = False
                    if supplier:
                        credit_limit = supplier.credit_limit
                        debit_limit = supplier.debit_limit
                        current_balance = supplier.current_balance
                        sup_balance_type = supplier.get_balance_data()['balance_type']
                        sup_balance = supplier.get_balance_data()['balance']

                        balance = total_amount - paid
                        new_balance = current_balance + balance

                        is_exceeded_limit = False
                        msg = ""
                        if new_balance < 0:
                            msg = "Credit"
                            if abs(new_balance) > credit_limit:
                                is_exceeded_limit = True
                        if new_balance > 0:
                            msg = "Debit"
                            if abs(new_balance) > debit_limit:
                                is_exceeded_limit = True

                        if is_exceeded_limit:
                            response_data = {
                                "status": "false",
                                "stable": "true",
                                "title": "Form validation error",
                                "message": str(msg)+" limit is exceeded"
                            }

                            return HttpResponse(json.dumps(response_data), content_type='application/javascript')

                    if batch_ok:
                        purchase_prefix = 'PUR'
                        date = datetime.combine(date, datetime.now().time())
                        data = form.save(commit=False)
                        data.creator = request.user
                        data.updater = request.user
                        data.date = date

                        data.supplier = supplier
                        data.auto_id = get_auto_id(Purchase)
                        data.purchase_no = get_purchase_no(Purchase)
                        data.purchase_id = str(purchase_prefix) + str(data.purchase_no).zfill(4)

                        data.subtotal = total_amount
                        data.balance = balance
                        data.paid = paid
                        data.product_total = product_total

                        data.save()

                        total_taxable_without_amount = 0
                        total_taxable_amount = 0
                        total_tax_amount = 0
                        product_discount = 0
                        tax_amount = 0

                        for f in purchase_item_formset:
                            if f.cleaned_data != {}:
                                # product = f.cleaned_data['product']
                                product_variant = f.cleaned_data['product_variant']
                                quantity = f.cleaned_data['quantity']
                                amount = f.cleaned_data['amount']
                                mrp = f.cleaned_data['mrp']
                                # batch_price = f.cleaned_data['price']
                                batch_number = f.cleaned_data['batch_number']
                                add_new_batch = f.cleaned_data['add_new_batch']
                                current_batch = f.cleaned_data['batch']
                                tax = f.cleaned_data['tax']
                                tax_amount = f.cleaned_data['tax_amount']
                                cgst_amount = f.cleaned_data['cgst_amount']
                                sgst_amount = f.cleaned_data['sgst_amount']
                                expire_date = f.cleaned_data['expire_date']
                                manufacturing_date = f.cleaned_data['manufacturing_date']
                                product_discount_rate = f.cleaned_data['discount']
                                net_rate = f.cleaned_data['net_rate']
                                retail_price = f.cleaned_data['retail_price']
                                whole_sale_price = f.cleaned_data['whole_sale_price']

                                if add_new_batch:
                                    current_batch = None
                                    if not batch_number:
                                        batch_number = '0DEFLT'
                                else:
                                    if current_batch:
                                        batch_number = current_batch.batch_number
                                    else:
                                        batch_number = '0DEFLT'

                                is_varient = True
                                if product_variant:
                                    if ProductVariant.objects.filter(is_deleted=False, pk=product_variant.pk).exists():
                                        is_varient = True

                                if is_varient:

                                    dic = {
                                        "quantity": quantity,
                                        "amount": amount,
                                        # 'price': batch_price,
                                        "net_rate": net_rate,
                                        "product_discount_rate": product_discount_rate,

                                        "tax": tax,
                                        "tax_amount": tax_amount,
                                        "cgst_amount": cgst_amount,
                                        "sgst_amount": sgst_amount,
                                        # "gross_amount": gross_amount,

                                        "mrp": mrp,
                                        "expire_date": expire_date,
                                        "manufacturing_date": manufacturing_date,
                                        "batch_number": batch_number,
                                        "add_new_batch": add_new_batch,
                                        "current_batch": current_batch,

                                        "is_varient": True
                                    }
                                    key = product_variant.pk
                                    value = dic

                                if value['is_varient'] == True:
                                    product_variant = ProductVariant.objects.get(pk=key)
                                    hsn = product_variant.product.hsn
                                    pro_pk = product_variant.pk

                                quantity = value["quantity"]
                                # batch_price = value["price"]
                                price = value["amount"]
                                tax = value["tax"]
                                tax_amount_value = value["tax_amount"]
                                product_discount_rate = value["product_discount_rate"]
                                net_rate = value["net_rate"]
                                mrp = value["mrp"]
                                expire_date = value["expire_date"]
                                manufacturing_date = value["manufacturing_date"]

                                add_new_batch = value["add_new_batch"]
                                current_batch = value["current_batch"]
                                batch_number = value['batch_number']

                                tot = (quantity * price)
                                if product_discount_rate:
                                    product_discount = tot * product_discount_rate / 100
                                else:
                                    product_discount = 0

                                if add_gst:
                                    tax_amount_og = cgst_amount+sgst_amount
                                    cgst = cgst_amount
                                    sgst = sgst_amount
                                    igst = 0
                                else:
                                    tax_amount_og = 0
                                    cgst = 0
                                    sgst = 0
                                    igst = 0

                                # batch_price = price
                                total += (tot+tax_amount_og)-product_discount
                                total_taxable_without_amount += tot-product_discount
                                total_tax_amount += tax_amount_og

                                single_tot = tot+tax_amount_og

                                if value['is_varient'] == True:
                                    purchase_item = PurchaseItem.objects.create(
                                        purchase=data,
                                        product_variant=product_variant,
                                        hsn=hsn.hsn_number,
                                        retail_price=retail_price,
                                        whole_sale_price=whole_sale_price,

                                        batch=current_batch,
                                        batch_number=batch_number,
                                        add_new_batch=add_new_batch,

                                        amount=price,
                                        # price=batch_price,
                                        mrp=mrp,

                                        quantity=quantity,
                                        expire_date=expire_date,
                                        manufacturing_date=manufacturing_date,
                                        net_rate=net_rate,
                                        discount=product_discount_rate,
                                        total=(single_tot-product_discount),
                                        tax=tax,
                                        tax_amount=tax_amount_value,
                                        sgst_amount=sgst,
                                        cgst_amount=cgst,
                                        igst_amount=igst
                                    )
                                    if Batch.objects.filter(batch_number=batch_number, product_variant=product_variant, warehouse=warehouse).exists():
                                        Batch.objects.filter(batch_number=batch_number, product_variant=product_variant, warehouse=warehouse).update(
                                            stock=F('stock') + quantity,
                                            mrp=mrp,
                                            cost=(
                                                (single_tot-product_discount)/quantity),
                                            retail_price=retail_price,
                                            whole_sale_price=whole_sale_price,
                                            expire_date=expire_date,
                                            manufacturing_date=manufacturing_date,
                                        )

                                        batch = Batch.objects.get(batch_number=batch_number, product_variant=product_variant, warehouse=warehouse)

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
                                            cost=((single_tot-product_discount)/quantity),
                                            retail_price=retail_price,
                                            whole_sale_price=whole_sale_price,
                                            expire_date=expire_date,
                                            manufacturing_date=manufacturing_date,
                                        )

                                    product_variant.stock = product_variant.total_stock()
                                    product_variant.save()
                                else:
                                    print("is variant False")
                                    pass

                            purchase_item.batch = batch
                            purchase_item.save()

                            tot = (total_taxable_without_amount)-discount

                        data.subtotal = total_amount
                        data.paid = paid
                        balance = balance

                        data.balance = balance
                        user = request.user
                        data.save()

                        balance = total_amount - paid
                        current_balance = supplier.current_balance
                        n_balance = current_balance + balance
                        Supplier.objects.filter(pk=supplier.pk).update(current_balance=n_balance)

                        if paid > 0:
                            # Set PaymentVoucher
                            account_head = AccountHead.objects.get(code="sundry_creditor_supplier", is_deleted=False)

                            if PaymentVoucher.objects.all().exists():
                                number = PaymentVoucher.objects.aggregate(voucher_number=Max('voucher_number')).get('voucher_number')
                                voucher_no = int(number) + 1
                            else:
                                voucher_no = 1

                            if transfer_type == 10:
                                payment_voucher = PaymentVoucher.objects.create(
                                    voucher_number=voucher_no,
                                    auto_id= get_auto_id(PaymentVoucher),
                                    creator=request.user,
                                    updater=request.user,

                                    account_head=account_head,
                                    voucher_date=data.date_added,
                                    title="Purchase Create",
                                    description="Purchase Create",
                                    amount=paid,
                                    transfer_type=10,
                                    sub_ledger = supplier.pk,
                                    is_system_generated = True,

                                    financial_year=financial_year,
                                    warehouse=warehouse,
                                )

                                payment_method = 'cash'

                                # account_group, created = AccountGroup.objects.get_or_create(
                                #     name='Cash in Hand', description="Cash in Hand", is_deleted=False)
                                # account_head, created = AccountHead.objects.get_or_create(
                                #     name='Cash A/C', description="Cash A/C", account_group=account_group, is_deleted=False)
                                # account_head.current_balance = (
                                #     account_head.current_balance - Decimal(paid))
                                # account_head.save()

                            elif transfer_type in [15, 20, 25]:
                                bank = voucher_form.cleaned_data['bank']
                                cheque_number = None
                                cheque_date = None
                                status = 20
                                draft_number = None
                                draft_date = None
                                transfer_number = None
                                transfer_date = None

                                if transfer_type == 15:
                                    payment_method = 'cheque'
                                    cheque_number = voucher_form.cleaned_data['cheque_number']
                                    cheque_date = voucher_form.cleaned_data['cheque_date']
                                elif transfer_type == 20:
                                    payment_method = 'draft'
                                    draft_number = voucher_form.cleaned_data['draft_number']
                                    draft_date = voucher_form.cleaned_data['draft_date']
                                elif transfer_type == 25:
                                    payment_method = 'bank transfer'
                                    transfer_number = voucher_form.cleaned_data['transfer_number']
                                    transfer_date = voucher_form.cleaned_data['transfer_date']

                                payment_voucher = PaymentVoucher.objects.create(
                                    voucher_number = voucher_no,
                                    auto_id = get_auto_id(PaymentVoucher),
                                    creator = request.user,
                                    updater = request.user,

                                    voucher_date = data.date_added,
                                    account_head = account_head,
                                    title = "Purchase Create",
                                    description = "Purchase Create",
                                    amount = paid,
                                    sub_ledger = supplier.pk,
                                    transfer_type = transfer_type,
                                    is_system_generated = True,

                                    bank = bank,
                                    cheque_number = cheque_number,
                                    cheque_date = cheque_date,
                                    cheque_status = status,
                                    draft_number = draft_number,
                                    draft_date = draft_date,
                                    transfer_number = transfer_number,
                                    transfer_date = transfer_date,

                                    warehouse = warehouse,
                                    financial_year = financial_year
                                )

                            data.payment_voucher = payment_voucher
                            data.payment_method = payment_method
                            data.save()

                        response_data = {
                            "status": "true",
                            "title": "Successfully Created!!",
                            "message": "Purchase Successfully Created",
                            "redirect": 'true',
                            "redirect_url": reverse('purchases:purchase', kwargs={"pk": data.pk})
                        }
                        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
                    response_data = {
                        "status": "false",
                        "stable": "true",
                        "title": "Form validation error",
                        "message": error_message
                    }

                else:
                    if transfer_type == 30:
                        error_message = "Please choose a payment method if a payment is in progress."
                    elif not paid:
                        error_message = "Please enter paid amount or change payment method ot credit."
                    elif transfer_type in [15, 20, 25]:
                        error_message = "Please choose a bank account before submitting."
                    else:
                        error_message = "Cash A/C doesn't have enough balance."

                    response_data = {
                        "status": "false",
                        "stable": 'true',
                        "title": "Transaction Failed",
                        "message": error_message
                    }

                return HttpResponse(json.dumps(response_data), content_type='application/javascript')
            else:
                if FinancialYear.objects.filter(is_deleted=False, is_active=True).exists():
                    error_message = "Sale date must be within active financial year."
                elif FinancialYear.objects.filter(is_deleted=False, is_active=False).exists():
                    error_message = "Don't have an active Financial year."
                else:
                    error_message = "Please Add a Financial year."

                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Financial Year error",
                    "message": error_message
                }
        else:
            print(form.errors)
            print(purchase_item_formset.errors)
            message1 = str(generate_form_errors(voucher_form, formset=False))
            message = str(generate_form_errors(form, formset=False)) + message1
            # message += str(generate_form_errors(voucher_form, formset=False))
            message += str(generate_form_errors(purchase_item_formset, formset=True))

            if 'Amount :' in message:
                message = message.replace("Amount :", "Rate :")

            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        warehouse = get_warehouse(request)
        supplier_form = SupplierCreateFromForm()
        voucher_form = PurchaseVoucherForm(initial={'transfer_type': 10})
        purchase_item_formset = PurchaseItemFormset(prefix="purchase_item_formset")
        form = PurchaseForm(
            initial={'date': datetime.strftime(datetime.now().date(), '%d/%m/%Y'), 'warehouse': warehouse})

        for form_item in purchase_item_formset:
            form_item.fields['product_variant'].queryset = ProductVariant.objects.none()
            form_item.fields['batch'].queryset = Batch.objects.none()

        context = {
            "voucher_form": voucher_form,
            "form": form,
            "supplier_form": supplier_form,
            "purchase_item_formset": purchase_item_formset,
            "title": "Create Purchase",
            "redirect": True,
        }

        return render(request, 'purchases/entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def purchase(request, pk):
    instance = get_object_or_404(Purchase.objects.filter(pk=pk))
    purchase_item_formset = PurchaseItem.objects.filter(purchase=instance)
    voucher_instance = instance.payment_voucher

    total_amount = instance.subtotal - instance.round_off

    context = {
        "instance": instance,
        "voucher_instance": voucher_instance,
        "purchase_item_formset": purchase_item_formset,
        "total_amount": total_amount,
        "title": "Purchase",

        "single_page": True,
    }
    return render(request, 'purchases/purchase.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def purchases(request):
    user = request.user
    instances = Purchase.objects.none()
    filter_data = {}

    suppliers = get_all_suppliers()

    instances = Purchase.objects.all().order_by('-purchase_id')

    query = request.GET.get('q')
    on_date = request.GET.get('on_date')
    to_date = request.GET.get('to_date')
    from_date = request.GET.get('from_date')
    invoice_id = request.GET.get('invoice_id')
    view_option = request.GET.get('view')
    payment_method = request.GET.get('payment_method')
    supplier = request.GET.get('suppliers')

    if query:
        instances = instances.filter(
            Q(purchase_id__icontains=query) |
            Q(paid__icontains=query) |
            Q(subtotal__icontains=query) |
            Q(supplier__name__icontains=query) |
            Q(creator__username__icontains=query)
        )
        filter_data['query'] = query

    if view_option == 'active':
        filter_data['view'] = 'active'
        instances = instances.filter(is_deleted=False)
    elif view_option == 'cancelled':
        filter_data['view'] = 'cancelled'
        instances = instances.filter(is_deleted=True)
    else:
        filter_data['view'] = 'all'

    if from_date and to_date:
        # f_date = datetime.strptime(from_date, '%d/%m/%Y').date()
        # t_date = datetime.strptime(to_date, '%d/%m/%Y').date()
        instances = instances.filter(date__date__range=[from_date, to_date])
        title = 'Total Number of Purchases (from %s to %s)' % (str(from_date), str(to_date))

        filter_data['from_date'] = from_date
        filter_data['to_date'] = to_date

    if on_date:
        # o_date = datetime.strptime(on_date, '%d/%m/%Y').date()
        instances = instances.filter(date__date=on_date)
        title = 'Total Number of Purchases (On %s)' % (str(on_date))
        filter_data['on_date'] = on_date

    if payment_method:
        instances = instances.filter(payment_method=payment_method)
        filter_data['payment_method'] = payment_method

    if supplier:
        instances = instances.filter(supplier__pk=supplier)

    context = {
        "instances": instances,
        "title": "Purchases",
        'filter_data': filter_data,
        "suppliers": suppliers,
    }
    return render(request, 'purchases/purchases.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def edit_purchase(request, pk):
    instance = get_object_or_404(Purchase.objects.filter(pk=pk, is_deleted=False))
    purchaseitem = PurchaseItem.objects.filter(purchase=instance)

    previous_date = instance.date
    previous_amount = instance.subtotal
    previous_balance = instance.balance

    if PurchaseItem.objects.filter(purchase=instance).exists():
        extra = 0
    else:
        extra = 1

    PurchaseItemFormset = inlineformset_factory(
        Purchase,
        PurchaseItem,
        can_delete=True,
        extra=extra,
        form=PurchaseItemForm,
    )

    old_paid = instance.paid
    old_total_amount = instance.subtotal
    old_supplier = Supplier.objects.get(pk=instance.supplier.pk)

    if instance.payment_voucher:
        voucher_instance = instance.payment_voucher
        old_amount = voucher_instance.amount
    else:
        old_amount = 0
        voucher_instance = None

    if request.method == 'POST':
        ModifiedRequest = get_date_updated_request(
            request.POST.copy(), ['date', 'cheque_date', 'draft_date', 'transfer_date'])


        form = PurchaseForm(ModifiedRequest, instance=instance)
        voucher_form = PurchaseVoucherForm(ModifiedRequest, instance=voucher_instance)

        purchase_item_formset = PurchaseItemFormset(request.POST, prefix='purchase_item_formset', instance=instance)

        if form.is_valid() and purchase_item_formset.is_valid() and voucher_form.is_valid():
            date = form.cleaned_data['date']
            paid = form.cleaned_data['paid']
            balance = form.cleaned_data['balance']
            subtotal_amount = form.cleaned_data['subtotal']
            # other_amount = form.cleaned_data['other_charge']
            add_gst = form.cleaned_data['add_gst']
            supplier = form.cleaned_data['supplier']
            purchase_date = form.cleaned_data['date']
            discount_rate = form.cleaned_data['discount']
            product_total = form.cleaned_data['product_total']
            warehouse = form.cleaned_data['warehouse']

            items_count = 0
            for f in purchase_item_formset:
                items_count += 1

            if items_count == 0:
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": "No purchase items enterd"
                }

                return HttpResponse(json.dumps(response_data), content_type='application/javascript')

            if voucher_form.cleaned_data['transfer_type'] != 30 and not paid:
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": "Please enter paid amount or change payment method to credit."
                }
                return HttpResponse(json.dumps(response_data), content_type='application/javascript')

            elif voucher_form.cleaned_data['transfer_type'] == 30 and paid:
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": "Please choose a payment method if a payment is in progress."
                }
                return HttpResponse(json.dumps(response_data), content_type='application/javascript')

            if voucher_form.cleaned_data['transfer_type'] in [15, 20, 25]:
                bank = voucher_form.cleaned_data['bank']
                if not bank:
                    response_data = {
                        "status": "false",
                        "stable": "true",
                        "title": "Form validation error",
                        "message": "Please choose a bank account before submitting."
                    }
                    return HttpResponse(json.dumps(response_data), content_type='application/javascript')

            if FinancialYear.objects.filter(is_deleted=False, is_active=True, start_date__date__lte=date, end_date__date__gte=date).exists():
                financial_year = FinancialYear.objects.get(is_deleted=False, is_active=True, start_date__date__lte=date, end_date__date__gte=date)
                batch_ok = True
                stock_ok = True
                error_message = ''
                check_already_array = []

                for f in purchase_item_formset:
                    if f.cleaned_data != {}:
                        product_variant = f.cleaned_data['product_variant']
                        quantity = f.cleaned_data['quantity']

                        batch_number = f.cleaned_data['batch_number']
                        add_new_batch = f.cleaned_data['add_new_batch']
                        current_batch = f.cleaned_data['batch']

                        obj = {
                            'product_variant': product_variant,
                            'current_batch': current_batch,
                            'add_new_batch': add_new_batch,
                            'batch_number': batch_number,
                        }

                        if product_variant:
                            product_name = str(product_variant)

                        if obj in check_already_array:
                            batch_ok = False
                            error_message += f'same batch of {product_name} is used more than once.\n'

                        else:
                            check_already_array.append(obj)

                        mrp = f.cleaned_data['mrp']
                        cost = f.cleaned_data['amount']
                        retail_price = f.cleaned_data['retail_price']
                        whole_sale_price = f.cleaned_data['whole_sale_price']

                        if (Decimal(mrp) - Decimal(retail_price)) < 0:
                            error_message += f'Retail price is greater than MRP of {product_name}.\n'
                            batch_ok = False
                        if (Decimal(retail_price) - Decimal(cost)) < 0:
                            error_message += f'Cost(amount) is greater than Retail price of {product_name}.\n'
                            batch_ok = False

                        if (Decimal(mrp) - Decimal(whole_sale_price)) < 0:
                            error_message += f'Whole sale price is greater than MRP of {product_name}.\n'
                            batch_ok = False
                        if (Decimal(whole_sale_price) - Decimal(cost)) < 0:
                            error_message += f'Cost(amount) is greater than Whole sale price of {product_name}.\n'
                            batch_ok = False

                        if batch_ok and current_batch:
                            if PurchaseItem.objects.filter(batch_number=batch_number, add_new_batch=add_new_batch, batch=current_batch, purchase=instance).exists():
                                old_qty = PurchaseItem.objects.filter(
                                    batch_number=batch_number, add_new_batch=add_new_batch, batch=current_batch, purchase=instance).last().quantity
                                current_batch.stock -= old_qty
                                current_batch.stock += quantity

                                if current_batch.stock < 0:
                                    stock_ok = False
                                    error_message += f'Not enough stock in batch {current_batch}.'

                if batch_ok and stock_ok:
                    old_balance = old_total_amount - old_paid
                    current_balance = old_supplier.current_balance
                    o_balance = current_balance - old_balance
                    Supplier.objects.filter(pk=old_supplier.pk).update(current_balance=o_balance)

                    befor_discount_amount = 0

                    if discount_rate:
                        discount = product_total*discount_rate/100
                        # after_discount_amount = befor_discount_amount
                        total_amount = product_total-discount
                    else:
                        total_amount = befor_discount_amount
                        discount = 0

                    date = form.cleaned_data['date']
                    date = datetime.combine(date, datetime.now().time())

                    data = form.save(commit=False)
                    data.updater = request.user
                    data.date_updated = datetime.now()
                    data.is_updated = True
                    data.date = date
                    data.discount = discount_rate
                    data.save()

                    items = {}
                    new_total_quantity = 0

                    # delete previous items
                    old_purchase_items = PurchaseItem.objects.filter(purchase=instance)

                    for old_item in old_purchase_items:
                        quantity = old_item.quantity
                        try:
                            Batch.objects.filter(pk=old_item.batch.pk).update(
                                stock=F('stock') - quantity,
                            )
                        except:
                            pass

                    for p in old_purchase_items:
                        print('delete---: ', p)
                    old_purchase_items.delete()

                    # save items
                    total = 0
                    total_taxable_amount = 0
                    total_tax_amount = 0
                    all_tax_total = 0
                    all_cess_amount = 0
                    tax_amount = 0
                    total_taxable_without_amount = 0
                    product_discount = 0
                    total_amount = 0

                    for f in purchase_item_formset:
                        quantity = f.cleaned_data['quantity']
                        product_variant = f.cleaned_data['product_variant']
                        amount = f.cleaned_data['amount']
                        tax = f.cleaned_data['tax']
                        mrp = f.cleaned_data['mrp']
                        retail_price = f.cleaned_data['retail_price']
                        whole_sale_price = f.cleaned_data['whole_sale_price']
                        tax_amount = f.cleaned_data['tax_amount']
                        cgst_amount = f.cleaned_data['cgst_amount']
                        sgst_amount = f.cleaned_data['sgst_amount']
                        product_discount_rate = f.cleaned_data['discount']
                        net_rate = f.cleaned_data['net_rate']
                        batch_number = f.cleaned_data['batch_number']
                        add_new_batch = f.cleaned_data['add_new_batch']
                        current_batch = f.cleaned_data['batch']
                        expire_date = f.cleaned_data['expire_date']
                        manufacturing_date = f.cleaned_data['manufacturing_date']

                        # tot = quantity * amount
                        # total +=  tot
                        # print(subtotal)

                        if add_new_batch:
                            current_batch = None
                            if not batch_number:
                                batch_number = '0DEFLT'
                        else:
                            if current_batch:
                                batch_number = current_batch.batch_number
                            else:
                                batch_number = '0DEFLT'

                        # batch_number = batch_number.upper()
                        new_total_quantity += quantity

                        is_varient = False
                        if product_variant:
                            if ProductVariant.objects.filter(is_deleted=False, pk=product_variant.pk).exists():
                                is_varient = True

                        if is_varient:
                            if str(product_variant.pk) in items:
                                q = items[str(product_variant.pk)]["quantity"]
                                items[str(product_variant.pk)]["quantity"] = q + quantity
                            else:
                                dic = {
                                    "quantity": quantity,
                                    "amount": amount,
                                    "retail_price": retail_price,
                                    "whole_sale_price": whole_sale_price,
                                    "net_rate": net_rate,
                                    "product_discount_rate": product_discount_rate,

                                    "mrp": mrp,
                                    "expire_date": expire_date,
                                    "manufacturing_date": manufacturing_date,
                                    "batch_number": batch_number,
                                    "add_new_batch": add_new_batch,
                                    "current_batch": current_batch,

                                    "tax": tax,
                                    "tax_amount": tax_amount,
                                    "cgst_amount": cgst_amount,
                                    "sgst_amount": sgst_amount,
                                    # "gross_amount": gross_amount,

                                    "is_varient": True
                                }
                                key = product_variant.pk
                                value = dic
                                # items[str(product_variant.pk)] = dic

                        else:
                            print("Product Variant is not available")

                        # for key, value in items.items():
                        if value['is_varient'] == True:
                            product_variant = ProductVariant.objects.get(pk=key)
                            hsn = product_variant.product.hsn
                            pro_pk = product_variant.pk

                        quantity = value["quantity"]
                        price = value["amount"]
                        tax = value["tax"]
                        tax_amount_value = value["tax_amount"]
                        # gross_amount = value["gross_amount"]
                        product_discount_rate = value["product_discount_rate"]
                        net_rate = value["net_rate"]
                        tot = (quantity * price)

                        mrp = value["mrp"]
                        retail_price = value['retail_price']
                        whole_sale_price = value['whole_sale_price']
                        expire_date = value["expire_date"]
                        manufacturing_date = value["manufacturing_date"]
                        add_new_batch = value["add_new_batch"]
                        current_batch = value["current_batch"]
                        batch_number = value['batch_number']

                        if product_discount_rate:
                            product_discount = tot * product_discount_rate / 100
                        else:
                            product_discount = 0

                        if add_gst:
                            tax_amount_og = cgst_amount+sgst_amount
                            cgst = cgst_amount
                            sgst = sgst_amount
                            igst = 0
                        else:
                            tax_amount_og = 0
                            cgst = 0
                            sgst = 0
                            igst = 0

                        total += (tot+tax_amount_og)-product_discount
                        total_taxable_without_amount += tot-product_discount
                        total_tax_amount += tax_amount_og
                        single_tot = tot+tax_amount_og

                        if value['is_varient'] == True:
                            purchase_item_instance = PurchaseItem.objects.create(
                                product_variant=product_variant,
                                hsn=hsn.hsn_number,

                                batch=current_batch,
                                batch_number=batch_number,
                                add_new_batch=add_new_batch,
                                expire_date=expire_date,
                                manufacturing_date=manufacturing_date,

                                amount=price,
                                retail_price=retail_price,
                                whole_sale_price=whole_sale_price,
                                mrp=mrp,

                                quantity=quantity,
                                discount=product_discount_rate,
                                net_rate=net_rate,
                                # gross_amount=gross_amount,
                                total=(single_tot-product_discount),
                                purchase=data,
                                tax=tax,
                                tax_amount=tax_amount_value,
                                sgst_amount=sgst,
                                cgst_amount=cgst,
                                igst_amount=igst
                            )

                            if Batch.objects.filter(batch_number=batch_number, product_variant=product_variant, warehouse=warehouse).exists():
                                Batch.objects.filter(batch_number=batch_number, product_variant=product_variant, warehouse=warehouse).update(
                                    stock=F('stock') + quantity,
                                    expire_date=expire_date,
                                    manufacturing_date=manufacturing_date,
                                    mrp=mrp,
                                    retail_price=retail_price,
                                    whole_sale_price=whole_sale_price,
                                    cost=((single_tot-product_discount)/quantity),
                                )

                                batch = Batch.objects.get(
                                    batch_number=batch_number, product_variant=product_variant, warehouse=warehouse)

                            else:
                                batch = Batch.objects.create(
                                    mrp=mrp,
                                    stock=quantity,
                                    retail_price=retail_price,
                                    whole_sale_price=whole_sale_price,
                                    expire_date=expire_date,
                                    manufacturing_date=manufacturing_date,
                                    batch_number=batch_number,
                                    product_variant=product_variant,
                                    product=product_variant.product,
                                    cost=((single_tot-product_discount)/quantity),
                                )

                            product_variant.stock = product_variant.total_stock()
                            product_variant.save()

                        else:
                            print("Variant not Exists....")

                        purchase_item_instance.batch = batch
                        purchase_item_instance.save()

                        tot = (total_taxable_without_amount)-discount
                        # test_product = Product.objects.filter(pk=product.pk).update(cost=price)

                        # update_stock_register(product.pk,quantity,"increase","purchase",data.pk,date)

                    total_amount = form.cleaned_data['subtotal']
                    balance = balance

                    data.subtotal = total_amount
                    data.paid = paid
                    data.balance = balance
                    data.save()

                    balance = total_amount - paid
                    # current_balance = supplier.current_balance
                    # n_balance = current_balance + balance

                    # Supplier.objects.filter(pk=supplier.pk).update(current_balance=n_balance)

                    transfer_type = voucher_form.cleaned_data['transfer_type']
                    voucher_date = data.date
                    payment_method = 'credit'

                    if voucher_instance:
                        if transfer_type == 10:
                            payment_method = 'cash'
                            PaymentVoucher.objects.filter(pk=voucher_instance.pk).update(
                                voucher_date=voucher_date,
                                description="purchase creation Updated",
                                amount=paid,
                                transfer_type=transfer_type,
                                date_updated=datetime.now(),
                                updater=request.user,

                                bank=None,
                                draft_number=None,
                                draft_date=None,
                                cheque_number=None,
                                cheque_date=None,
                                cheque_status=None,
                                transfer_number=None,
                                transfer_date=None,
                            )

                        elif transfer_type in [15, 20, 25]:
                            bank_account = voucher_form.cleaned_data['bank']

                            cheque_number = None
                            cheque_date = None
                            draft_number = None
                            draft_date = None
                            transfer_number = None
                            transfer_date = None

                            if transfer_type == 15:
                                payment_method = 'cheque'
                                cheque_number = voucher_form.cleaned_data['cheque_number']
                                cheque_date = voucher_form.cleaned_data['cheque_date']
                            elif transfer_type == 20:
                                payment_method = 'draft'
                                draft_number = voucher_form.cleaned_data['draft_number']
                                draft_date = voucher_form.cleaned_data['draft_date']
                            elif transfer_type == 25:
                                payment_method = 'bank transfer'
                                transfer_number = voucher_form.cleaned_data['transfer_number']
                                transfer_date = voucher_form.cleaned_data['transfer_date']

                            PaymentVoucher.objects.filter(pk=voucher_instance.pk).update(
                                voucher_date=voucher_date,
                                description="purchase creation Updated",
                                amount=paid,
                                transfer_type=transfer_type,
                                updater=request.user,
                                date_updated=datetime.now(),

                                bank=bank_account,
                                draft_number=draft_number,
                                draft_date=draft_date,
                                cheque_number=cheque_number,
                                cheque_date=cheque_date,
                                cheque_status=20,
                                transfer_number=transfer_number,
                                transfer_date=transfer_date,
                            )

                        elif transfer_type == 30:
                            voucher_instance.is_deleted = True
                            voucher_instance.description = 'Purchase payment changed to credit'
                            voucher_instance.save()

                    else:
                        payment_voucher = None
                        payment_method = "credit"

                        if transfer_type != 30 and paid:
                            # Set PaymentVoucher
                            account_head = AccountHead.objects.get(code="sundry_creditor_supplier", is_deleted=False)

                            if PaymentVoucher.objects.all().exists():
                                number = PaymentVoucher.objects.aggregate(voucher_number=Max('voucher_number')).get('voucher_number')
                                voucher_no = int(number) + 1
                            else:
                                voucher_no = 1

                            if transfer_type == 10:
                                payment_method = 'cash'
                                payment_voucher = PaymentVoucher.objects.create(
                                    auto_id= get_auto_id(PaymentVoucher),

                                    account_head=account_head,
                                    voucher_number=voucher_no,
                                    creator=request.user,
                                    updater=request.user,
                                    voucher_date=data.date_added,

                                    title="Purchase Create",
                                    description="Purchase Create",
                                    amount=paid,
                                    transfer_type=10,
                                    sub_ledger=data.pk,
                                    is_system_generated=True,
                                    warehouse=warehouse,
                                    financial_year=financial_year
                                )

                            elif transfer_type in [15, 20, 25]:
                                bank = voucher_form.cleaned_data['bank']
                                cheque_number = None
                                cheque_date = None
                                status = 20
                                draft_number = None
                                draft_date = None
                                transfer_number = None
                                transfer_date = None

                                if transfer_type == 15:
                                    payment_method = 'cheque'
                                    cheque_number = voucher_form.cleaned_data['cheque_number']
                                    cheque_date = voucher_form.cleaned_data['cheque_date']
                                elif transfer_type == 20:
                                    payment_method = 'draft'
                                    draft_number = voucher_form.cleaned_data['draft_number']
                                    draft_date = voucher_form.cleaned_data['draft_date']
                                elif transfer_type == 25:
                                    payment_method = 'bank transfer'
                                    transfer_number = voucher_form.cleaned_data['transfer_number']
                                    transfer_date = voucher_form.cleaned_data['transfer_date']

                                payment_voucher = PaymentVoucher.objects.create(
                                    auto_id= get_auto_id(PaymentVoucher),

                                    account_head=account_head,
                                    voucher_number=voucher_no,
                                    creator=request.user,
                                    updater=request.user,
                                    voucher_date=data.date_added,
                                    title="Purchase Create",
                                    description="Purchase Create",
                                    amount=paid,
                                    sub_ledger=data.pk,
                                    transfer_type=transfer_type,
                                    is_system_generated=True,

                                    bank=bank,
                                    cheque_number=cheque_number,
                                    cheque_date=cheque_date,
                                    cheque_status=status,
                                    draft_number=draft_number,
                                    draft_date=draft_date,
                                    transfer_number=transfer_number,
                                    transfer_date=transfer_date,
                                    warehouse=warehouse,
                                    financial_year=financial_year
                                )

                        data.payment_voucher = payment_voucher
                        data.payment_method = payment_method
                        data.save()

                response_data = {
                    "status": "true",
                    "title": "Successfully Updated",
                    "message": "Purchase Successfully Updated.",
                    "redirect": "true",
                    "redirect_url": reverse('purchases:purchases')
                }

            else:
                if FinancialYear.objects.filter(is_deleted=False, is_active=True).exists():
                    error_message = "Purchase date must be within active financial year."
                elif FinancialYear.objects.filter(is_deleted=False, is_active=False).exists():
                    error_message = "Don't have an active Financial year."
                else:
                    error_message = "Please Add a Financial year."

                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Financial Year error",
                    "message": error_message
                }
        else:
            message = generate_form_errors(form, formset=False)
            # message += str(generate_form_errors(voucher_form, formset=False))
            message += str(generate_form_errors(purchase_item_formset, formset=True))
            print(form.errors)
            print(purchase_item_formset.errors)
            # print(form.errors)

            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": str(message)
            }
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = PurchaseForm(instance=instance)
        purchase_item_formset = PurchaseItemFormset(prefix='purchase_item_formset', instance=instance)

        for x in purchase_item_formset:
            x.fields['batch'].queryset = Batch.objects.none()

        if voucher_instance:
            voucher_initial = {}

            if voucher_instance.transfer_date:
                voucher_initial['transfer_date'] = datetime.strftime(voucher_instance.transfer_date, '%d/%m/%Y')
            if voucher_instance.draft_date:
                voucher_initial['draft_date'] = datetime.strftime(voucher_instance.draft_date, '%d/%m/%Y')
            if voucher_instance.cheque_date:
                voucher_initial['cheque_date'] = datetime.strftime(voucher_instance.cheque_date, '%d/%m/%Y')

        else:
            voucher_initial = {
                'transfer_type': 30
            }

        voucher_form = PurchaseVoucherForm(instance=voucher_instance, initial=voucher_initial)

        context = {
            "voucher_form": voucher_form,
            "form": form,
            "is_edit": True,
            "instance": instance,
            "title": "Edit Purchase",
            "purchase_item_formset": purchase_item_formset,
            "url": reverse('purchases:edit_purchase', kwargs={'pk': pk}),
        }

        return render(request, 'purchases/entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_purchase(request, pk):
    reason = request.GET.get('reason')
    instance = get_object_or_404(Purchase.objects.filter(pk=pk))
    purchase_items = PurchaseItem.objects.filter(purchase=instance)
    # update stock
    for item in purchase_items:
        quantity = item.quantity
        batch = item.batch
        product = item.product

        if item.product_variant:
            if Batch.objects.filter(batch_number=batch.batch_number, product_variant=item.product_variant, product=product).exists():
                Batch.objects.filter(batch_number=batch.batch_number, product_variant=item.product_variant, product=product).update(
                    stock=F('stock') - quantity,
                )

            item.product_variant.stock = item.product_variant.total_stock()
            item.product_variant.save()

    instance.is_deleted = True
    instance.deleted_reason = reason
    instance.date_updated = datetime.now()
    instance.save()

    response_data = {
        "status": "true",
        "title": "Successfully Cancelled",
        "message": "Purchase Successfully cancelled.",
        "redirect": "true",
        "redirect_url": reverse('purchases:purchases')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def print_purchase(request, pk):
    instance = get_object_or_404(Purchase.objects.filter(pk=pk))
    state = instance.supplier.state
    sale_category = "intra_state"
    if not state == "Kerala":
        sale_category = "inter_state"

    purchase_items = PurchaseItem.objects.filter(purchase=instance)

    total_subtotal = 0
    grant_total = 0
    total_cgst = 0
    total_sgst = 0
    total_igst = 0
    for purchase_item in purchase_items:
        tax_amount = purchase_item.tax_amount
        subtotal = purchase_item.subtotal()
        gst_added_total = purchase_item.total
        grant_total += gst_added_total
        total_subtotal += subtotal

        if sale_category == "intra_state":
            sgst = tax_amount/2
            cgst = tax_amount/2
            sgst_rate = purchase_item.tax/2
            cgst_rate = purchase_item.tax/2
            igst = 0
            igst_rate = 0

            total_cgst += cgst
            total_sgst += sgst
        else:
            igst = tax_amount
            igst_rate = purchase_item.tax
            sgst = 0
            cgst = 0
            sgst_rate = 0
            cgst_rate = 0

            total_igst += igst

    grant_total_value = grant_total
    round = instance.round_off
    print(total_subtotal, ";;;;;;;;")
    total_amount = instance.subtotal - round

    context = {
        "title": "Quotation ",
        "instance": instance,
        "purchase_items": purchase_items,
        "purchase_category": sale_category,
        "grant_total_value": grant_total_value,
        "total_subtotal": total_subtotal,
        "total_cgst": total_cgst,
        "total_sgst": total_sgst,
        "total_igst": total_igst,
        "total_amount": total_amount,
    }
    return render(request, 'purchases/print/print_purchase_page.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def create_purchase_return(request):
    if request.method == "POST":
        response_data = {}
        form = PurchaseReturnForm(request.POST)
        if form.is_valid():
            message = ""
            is_ok = True
            products = request.POST.getlist('product_pk')
            qtys = request.POST.getlist('returned_qty')
            purchase = form.cleaned_data['purchase']
            date = form.cleaned_data['date']
            items = zip(products, qtys)
            returned_items = []
            for item in items:
                product_pk = item[0]
                try:
                    product_instance = Product.objects.get(pk=product_pk)
                    print(item)
                except:
                    product_instance = None
                    message += "Invalid product selection"
                    is_ok = False
                unit_pk = item[0]

                qty = item[1]

                if PurchaseItem.objects.filter(purchase=purchase, product=product_instance).exists():
                    purchase_item = PurchaseItem.objects.get(
                        purchase=purchase, product=product_instance)
                    print(purchase_item)
                    qty2 = Decimal(qty) + purchase_item.return_qty
                    purchase_qty = purchase_item.quantity - Decimal(qty2)

                    if purchase_item.quantity >= Decimal(qty2):
                        print("working")
                        pr_ins = {
                            "product": product_instance,
                            "qty": qty,
                            "price": purchase_item.amount,
                            "purchase_item_quantity": purchase_item.quantity,
                            "purchase_return_qty": qty2
                        }

                        returned_items.append(pr_ins)

                    else:
                        print("else")
                        message += "Qty is greater than purchase quantity."
                        is_ok = False
                else:
                    message += "Product with this unit is not in this sale. Please don't edit hidden values."
                    is_ok = False

            error_messages = ""
            title = ""

            if is_ok:
                amount_returned = form.cleaned_data['amount_returned']
                # amount_returned = 0
                # Save Sale Return
                supplier = purchase.supplier
                data = form.save(commit=False)
                data.creator = request.user
                data.updater = request.user
                data.time = datetime.now()
                data.auto_id = get_auto_id(PurchaseReturn)
                data.amount_returned = amount_returned
                data.purchase = purchase
                data.supplier = supplier
                data.total = 0
                data.save()

                returnable_amount = 0
                total_tax = 0
                total_taxable_amount = 0
                # Save Sale Return Item
                for f in returned_items:
                    product = f['product']
                    qty = f['qty']
                    purchase_return_qty = f['purchase_return_qty']
                    # exact_qty = Decimal(get_exact_qty(qty))
                    exact_qty = qty
                    # if unit.is_base == True :
                    #     cost = product.cost
                    # else :
                    #     unit_instanse = get_object_or_404(ProductAlternativeUnitPrice.objects.filter(product=product,unit=unit))
                    #     cost = unit_instanse.cost
                    price = f['price']
                    cost = product.cost
                    purchase_item_quantity = f['purchase_item_quantity']
                    tax_amount1 = (Decimal(price) * Decimal(product.gst)/100)
                    total_tax += tax_amount1*Decimal(qty)
                    total_taxable_amount += price*Decimal(qty)
                    tax_added_price = Decimal(
                        price) + (Decimal(price) * Decimal(product.gst)/100)

                    print(tax_added_price)
                    PurchaseReturnItem(
                        purchase_return=data,
                        product=product,
                        quantity=qty,
                        total=tax_added_price,
                        amount=cost,
                    ).save()

                    # purchase_item = PurchaseItem.objects.filter(purchase=purchase, product=product).last()
                    # quantity = qty
                    # batch = p.batch
                    # product = p.product

                    # if p.product_variant:
                    #     if Batch.objects.filter(batch_number=batch.batch_number, product_variant=p.product_variant, product=product).exists():
                    #         Batch.objects.filter(batch_number=batch.batch_number, product_variant=p.product_variant, product=product).update(
                    #             stock = F('stock') - quantity,
                    #         )

                    #     p.product_variant.stock = p.product_variant.total_stock()
                    #     p.product_variant.save()

                    qty = Decimal(qty)
                    PurchaseItem.objects.filter(purchase=purchase, product=product).update(return_qty=purchase_return_qty)

                    sale_item = PurchaseItem.objects.get(purchase=purchase, product=product)
                    returnable_amount += (tax_added_price*Decimal(qty))
                    returned_purchase_items = PurchaseItem.objects.filter(purchase=purchase)

                data.total = returnable_amount
                data.save()

                response_data = {
                    'status': 'true',
                    'title': "Successfully Created",
                    'redirect': 'true',
                    'redirect_url': reverse('purchases:purchase_return', kwargs={'pk': data.pk}),
                    'message': "Purchase Return Successfully Created.",
                }
            else:
                response_data = {
                    'status': 'false',
                    'stable': "true",
                    'title': "Error in input values",
                    'message': message,
                }
        else:
            response_data = {
                'status': 'false',
                'stable': 'true',
                'title': "Form validation error",
            }
            message = ''
            print(form.errors)
            print('form')
            message += generate_form_errors(form, formset=False)
            response_data['message'] = str(message)

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = PurchaseReturnForm()

        context = {
            "form": form,
            "title": "Create Purchase Return",
            "redirect": True,

            "is_create_page": True
        }
        return render(request, 'purchases/purchase_return_entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def create_purchase_return_new(request):
    if request.method == "POST":
        ModifiedRequest = get_date_updated_request(
            request.POST.copy(), ['date'])
        form = PurchaseReturnForm(ModifiedRequest)
        response_data = {}
        amount_returned = 0

        if form.is_valid():
            message = ""
            is_ok = True
            purchase_item_pk = request.POST.getlist('purchase_item_pk')
            qtys = request.POST.getlist('returned_qty')
            status = request.POST.getlist('status')
            purchase = form.cleaned_data['purchase']
            print(qtys, status, purchase_item_pk)
            items = zip(purchase_item_pk, qtys, status)
            returned_items = []

            for item in items:
                product_pk = item[0]

                # try:
                purchase_item_instance = PurchaseItem.objects.get(
                    pk=product_pk)

                qty = Decimal(item[1])
                status = item[2]

                if purchase_item_instance.quantity >= qty and purchase_item_instance.return_qty < purchase_item_instance.quantity:
                    if purchase_item_instance.product_variant:
                        product_variant = purchase_item_instance.product_variant
                        pr_ins = {
                            "product": product_variant.product.pk,
                            "product_variant": product_variant.pk,
                            "qty": qty,
                            "price": purchase_item_instance.amount,
                            "purchase_item_quantity": purchase_item_instance.quantity,
                            "status": status,
                            "purchase_item_return_quantity": qty,
                            "is_varient": True,
                            "batch": purchase_item_instance.batch,
                            "purchase_item_instance": purchase_item_instance,
                        }
                    # else:
                    #     product = purchase_item_instance.product
                    #     pr_ins = {
                    #         "product": product.pk,
                    #         "qty": qty,
                    #         "price": purchase_item_instance.amount,
                    #         "purchase_item_quantity": purchase_item_instance.quantity,
                    #         "status": status,
                    #         "purchase_item_return_quantity": qty,
                    #         "is_varient": False,
                    #         "batch": purchase_item_instance.batch,
                    #         "purchase_item_instance": purchase_item_instance,
                    #     }

                    returned_items.append(pr_ins)

                else:
                    message += "Quantity is greater than bought quantity."
                    is_ok = False

                # except:
                #     purchase_item_instance = None
                #     message += "Invalid purchase selection"
                #     is_ok = False

                # Save Purchase Return Item
            if is_ok:
                supplier = purchase.supplier
                data = form.save(commit=False)
                data.creator = request.user
                data.updater = request.user
                data.auto_id = get_auto_id(PurchaseReturn)
                data.purchase = purchase
                data.supplier = supplier
                data.amount_returned = amount_returned
                data.save()

                for f in returned_items:
                    qty = f['qty']
                    status = f['status']
                    price = f['price']
                    purchase_item_quantity = f['purchase_item_quantity']
                    purchase_item_return_quantity = f['purchase_item_return_quantity']

                    is_varient = f['is_varient']

                    if is_varient:
                        PurchaseReturnItem.objects.create(
                            product_id=f["product"],
                            batch=f["batch"],
                            product_variant_id=f["product_variant"],
                            purchase_return=data,
                            quantity=qty,
                            amount=price,
                            status=status,
                            purchase_item=f['purchase_item_instance'],
                        )

                    # else:
                    #     PurchaseReturnItem.objects.create(
                    #         product_id=f["product"],
                    #         purchase_return=data,
                    #         batch=f["batch"],
                    #         quantity=qty,
                    #         amount=price,
                    #         status=status,
                    #         purchase_item=f['purchase_item_instance'],
                    #     )

                    if status == 'returnable':
                        update_batch_stock(
                            f['batch'].pk, purchase_item_return_quantity, "decrease")

                    f['purchase_item_instance'].return_qty += qty
                    f['purchase_item_instance'].save()
                    amount_returned += price * purchase_item_return_quantity

                data.amount_returned = amount_returned
                data.save()

                response_data = {
                    'status': 'true',
                    'title': "Successfully Created",
                    'redirect': 'true',
                    'redirect_url': reverse('purchases:purchase_return', kwargs={'pk': data.pk}),
                    'message': "Purchase Return Successfully Created.",
                }
            else:
                response_data = {
                    'status': 'false',
                    'stable': "true",
                    'title': "Error in input values",
                    'message': message,
                }
        else:
            response_data = {
                'status': 'false',
                'stable': 'true',
                'title': "Form validation error",
            }
            message = ''
            print(form.errors)
            print('form')
            message += generate_form_errors(form, formset=False)
            response_data['message'] = str(message)

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = PurchaseReturnForm()

        context = {
            "form": form,
            "title": "Create Purchase Return",
            "redirect": True,

            "is_create_page": True
        }

        return render(request, 'purchases/purchase_return_entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def edit_purchase_return(request, pk):
    instance = get_object_or_404(
        PurchaseReturn.objects.filter(pk=pk, is_deleted=False))

    if PurchaseReturnItem.objects.filter(purchase_return=instance).exists():
        extra = 0
    else:
        extra = 1

    PurchaseReturnItemFormset = inlineformset_factory(
        PurchaseReturn,
        PurchaseReturnItem,
        can_delete=True,
        extra=extra,
        exclude=['total'],
        widgets={
            # 'material': autocomplete.ModelSelect2(url='material_return:material_autocomplete',attrs={'data-placeholder': 'Material','data-minimum-input-length': 1},),
            'product': Select(attrs={'class': 'required form-control selectpicker', 'placeholder': 'Product'}),
            'quantity': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Quantity'}),
            'amount': TextInput(attrs={'class': 'required form-control', 'placeholder': 'Amount'}),
        }
    )
    if request.method == "POST":
        ModifiedRequest = get_date_updated_request(
            request.POST.copy(), ['date'])

        form = PurchaseReturnForm(ModifiedRequest, instance=instance)
        purchase_return_item_formset = PurchaseReturnItemFormset(
            request.POST, prefix="purchase_return_item_formset", instance=instance)

        if form.is_valid() and purchase_return_item_formset.is_valid():
            data = form.save(commit=False)
            data.updater = request.user
            data.date_updated = datetime.datetime.now()
            data.save()

            purchase_returns = purchase_return_item_formset.save(commit=False)
            for purchase_return in purchase_returns:
                purchase_return.purchase_return = data
                purchase_return.save()

            subtotal = 0
            for item in purchase_return_item_formset:
                product = item.cleaned_data['product']
                quantity = item.cleaned_data['quantity']
                amount = item.cleaned_data['amount']
                sub = quantity * amount
                subtotal += sub

            data.total = subtotal
            data.is_updated = True
            data.save()

            for obj in purchase_return_item_formset.deleted_objects:
                obj.delete()

            response_data = {
                "status": "true",
                "title": "Successfully Updated!!",
                "message": "Purchase Return  Successfully Updated",
                "redirect": 'true',
                "redirect_url": reverse('purchases:purchase_return', kwargs={"pk": data.pk})
            }
        else:
            message = generate_form_errors(form, formset=False)
            message += generate_form_errors(
                purchase_return_item_formset, formset=True)

            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": str(message)
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        form = PurchaseReturnForm(instance=instance)
        purchase_return_item_formset = PurchaseReturnItemFormset(
            prefix="purchase_return_item_formset", instance=instance)
        context = {
            "form": form,
            "purchase_return_item_formset": purchase_return_item_formset,
            "title": "Edit Purchase Return",
            "redirect": True,
        }
        return render(request, 'purchases/purchase_return_entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def edit_purchase_return_new(request, pk):
    instance = get_object_or_404(
        PurchaseReturn.objects.filter(pk=pk, is_deleted=False))

    if request.method == "POST":
        response_data = {}
        form = PurchaseReturnForm(request.POST, instance=instance)
        if form.is_valid():
            message = ""
            is_ok = True
            purchase_item_pk = request.POST.getlist('purchase_item_pk')
            qtys = request.POST.getlist('returned_qty')
            status = request.POST.getlist('status')
            purchase = form.cleaned_data['purchase']
            print(qtys, status, purchase_item_pk)
            items = zip(purchase_item_pk, qtys, status)
            returned_items = []

            for item in items:
                product_pk = item[0]

                # try:
                purchase_item_instance = PurchaseItem.objects.get(
                    pk=product_pk)

                qty = Decimal(item[1])
                status = item[2]
                if purchase_item_instance.quantity >= qty:

                    if purchase_item_instance.product_variant:
                        product_variant = purchase_item_instance.product_variant

                        pr_ins = {
                            "product": purchase_item_instance.product.pk,
                            "product_variant": product_variant.pk,
                            "qty": qty,
                            "price": purchase_item_instance.amount,
                            "purchase_item_quantity": purchase_item_instance.quantity,
                            "status": status,
                            "purchase_item_return_quantity": qty,
                            "is_varient": True
                        }
                    else:
                        product = purchase_item_instance.product

                        pr_ins = {
                            "product": product.pk,
                            "qty": qty,
                            "price": purchase_item_instance.amount,
                            "purchase_item_quantity": purchase_item_instance.quantity,
                            "status": status,
                            "purchase_item_return_quantity": qty,
                            "is_varient": False
                        }

                    returned_items.append(pr_ins)

                else:
                    message += "Quantity is greater than sold quantity."
                    is_ok = False

                # except:
                #     purchase_item_instance = None
                #     message += "Invalid purchase selection"
                #     is_ok = False
                # Save Purchase Return Item

            if is_ok:
                supplier = purchase.supplier
                data = form.save(commit=False)
                data.creator = request.user
                data.updater = request.user
                data.auto_id = get_auto_id(PurchaseReturn)
                data.purchase = purchase
                data.supplier = supplier
                data.amount_returned = 0
                data.save()

                purchase_ob = PurchaseReturnItem.objects.filter(
                    purchase_return=instance)
                for i in purchase_ob:
                    if i.product_variant:
                        i.delete()
                    else:
                        i.delete()

                for f in returned_items:
                    qty = f['qty']
                    status = f['status']
                    price = f['price']
                    purchase_item_quantity = f['purchase_item_quantity']
                    purchase_item_return_quantity = f['purchase_item_return_quantity']

                    is_varient = f['is_varient']

                    if is_varient:
                        PurchaseReturnItem(
                            product_id=f["product"],
                            product_variant_id=f["product_variant"],
                            purchase_return=data,
                            quantity=qty,
                            amount=price,
                            status=status
                        ).save()

                        if status == 'returnable':
                            pass
                    else:
                        PurchaseReturnItem(
                            product_id=f["product"],
                            purchase_return=data,
                            quantity=qty,
                            amount=price,
                            status=status
                        ).save()

                        if status == 'returnable':
                            pass

                response_data = {
                    'status': 'true',
                    'title': "Successfully Created",
                    'redirect': 'true',
                    'message': "Purchase Return Successfully Created.",
                    # 'redirect_url': reverse('purchases:purchase_return', kwargs={'pk': data.pk}),
                    "redirect_url": reverse('purchases:purchase_returns')
                }

            else:
                response_data = {
                    'status': 'false',
                    'stable': "true",
                    'title': "Error in input values",
                    'message': message,
                }
        else:
            response_data = {
                'status': 'false',
                'stable': 'true',
                'title': "Form validation error",
            }
            message = ''
            print(form.errors)
            print('form')
            message += generate_form_errors(form, formset=False)
            response_data['message'] = str(message)

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = PurchaseReturnForm(instance=instance)

        context = {
            "form": form,
            "title": "Create Purchase Return",
            "redirect": True,

            "is_create_page": True
        }
        return render(request, 'purchases/purchase_return_entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def purchase_return(request, pk):
    instance = get_object_or_404(PurchaseReturn.objects.filter(pk=pk))
    purchase_return_item = PurchaseReturnItem.objects.filter(
        purchase_return=instance)
    print(purchase_return_item)
    context = {
        "title": "Purchase Return : ",
        "instance": instance,
        "purchase_return_item": purchase_return_item,

    }
    return render(request, 'purchases/purchase_return.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def purchase_returns(request):
    instances = PurchaseReturn.objects.all()
    query = request.GET.get('q')
    if query:
        instances = instances.filter(
            Q(date__icontains=query) | Q(supplier__icontains=query))
    context = {
        "title": "Purchase Return",
        "instances": instances,
    }
    return render(request, 'purchases/purchase_returns.html', context)


@login_required
@ajax_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_purchase_return(request, pk):
    reason = request.GET.get('reason')
    instance = PurchaseReturn.objects.get(pk=pk)
    instance.deleted_reason = reason
    instance.is_deleted = True
    instance.save()
    return_items = PurchaseReturnItem.objects.filter(purchase_return=instance)

    for p in return_items:
        quantity = p.quantity
        try:
            if p.batch:
                # purchase_item = PurchaseItem.objects.get(purchase=instance.purchase, product=p.product, product_variant=p.product_variant)
                update_batch_stock(p.batch.pk, quantity, "increase")
        except:
            pass

        if p.purchase_item:
            PurchaseItem.objects.filter(pk=p.purchase_item.pk).update(
                return_qty=F('return_qty')-quantity)

    response_data = {
        "status": "true",
        "title": "Successfully Deleted!!",
        "message": "Purchase Return Successfully Cancelled",
        "redirect": 'true',
        "redirect_url": reverse('purchases:purchase_returns')
    }
    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@ajax_required
@role_required(['superadmin'])
def delete_selected_purchase_return(request):
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(
                PurchaseReturn.objects.filter(pk=pk, is_deleted=False))
            instance.is_deleted = True
            instance.save()
            purchase_return_items = PurchaseReturnItem.objects.filter(
                purchase_return=instance)

            for p in purchase_return_items:
                quantity = p.quantity

        response_data = {
            "status": "true",
            "title": "Successfully Deleted",
            "message": "Selected Sale(s) Successfully Deleted.",
            "redirect": "true",
            "redirect_url": reverse('purchases:purchase_returns')
        }
    else:
        response_data = {
            "status": "false",
            "title": "Nothing selected",
            "message": "Please select some items first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin'])
def print_purchase_return(request, pk):
    instance = get_object_or_404(PurchaseReturn.objects.filter(pk=pk))
    state = instance.supplier.state
    purchase_category = "intra_state"
    if not state == "Kerala":
        purchase_category = "inter_state"
    purchase_return_items = PurchaseReturnItem.objects.filter(
        purchase_return=instance)

    total_subtotal = 0
    grant_total = 0
    total_cgst = 0
    total_sgst = 0
    total_igst = 0
    for item in purchase_return_items:
        # tax_amount = item.tax_amount
        subtotal = item.total
        total_subtotal += subtotal

    grant_total_value = grant_total

    context = {
        "instance": instance,
        "title": "Purchase Return ",
        "total_subtotal": total_subtotal,
        "purchase_category": purchase_category,
        "purchase_items": purchase_return_items,
    }
    return render(request, 'purchases/print/print_purchase_return.html', context)


@login_required
@ajax_required
@role_required(['superadmin', 'staff_user'])
def get_purchase_returns(request):
    pk = request.GET.get('id')
    if pk:
        supplier = get_object_or_404(Supplier, pk=pk)
        instances = PurchaseReturn.objects.filter(
            supplier_id=pk, is_deleted=False)

        if instances:
            data = []
            for item in instances:
                obj = {
                    'return': str(item),
                    'pk': str(item.pk)
                }
                data.append(obj)

            response_data = {
                "status": "true",
                "data": data
            }

        else:
            response_data = {
                "status": "false",
                "message": "Purchase returns Not found"
            }

    else:
        response_data = {
            "status": "false",
            "message": "vendor data unavailable"
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')




@login_required
@ajax_required
@role_required(['superadmin', 'staff_user'])
def get_purchase_return_amount(request):
    pk = request.GET.get('id')

    if pk:
        if PurchaseReturn.objects.filter(pk=pk, is_deleted=False):
            instance = PurchaseReturn.objects.get(pk=pk, is_deleted=False)

            response_data = {
                "status": "true",
                "amount": str(instance.amount_returned)
            }

        else:
            response_data = {
                "status": "false",
                "message": "Purchase return Not found"
            }

    else:
        response_data = {
            "status": "false",
            "message": "Key unavailable"
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')



@login_required
@role_required(['superadmin', 'warehouse_manager'])
def get_purchase_return_supplier(request):
    pk = request.GET.get('id')
    template_name = 'purchases/includes/purchase_item.html'
    instance = get_object_or_404(PurchaseReturn, pk=pk)

    response_data = {
        "status": "true",
        'supplier': str(instance.supplier.pk),
        'supplier_name': instance.supplier.name,
    }
    # else:
    #     response_data = {
    #         "status": "false",
    #         "message": "Product not found"
    #     }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def get_prifix_purchase_id(request):
    pk = request.GET.get('id')
    # for generating order id
    prefix = InvoicePrefix.objects.get(pk=pk,is_deleted=False)
    if Purchase.objects.filter(purchase_prifix=prefix,is_deleted=False).exists():
        purchase_no = Purchase.objects.filter(purchase_prifix=prefix,is_deleted=False).aggregate(Max('purchase_no'))['purchase_no__max']
    else:
        purchase_no = 1

    purchase_id = f"{prefix.purchase}{str(purchase_no).zfill(6)}"


    response_data = {
        "status": "true",
        'purchase_id': str(purchase_id),
    }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def create_purchase_order(request):
    PurchaseOrderItemFormset = formset_factory(PurchaseOrderItemForm, extra=1)

    if request.method == "POST":
        # ModifiedRequest = get_date_updated_request(
        #     request.POST.copy(), ['date'])
        ModifiedRequest = get_date_updated_request(request.POST.copy(), ['date'])

        form = PurchaseOrderForm(ModifiedRequest)
        purchase_order_item_formset = PurchaseOrderItemFormset(request.POST, prefix="purchase_order_item_formset")

        if form.is_valid() and purchase_order_item_formset.is_valid():
            date = form.cleaned_data['date']
            supplier = form.cleaned_data['supplier']
            # paid = form.cleaned_data['paid']
            # balance = form.cleaned_data['balance']
            product_total = form.cleaned_data['product_total']
            total_amount = form.cleaned_data['subtotal']
            discount_rate = form.cleaned_data['discount']
            warehouse = form.cleaned_data['warehouse']
            add_gst = form.cleaned_data['add_gst']

            balance_ok = True
            items_count = 0
            today = datetime.now().date()

            for f in purchase_order_item_formset:
                items_count += 1

            if items_count == 0:
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": "No purchase items enterd"
                }

                return HttpResponse(json.dumps(response_data), content_type='application/javascript')


            if FinancialYear.objects.filter(is_deleted=False, is_active=True, start_date__date__lte=date, end_date__date__gte=date).exists():
                financial_year = FinancialYear.objects.get(is_deleted=False, is_active=True, start_date__date__lte=date, end_date__date__gte=date)

                if balance_ok:
                    # if not paid:
                    paid = 0
                    if discount_rate:
                        discount = product_total*discount_rate/100
                    else:
                        discount = 0

                    tot = 0
                    total = 0
                    subtotal = 0
                    items = {}
                    batch_ok = True
                    stock_ok = True
                    error_message = ''
                    check_already_array = []

                    for f in purchase_order_item_formset:
                        if f.cleaned_data != {}:
                            # product = f.cleaned_data['product']
                            product_variant = f.cleaned_data['product_variant']
                            quantity = f.cleaned_data['quantity']

                            batch_number = f.cleaned_data['batch_number']
                            add_new_batch = f.cleaned_data['add_new_batch']
                            current_batch = f.cleaned_data['batch']

                            obj = {
                                # 'product': product,
                                'product_variant': product_variant,
                                'current_batch': current_batch,
                                'add_new_batch': add_new_batch,
                                'batch_number': batch_number,
                            }

                            product_name = str(product_variant)

                            if obj in check_already_array:
                                batch_ok = False
                                error_message += f'same batch of {product_name} is used more than once.\n'

                            else:
                                check_already_array.append(obj)


                            mrp = f.cleaned_data['mrp']
                            cost = f.cleaned_data['amount']
                            retail_price = f.cleaned_data['retail_price']
                            whole_sale_price = f.cleaned_data['whole_sale_price']

                            if (Decimal(mrp) - Decimal(retail_price)) < 0:
                                error_message += f'Retail price is greater than MRP of {product_name}.\n'
                                batch_ok = False

                            if (Decimal(retail_price) - Decimal(cost)) < 0:
                                error_message += f'Cost(amount) is greater than Retail price of {product_name}.\n'
                                batch_ok = False

                            if (Decimal(mrp) - Decimal(whole_sale_price)) < 0:
                                error_message += f'Whole sale price is greater than MRP of {product_name}.\n'
                                batch_ok = False

                            if (Decimal(whole_sale_price) - Decimal(cost)) < 0:
                                error_message += f'Cost(amount) is greater than Whole sale price of {product_name}.\n'
                                batch_ok = False

                            # if batch_ok and current_batch:
                            #     if PurchaseOrderItem.objects.filter(batch_number=batch_number, add_new_batch=add_new_batch, batch=current_batch, purchase_order=instance).exists():
                            #         old_qty = PurchaseOrderItem.objects.filter(
                            #             batch_number=batch_number, add_new_batch=add_new_batch, batch=current_batch, purchase_order=instance).last().quantity
                            #         current_batch.stock -= old_qty
                            #         current_batch.stock += quantity

                            #         if current_batch.stock < 0:
                            #             stock_ok = False
                            #             error_message += f'Not enough stock in batch {current_batch}.'


                    if batch_ok and stock_ok:
                        purchase_prefix = 'PURO'
                        date = datetime.combine(date, datetime.now().time())
                        data = form.save(commit=False)
                        data.creator = request.user
                        data.updater = request.user
                        data.date = date

                        data.supplier = supplier
                        data.auto_id = get_auto_id(PurchaseOrder)
                        data.order_no = get_purchase_order_no(PurchaseOrder)
                        data.order_id = str(purchase_prefix) + str(data.order_no).zfill(4)

                        data.subtotal = total_amount
                        # data.balance = balance
                        # data.paid = paid
                        data.product_total = product_total

                        data.save()

                        total_taxable_without_amount = 0
                        total_taxable_amount = 0
                        total_tax_amount = 0
                        product_discount = 0
                        tax_amount = 0

                        for f in purchase_order_item_formset:
                            if f.cleaned_data != {}:
                                # product = f.cleaned_data['product']
                                product_variant = f.cleaned_data['product_variant']
                                quantity = f.cleaned_data['quantity']
                                amount = f.cleaned_data['amount']
                                mrp = f.cleaned_data['mrp']
                                # batch_price = f.cleaned_data['price']
                                batch_number = f.cleaned_data['batch_number']
                                add_new_batch = f.cleaned_data['add_new_batch']
                                current_batch = f.cleaned_data['batch']
                                tax = f.cleaned_data['tax']
                                tax_amount = f.cleaned_data['tax_amount']
                                cgst_amount = f.cleaned_data['cgst_amount']
                                sgst_amount = f.cleaned_data['sgst_amount']
                                expire_date = f.cleaned_data['expire_date']
                                product_discount_rate = f.cleaned_data['discount']
                                net_rate = f.cleaned_data['net_rate']
                                manufacturing_date = f.cleaned_data['manufacturing_date']
                                retail_price = f.cleaned_data['retail_price']
                                whole_sale_price = f.cleaned_data['whole_sale_price']

                                if add_new_batch:
                                    current_batch = None
                                    if not batch_number:
                                        batch_number = '0DEFLT'
                                else:
                                    if current_batch:
                                        batch_number = current_batch.batch_number
                                    else:
                                        batch_number = '0DEFLT'

                                is_varient = True
                                if product_variant:
                                    if ProductVariant.objects.filter(is_deleted=False, pk=product_variant.pk).exists():
                                        is_varient = True

                                if is_varient:

                                    dic = {
                                        "quantity": quantity,
                                        "amount": amount,
                                        # 'price': batch_price,
                                        "net_rate": net_rate,
                                        "product_discount_rate": product_discount_rate,

                                        "tax": tax,
                                        "tax_amount": tax_amount,
                                        "cgst_amount": cgst_amount,
                                        "sgst_amount": sgst_amount,
                                        # "gross_amount": gross_amount,

                                        "mrp": mrp,
                                        "expire_date": expire_date,
                                        "manufacturing_date": manufacturing_date,
                                        "batch_number": batch_number,
                                        "add_new_batch": add_new_batch,
                                        "current_batch": current_batch,

                                        "is_varient": True
                                    }
                                    key = product_variant.pk
                                    value = dic

                                if value['is_varient'] == True:
                                    product_variant = ProductVariant.objects.get(pk=key)
                                    hsn = product_variant.product.hsn
                                    pro_pk = product_variant.pk

                                quantity = value["quantity"]
                                # batch_price = value["price"]
                                price = value["amount"]
                                tax = value["tax"]
                                tax_amount_value = value["tax_amount"]
                                product_discount_rate = value["product_discount_rate"]
                                net_rate = value["net_rate"]
                                mrp = value["mrp"]
                                expire_date = value["expire_date"]
                                manufacturing_date = value["manufacturing_date"]

                                add_new_batch = value["add_new_batch"]
                                current_batch = value["current_batch"]
                                batch_number = value['batch_number']

                                tot = (quantity * price)
                                if product_discount_rate:
                                    product_discount = tot * product_discount_rate / 100
                                else:
                                    product_discount = 0

                                if True:
                                    tax_amount_og = cgst_amount+sgst_amount
                                    cgst = cgst_amount
                                    sgst = sgst_amount
                                    igst = 0
                                else:
                                    tax_amount_og = 0
                                    cgst = 0
                                    sgst = 0
                                    igst = 0

                                # batch_price = price
                                total += (tot+tax_amount_og)-product_discount
                                total_taxable_without_amount += tot-product_discount
                                total_tax_amount += tax_amount_og

                                single_tot = tot+tax_amount_og

                                purchase_item = PurchaseOrderItem.objects.create(
                                    purchase_order=data,
                                    product_variant=product_variant,
                                    hsn=hsn.hsn_number,
                                    retail_price=retail_price,
                                    whole_sale_price=whole_sale_price,

                                    batch=current_batch,
                                    batch_number=batch_number,
                                    add_new_batch=add_new_batch,

                                    amount=price,
                                    # price=batch_price,
                                    mrp=mrp,

                                    quantity=quantity,
                                    expire_date=expire_date,
                                    manufacturing_date=manufacturing_date,
                                    net_rate=net_rate,
                                    discount=product_discount_rate,
                                    total=(single_tot-product_discount),
                                    tax=tax,
                                    tax_amount=tax_amount_value,
                                    sgst_amount=sgst,
                                    cgst_amount=cgst,
                                    igst_amount=igst
                                )

                                # product_variant.stock = product_variant.total_stock()
                                product_variant.save()

                            purchase_item.batch = current_batch
                            purchase_item.save()

                            tot = (total_taxable_without_amount)-discount

                        data.subtotal = total_amount
                        # data.paid = paid
                        # balance = balance

                        # data.balance = balance
                        user = request.user
                        data.save()
                        response_data = {
                            "status": "true",
                            "title": "Successfully Created!!",
                            "message": "Purchase Order Successfully Created",
                            "redirect": 'true',
                            "redirect_url": reverse('purchases:purchase_order', kwargs={"pk": data.pk})
                        }
                        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
                    response_data = {
                        "status": "false",
                        "stable": "true",
                        "title": "Form validation error",
                        "message": error_message
                    }

            else:
                if FinancialYear.objects.filter(is_deleted=False, is_active=True).exists():
                    error_message = "Sale date must be within active financial year."
                elif FinancialYear.objects.filter(is_deleted=False, is_active=False).exists():
                    error_message = "Don't have an active Financial year."
                else:
                    error_message = "Please Add a Financial year."

                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Financial Year error",
                    "message": error_message
                }
        else:
            print(form.errors)
            print(purchase_order_item_formset.errors)
            message = str(generate_form_errors(form, formset=False)) + message1
            # message += str(generate_form_errors(voucher_form, formset=False))
            message += str(generate_form_errors(purchase_order_item_formset, formset=True))

            if 'Amount :' in message:
                message = message.replace("Amount :", "Rate :")

            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        warehouse = get_warehouse(request)
        supplier_form = SupplierCreateFromForm()
        purchase_order_item_formset = PurchaseOrderItemFormset(prefix="purchase_order_item_formset")
        form = PurchaseOrderForm(
            initial={'date': datetime.strftime(datetime.now().date(), '%d/%m/%Y'), 'warehouse': warehouse})

        for form_item in purchase_order_item_formset:
            form_item.fields['product_variant'].queryset = ProductVariant.objects.none()
            form_item.fields['batch'].queryset = Batch.objects.none()

        context = {
            "form": form,
            "supplier_form": supplier_form,
            "purchase_order_item_formset": purchase_order_item_formset,
            "title": "Create Purchase Order",
            "redirect": True,
        }

        return render(request, 'purchases/purchase-order/entry.html', context)


@login_required
@role_required(['superadmin', 'staff_user'])
def purchase_order(request, pk):
    instance = get_object_or_404(PurchaseOrder.objects.filter(pk=pk))
    purchase_order_items = PurchaseOrderItem.objects.filter(
        purchase_order=instance)

    total_amount = instance.subtotal - instance.round_off

    context = {
        "instance": instance,
        "purchase_order_items": purchase_order_items,
        "total_amount": total_amount,
        "title": "Purchase Order",
        "single_page": True,
    }

    return render(request, 'purchases/purchase-order/purchase_order.html', context)


@login_required
@role_required(['superadmin', 'staff_user'])
def purchase_orders(request):
    filter_data = {}

    instances = PurchaseOrder.objects.filter(
        is_deleted=False).order_by('-auto_id')

    query = request.GET.get('q')
    on_date = request.GET.get('on_date')
    to_date = request.GET.get('to_date')
    from_date = request.GET.get('from_date')
    invoice_id = request.GET.get('invoice_id')
    view_option = request.GET.get('view')

    if query:
        instances = instances.filter(
            Q(order_id__icontains=query) |
            Q(subtotal=query) |
            Q(vendor__name__icontains=query) |
            Q(creator__username__icontains=query)
        )
        filter_data['query'] = query

    if view_option == 'active':
        filter_data['view'] = 'active'
        instances = instances.filter(is_deleted=False)
    elif view_option == 'cancelled':
        filter_data['view'] = 'cancelled'
        instances = instances.filter(is_deleted=True)
    else:
        filter_data['view'] = 'all'

    if from_date and to_date:
        f_date = datetime.strptime(from_date, '%d/%m/%Y').date()
        t_date = datetime.strptime(to_date, '%d/%m/%Y').date()
        instances = instances.filter(date__date__range=[f_date, t_date])
        title = 'Total Number of Purchases (from %s to %s)' % (
            str(f_date), str(t_date))

        filter_data['from_date'] = from_date
        filter_data['to_date'] = to_date

    if on_date:
        o_date = datetime.strptime(on_date, '%d/%m/%Y').date()
        instances = instances.filter(date__date=o_date)
        title = 'Total Number of Purchase Orders (On %s)' % (str(o_date))
        filter_data['on_date'] = on_date

    context = {
        "instances": instances,
        "title": "Purchase Orders",
        'filter_data': filter_data
    }
    return render(request, 'purchases/purchase-order/purchase_orders.html', context)


@login_required
@role_required(['superadmin'])
def delete_order_purchase(request, pk):
    instance = get_object_or_404(PurchaseOrder.objects.filter(pk=pk))

    if not instance.is_partial and not instance.is_purchased:
        instance.is_deleted = True
        instance.date_updated = datetime.now()
        instance.save()

        response_data = {
            "status": "true",
            "title": "Successfully Cancelled",
            "message": "Purchase Order Successfully cancelled.",
            "redirect": "true",
            "redirect_url": reverse('purchases:purchase_orders')
        }
    else:
        response_data = {
            "status": "false",
            "stable": "true",
            "title": "Cannot Delete",
            "message": "Purchase has been issued for this Purchase Order.",
            "redirect": "true",
            "redirect_url": reverse('purchases:purchase_orders')
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin'])
def edit_purchase_order(request, pk):
    instance = get_object_or_404(
        PurchaseOrder.objects.filter(pk=pk, is_deleted=False))
    purchase_order_items = PurchaseOrderItem.objects.filter(
        purchase_order=instance)
    total_qty = 0

    for i in purchase_order_items:
        total_qty += i.quantity

    if PurchaseOrderItem.objects.filter(purchase_order=instance).exists():
        extra = 0
    else:
        extra = 1

    PurchaseOrderItemFormset = inlineformset_factory(
        PurchaseOrder,
        PurchaseOrderItem,
        can_delete=True,
        extra=extra,
        form=PurchaseOrderItemForm,
    )

    if request.method == 'POST':
        ModifiedRequest = get_date_updated_request(
            request.POST.copy(), ['date'])

        form = PurchaseOrderForm(ModifiedRequest, instance=instance)
        purchase_order_item_formset = PurchaseOrderItemFormset(
            request.POST, prefix='purchase_order_item_formset', instance=instance)

        if form.is_valid() and purchase_order_item_formset.is_valid():
            date = form.cleaned_data['date']
            supplier = form.cleaned_data['supplier']
            discount_rate = form.cleaned_data['discount']
            subtotal_amount = form.cleaned_data['subtotal']
            product_total = form.cleaned_data['product_total']

            items_count = 0
            for f in purchase_order_item_formset:
                items_count += 1

            if items_count == 0:
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": "No purchase items enterd"
                }

                return HttpResponse(json.dumps(response_data), content_type='application/javascript')

            if FinancialYear.objects.filter(is_deleted=False, is_active=True, start_date__date__lte=date, end_date__date__gte=date).exists():
                batch_ok = True
                stock_ok = True
                error_message = ''
                check_already_array = []

                for f in purchase_order_item_formset:
                    if f.cleaned_data != {}:
                        product_variant = f.cleaned_data['product_variant']
                        quantity = f.cleaned_data['quantity']

                        batch_number = f.cleaned_data['batch_number']
                        add_new_batch = f.cleaned_data['add_new_batch']
                        current_batch = f.cleaned_data['batch']

                        obj = {
                            'product_variant': product_variant,
                            'current_batch': current_batch,
                            'add_new_batch': add_new_batch,
                            'batch_number': batch_number,
                        }

                        product_name = str(product_variant)

                        if obj in check_already_array:
                            batch_ok = False
                            error_message += f'same batch of {product_name} is used more than once.\n'

                        else:
                            check_already_array.append(obj)

                        mrp = f.cleaned_data['mrp']
                        cost = f.cleaned_data['amount']
                        retail_price = f.cleaned_data['retail_price']
                        whole_sale_price = f.cleaned_data['whole_sale_price']

                        if (Decimal(mrp) - Decimal(retail_price)) < 0:
                            error_message += f'Retail price is greater than MRP of {product_name}.\n'
                            batch_ok = False

                        if (Decimal(retail_price) - Decimal(cost)) < 0:
                            error_message += f'Cost(amount) is greater than Retail price of {product_name}.\n'
                            batch_ok = False

                        if (Decimal(mrp) - Decimal(whole_sale_price)) < 0:
                            error_message += f'Whole sale price is greater than MRP of {product_name}.\n'
                            batch_ok = False

                        if (Decimal(whole_sale_price) - Decimal(cost)) < 0:
                            error_message += f'Cost(amount) is greater than Whole sale price of {product_name}.\n'
                            batch_ok = False

                        if batch_ok and current_batch:
                            if PurchaseOrderItem.objects.filter(batch_number=batch_number, add_new_batch=add_new_batch, batch=current_batch, purchase_order=instance).exists():
                                old_qty = PurchaseOrderItem.objects.filter(
                                    batch_number=batch_number, add_new_batch=add_new_batch, batch=current_batch, purchase_order=instance).last().quantity
                                current_batch.stock -= old_qty
                                current_batch.stock += quantity

                                if current_batch.stock < 0:
                                    stock_ok = False
                                    error_message += f'Not enough stock in batch {current_batch}.'

                if batch_ok and stock_ok:
                    date = datetime.combine(date, datetime.now().time())
                    befor_discount_amount = 0

                    if discount_rate:
                        discount = product_total*discount_rate/100
                        total_amount = product_total-discount
                    else:
                        total_amount = befor_discount_amount
                        discount = 0

                    data = form.save(commit=False)
                    data.updater = request.user
                    data.date_updated = datetime.now()
                    data.discount = discount_rate
                    data.is_updated = True
                    data.save()

                    items = {}
                    new_total_quantity = 0

                    # delete previous items
                    old_purchase_order_items = PurchaseOrderItem.objects.filter(
                        purchase_order=instance)

                    for p in old_purchase_order_items:
                        print('delete---: ', p)
                    old_purchase_order_items.delete()

                    # save items
                    total = 0
                    total_taxable_amount = 0
                    total_tax_amount = 0
                    all_tax_total = 0
                    all_cess_amount = 0
                    tax_amount = 0
                    total_taxable_without_amount = 0
                    product_discount = 0
                    total_amount = 0

                    for f in purchase_order_item_formset:
                        quantity = f.cleaned_data['quantity']
                        product_variant = f.cleaned_data['product_variant']
                        amount = f.cleaned_data['amount']
                        tax = f.cleaned_data['tax']
                        mrp = f.cleaned_data['mrp']
                        tax_amount = f.cleaned_data['tax_amount']
                        cgst_amount = f.cleaned_data['cgst_amount']
                        sgst_amount = f.cleaned_data['sgst_amount']
                        product_discount_rate = f.cleaned_data['discount']
                        net_rate = f.cleaned_data['net_rate']
                        batch_number = f.cleaned_data['batch_number']
                        add_new_batch = f.cleaned_data['add_new_batch']
                        current_batch = f.cleaned_data['batch']
                        expire_date = f.cleaned_data['expire_date']
                        manufacturing_date = f.cleaned_data['manufacturing_date']
                        retail_price = f.cleaned_data['retail_price']
                        whole_sale_price = f.cleaned_data['whole_sale_price']

                        if add_new_batch:
                            current_batch = None
                            if not batch_number:
                                batch_number = '0DEFLT'
                        else:
                            if current_batch:
                                batch_number = current_batch.batch_number
                            else:
                                batch_number = '0DEFLT'

                        new_total_quantity += quantity

                        is_varient = False
                        if product_variant:
                            if ProductVariant.objects.filter(is_deleted=False, pk=product_variant.pk).exists():
                                is_varient = True

                        if is_varient:
                            if str(product_variant.pk) in items:
                                q = items[str(product_variant.pk)]["quantity"]
                                items[str(product_variant.pk)
                                      ]["quantity"] = q + quantity

                            else:
                                dic = {
                                    "quantity": quantity,
                                    "amount": amount,
                                    "retail_price": retail_price,
                                    "whole_sale_price": whole_sale_price,

                                    "net_rate": net_rate,
                                    "product_discount_rate": product_discount_rate,

                                    "mrp": mrp,
                                    "expire_date": expire_date,
                                    "manufacturing_date": manufacturing_date,
                                    "batch_number": batch_number,
                                    "add_new_batch": add_new_batch,
                                    "current_batch": current_batch,

                                    "tax": tax,
                                    "tax_amount": tax_amount,
                                    "cgst_amount": cgst_amount,
                                    "sgst_amount": sgst_amount,
                                    # "gross_amount": gross_amount,

                                    "is_varient": True
                                }
                                key = product_variant.pk
                                value = dic

                        product_variant = ProductVariant.objects.get(pk=key)
                        hsn = product_variant.product.hsn
                        pro_pk = product_variant.pk


                        quantity = value["quantity"]
                        price = value["amount"]
                        tax = value["tax"]
                        tax_amount_value = value["tax_amount"]
                        product_discount_rate = value["product_discount_rate"]
                        net_rate = value["net_rate"]
                        tot = (quantity * price)

                        mrp = value["mrp"]
                        retail_price = value['retail_price']
                        whole_sale_price = value['whole_sale_price']
                        expire_date = value["expire_date"]
                        manufacturing_date = value["manufacturing_date"]
                        add_new_batch = value["add_new_batch"]
                        current_batch = value["current_batch"]
                        batch_number = value['batch_number']

                        if product_discount_rate:
                            product_discount = tot * product_discount_rate / 100
                        else:
                            product_discount = 0

                        if True:
                            tax_amount_og = cgst_amount+sgst_amount
                            cgst = cgst_amount
                            sgst = sgst_amount
                            igst = 0
                        else:
                            tax_amount_og = 0
                            cgst = 0
                            sgst = 0
                            igst = 0

                        total += (tot+tax_amount_og)-product_discount
                        total_taxable_without_amount += tot-product_discount
                        total_tax_amount += tax_amount_og
                        single_tot = tot+tax_amount_og

                        purchase_order_item_instance = PurchaseOrderItem.objects.create(
                            purchase_order=data,
                            product_variant=product_variant,
                            hsn=hsn.hsn_number,
                            retail_price=retail_price,
                            whole_sale_price=whole_sale_price,

                            batch=current_batch,
                            batch_number=batch_number,
                            add_new_batch=add_new_batch,

                            amount=price,
                            # price=batch_price,
                            mrp=mrp,

                            quantity=quantity,
                            expire_date=expire_date,
                            manufacturing_date=manufacturing_date,
                            net_rate=net_rate,
                            discount=product_discount_rate,
                            total=(single_tot-product_discount),
                            tax=tax,
                            tax_amount=tax_amount_value,
                            sgst_amount=sgst,
                            cgst_amount=cgst,
                            igst_amount=igst
                        )



                    total_amount = form.cleaned_data['subtotal']
                    data.subtotal = total_amount
                    data.save()

                    # # -------------------- checking for purchase
                    # if Purchase.objects.filter(purchase_order=data, is_deleted=False).exists():
                    #     purchase = Purchase.objects.filter(
                    #         purchase_order=data, is_deleted=False).last()
                    #     is_purchased = False

                    #     purchased_items = PurchaseItem.objects.filter(
                    #         purchase_id=purchase.pk)
                    #     ordered_items = PurchaseOrderItem.objects.filter(
                    #         purchase_order_id=data.pk)

                    #     if purchased_items.count() == ordered_items.count() and ordered_items.count() > 0:
                    #         is_purchased = True

                    #         for item in purchased_items:
                    #             product = item.product
                    #             product_variant = item.product_variant
                    #             add_new_batch = item.add_new_batch
                    #             batch_number = item.batch_number
                    #             quantity = item.quantity
                    #             amount = item.amount
                    #             total = item.total
                    #             batch = item.batch

                    #             if add_new_batch:
                    #                 batch = None

                    #             if ordered_items.filter(batch=batch, quantity=quantity, batch_number=batch_number, product_variant=product_variant, add_new_batch=add_new_batch, amount=amount, total=total).exists():
                    #                 ordered_items.filter(batch=batch, quantity=quantity, batch_number=batch_number, product_variant=product_variant, add_new_batch=add_new_batch, amount=amount, total=total).update(
                    #                     is_purchased=True
                    #                 )
                    #             else:
                    #                 is_purchased = False

                    #     data.is_partial = True
                    #     data.is_purchased = is_purchased
                    #     data.save()
                    # # -------------------- purchase check ends

                    response_data = {
                        "status": "true",
                        "title": "Successfully Updated",
                        "message": "Purchase Order Successfully Updated.",
                        "redirect": "true",
                        # "redirect_url": reverse('purchases:purchase_order', kwargs={'pk': data.pk})
                        "redirect_url": reverse('purchases:purchase_orders')
                    }
                else:
                    response_data = {
                        "status": "false",
                        "stable": 'true',
                        "title": "Form validation error",
                        "message": error_message
                    }

            else:
                if FinancialYear.objects.filter(is_deleted=False, is_active=True).exists():
                    error_message = "Purchase Order date must be within active financial year."
                elif FinancialYear.objects.filter(is_deleted=False, is_active=False).exists():
                    error_message = "Don't have an active Financial year."
                else:
                    error_message = "Please Add a Financial year."

                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Financial Year error",
                    "message": error_message
                }
        else:
            message = generate_form_errors(form, formset=False)
            message += str(generate_form_errors(purchase_order_item_formset, formset=True))
            print(form.errors)
            print(purchase_order_item_formset.errors)

            if 'Amount :' in message:
                message = message.replace("Amount :", "Rate :")

            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": str(message)
            }
        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = PurchaseOrderForm(instance=instance)
        purchase_order_item_formset = PurchaseOrderItemFormset(
            prefix='purchase_order_item_formset', instance=instance)

        for x in purchase_order_item_formset:
            x.fields['batch'].queryset = Batch.objects.none()

        context = {
            "form": form,
            "is_edit": True,
            "instance": instance,
            "title": "Edit Purchase Order",
            "purchase_order_item_formset": purchase_order_item_formset,
            "url": reverse('purchases:edit_purchase_order', kwargs={'pk': pk}),
        }

        return render(request, 'purchases/purchase-order/purchase_order_edit.html', context)


@login_required
@role_required(['superadmin', 'staff_user'])
def save_purchase(request, pk):
    instance = PurchaseOrder.objects.get(pk=pk)
    order_items = PurchaseOrderItem.objects.filter(purchase_order_id=pk)

    initial = {
        'date': datetime.strftime(datetime.now().date(), '%d/%m/%Y'),
        'supplier': instance.supplier,
        'warehouse': instance.warehouse,
        'discount': instance.discount,
        'order_id': instance.order_id,
    }
    formset_initial = []

    for item in order_items:
        obj = {
            'product_variant': item.product_variant,
            'add_new_batch': item.add_new_batch,
            'batch_number': item.batch_number,
            'batch': item.batch,
            'amount': item.amount,
            'quantity': item.quantity,
        }
        formset_initial.append(obj)

    PurchaseItemFormset = formset_factory(PurchaseItemForm, extra=1)
    purchase_item_formset = PurchaseItemFormset(
        prefix="purchase_item_formset", initial=formset_initial)

    for x in purchase_item_formset:
        x.fields['batch'].queryset = Batch.objects.none()

    form = PurchaseForm(initial=initial)
    voucher_form = PurchaseVoucherForm(initial={'transfer_type': 10})
    supplier_form = SupplierCreateFromForm()

    context = {
        "form": form,
        "order_pk": pk,
        "instance": instance,
        "url": reverse('purchases:create_new_purchase'),
        "supplier_form": supplier_form,
        "voucher_form": voucher_form,
        "purchase_item_formset": purchase_item_formset,
        "title": "Create Purchase",
        "redirect": True,
        "is_edit": True,
    }

    return render(request, 'purchases/entry.html', context)


@login_required
@role_required(['superadmin', 'staff_user'])
def print_purchase_order(request, pk):
    instance = get_object_or_404(PurchaseOrder.objects.filter(pk=pk))
    state = instance.vendor.state
    sale_category = "intra_state"

    if not state == "Kerala":
        sale_category = "inter_state"

    purchase_items = PurchaseOrderItem.objects.filter(purchase_order_id=pk)

    total_subtotal = 0
    grant_total = 0
    total_cgst = 0
    total_sgst = 0
    total_igst = 0

    for purchase_item in purchase_items:
        tax_amount = purchase_item.tax_amount
        subtotal = purchase_item.subtotal()
        gst_added_total = purchase_item.total
        grant_total += gst_added_total
        total_subtotal += subtotal

        if sale_category == "intra_state":
            sgst = tax_amount/2
            cgst = tax_amount/2
            sgst_rate = purchase_item.tax/2
            cgst_rate = purchase_item.tax/2
            igst = 0
            igst_rate = 0

            total_cgst += cgst
            total_sgst += sgst
        else:
            igst = tax_amount
            igst_rate = purchase_item.tax
            sgst = 0
            cgst = 0
            sgst_rate = 0
            cgst_rate = 0

            total_igst += igst

    grant_total_value = grant_total
    total_amount = instance.subtotal - instance.round_off

    context = {
        "title": "Purchase Order ",
        "instance": instance,
        "purchase_items": purchase_items,
        "purchase_category": sale_category,
        "grant_total_value": grant_total_value,
        "total_subtotal": total_subtotal,
        "total_cgst": total_cgst,
        "total_sgst": total_sgst,
        "total_igst": total_igst,
        "total_amount": total_amount,
    }

    return render(request, 'purchases/purchase-order/print_purchase_order.html', context)


@login_required
def purchase_export(request):
    purchase_filter = PurchaseFilter(request)
    instances = purchase_filter.get_filtered_results()

    export_to_excel_utils = ExportToExcelUtils(instances, PurchaseExportSerializer, request, "purchase_export")

    returned_file_url = export_to_excel_utils.export_to_excel()
    return HttpResponseRedirect(returned_file_url)