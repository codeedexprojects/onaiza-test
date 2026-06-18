# Standard Libraries
import json
import datetime
from decimal import Decimal
from datetime import timedelta
# Third Party Libraries
from dal import autocomplete
# Django Libraries
from django.shortcuts import render, get_object_or_404
from django.http.response import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, Max, F, ExpressionWrapper, DecimalField
from django.forms.models import inlineformset_factory
from django.forms.formsets import formset_factory
from django.template.loader import render_to_string
# Local Libraries
from main.functions import get_auto_id, generate_form_errors, get_date_updated_request, get_a_id
from main.decorators import role_required, ajax_required
from main.utils.export_to_excel import ExportToExcelUtils
from api.v1.general.serializers import PurchaseExportSerializer
from api.v1.general.serializers import SaleExportSerializer
from finance.models import AccountGroup, AccountHead, ReceiptVoucher, InvoicePrefix, FinancialYear
from customers.models import Customer, PrivilegePoint
from customers.forms import CustomerFilterForm
from users.functions import get_warehouse
from staffs.models import Staff
from products.models import Product, ProductVariant
from general.models import Batch, InvoiceDesign
from sales.models import Sale, SaleItem, SaleReturn, SaleReturnItem
from sales.forms import SaleForm, SaleItemForm, CustomerCreateFromForm, SaleReturnForm, SaleReturnItemForm, SaleVoucherForm
from sales.functions import return_commission, create_or_update_commission, get_sale_invoice_id, update_batch_stock
from sales.filters import SaleFilter


class SaleAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self, *args, **kwargs):
        items = Sale.objects.filter(is_deleted=False).order_by('-sale_date')
        customer = self.forwarded.get('customer', None)

        if Staff.objects.filter(user=self.request.user).exists():
            warehouse = Staff.objects.get(user=self.request.user).warehouse
            items = items.filter(warehouse=warehouse)

        if customer:
            items = items.filter(customer=customer)

        if self.q:
            items = items.filter(
                Q(auto_id__istartswith=self.q) |
                Q(customer__name__istartswith=self.q) |
                Q(customer__address__istartswith=self.q) |
                Q(customer__email__istartswith=self.q) |
                Q(customer__phone__istartswith=self.q)
            )

        return items


class SaleReturnAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self, *args, **kwargs):
        items = SaleReturn.objects.filter(is_deleted=False).order_by('-time')
        customer = self.forwarded.get('customer', None)
        if customer:
            items = items.filter(customer=customer)

        if self.q:
            items = items.filter(
                Q(auto_id__istartswith=self.q) |
                Q(customer__name__istartswith=self.q) |
                Q(customer__address__istartswith=self.q) |
                Q(customer__email__istartswith=self.q) |
                Q(customer__phone__istartswith=self.q)
            )

        return items


def customer_from_create(request):
    if request.method == 'POST':
        form = CustomerCreateFromForm(request.POST)
        code = "onaiza"
        if form.is_valid():
            # create customer
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            phone = form.cleaned_data['phone']
            opening_type = form.cleaned_data['opening_type']
            opening_balance = form.cleaned_data['opening_balance']
            username = str(code) + str(phone)
            password = phone

            data = form.save(commit=False)
            data.creator = request.user
            data.updater = request.user
            data.auto_id = get_auto_id(Customer)
            current_balance = 0
            if opening_type == 'debit':
                current_balance += opening_balance
            elif opening_type == 'credit':
                current_balance -= opening_balance
            data.current_balance = current_balance
            data.save()

            # if not User.objects.filter(username=username).exists():
            #     if not User.objects.filter(email=email).exists():
            #         user = User.objects.create_user(
            #             username=username,
            #             password=password,
            #             email=email,
            #             first_name=name
            #         )
            #         # adding user to Group
            #         if Group.objects.filter(name="customer_user").exists():
            #             group = Group.objects.get(name="customer_user")
            #         else:
            #             group = Group.objects.create(name="customer_user")

            #         group.user_set.add(user)
            #         data.user = user
            #         data.save()

            #         message1 = "You can use the bellow Credential: %s is your Website Link" % (
            #             phone)
            #         message2 = "%s is your Username" % (username)
            #         message3 = ": %s is your Password." % (password)
            #         message4 = "Happy Purchase"
            #         message = str(message1) + str(message2) + \
            #             str(message3) + str(message4)

            # sendSMS(phone, message)
            response_data = {
                "status": "true",
                "title": "Successfully created",
                "message": " successfully created.",
                "redirect": "true",
                "redirect_url": reverse('sales:create')
            }

            return HttpResponse(json.dumps(response_data), content_type='application/javascript')

        else:
            message = generate_form_errors(form, formset=False)
            print(message)
            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": str(message)
            }

            return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def create(request):
    try_error_message = ''
    try:
        SaleItemFormset = formset_factory(SaleItemForm, extra=3)
        sale_id = get_sale_invoice_id(request)

    except Exception as e:
        try_error_message += '%s (%s)' % (e.message, type(e))

    if request.method == 'POST':
        try:
            ModifiedRequest = get_date_updated_request(request.POST.copy(), [
                                                       'sale_date', 'shipment_date', 'cheque_date', 'draft_date', 'transfer_date'])

            form = SaleForm(ModifiedRequest)
            voucher_form = SaleVoucherForm(ModifiedRequest)
            sale_item_formset = SaleItemFormset(
                request.POST, prefix='sale_item_formset')

        except Exception as e:
            try_error_message += '%s (%s)' % (e.message, type(e))

        all_forms_valid = False
        try:
            if form.is_valid() and sale_item_formset.is_valid() and voucher_form.is_valid():
                all_forms_valid = True

        except Exception as e:
            try_error_message += '%s (%s)' % (e.message, type(e))

        if try_error_message:
            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": try_error_message
            }
            return HttpResponse(json.dumps(response_data), content_type='application/javascript')

        if all_forms_valid:
            try:
                sale_date = form.cleaned_data['sale_date']
                customer = form.cleaned_data['customer']
                warehouse = form.cleaned_data['warehouse']
                total_sale_amount = form.cleaned_data['total']
                sale_category = form.cleaned_data['sale_category']
                sale_type = form.cleaned_data['sale_type']
                subtotalamount = form.cleaned_data['subtotal']
                add_gst = form.cleaned_data['add_gst']
                paid = form.cleaned_data['paid']
                main_discount_rate = form.cleaned_data['discount_rate']
                net_discount = form.cleaned_data['discount']
                customer_address = form.cleaned_data['customer_address']
                privilege_point_used = form.cleaned_data['privilege_point_used']
                privilege_point_amnt = form.cleaned_data['privilege_point_amnt']
                use_privilege_point = form.cleaned_data['use_privilege_point']

                if use_privilege_point:
                    if privilege_point_used > customer.current_privilege_points:
                        response_data = {
                            "status": "false",
                            "stable": "true",
                            "title": "Form validation error",
                            "message": "Customer have onlly" + str(customer.current_privilege_points) + "Points"
                        }

                        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

                count_sale = 0
                for f in sale_item_formset:
                    count_sale += 1

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

                if not count_sale:
                    response_data = {
                        "status": "false",
                        "stable": "true",
                        "title": "Form validation error",
                        "message": f"No sale items"
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

            except Exception as e:
                try_error_message += '%s (%s)' % (e.message, type(e))

            if FinancialYear.objects.filter(is_deleted=False, is_active=True, start_date__date__lte=sale_date, end_date__date__gte=sale_date).exists():
                financial_year = FinancialYear.objects.get(is_deleted=False, start_date__date__lte=sale_date, end_date__date__gte=sale_date)
                if customer:
                    if customer.name == 'Default Customer' and not total_sale_amount == paid:
                        response_data = {
                            "status": "false",
                            "stable": "true",
                            "title": "Form validation error",
                            "message": "Paid and total must equal to Default Customer."
                        }
                        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

                    items = {}  # used to save as single item when same product is choosen multiple times
                    sale_item = None
                    batch_items = []  # to save all items as seperate sale items
                    stock_items = {}  # to check stock availability
                    stock_ok = True
                    batch_ok = True
                    discount_ok = True
                    error_message = ''

                    try:
                        for f in sale_item_formset:
                            if f.cleaned_data != {}:
                                batch = f.cleaned_data['batch']
                                # product = f.cleaned_data['product']
                                product_variant = f.cleaned_data['product_variant']

                                if not batch:
                                    if Batch.objects.filter(product_variant=product_variant, stock__gt=0).exists():
                                        error_message = "Please choose a batch before submission."
                                    else:

                                        if product_variant:
                                            name = product_variant.product.name + product_variant.title

                                        error_message = f"{name} is out of stock."

                                    response_data = {
                                        "status": "false",
                                        "stable": "true",
                                        "title": "Form validation error",
                                        "message": error_message
                                    }
                                    return HttpResponse(json.dumps(response_data), content_type='application/javascript')

                    except Exception as e:
                        try_error_message += '%s (%s)' % (e.message, type(e))

                    try:
                        for f in sale_item_formset:
                            if f.cleaned_data != {}:
                                # product = f.cleaned_data['product']
                                product_variant = f.cleaned_data['product_variant']
                                qty = f.cleaned_data['quantity']
                                mrp = f.cleaned_data['mrp']
                                amount = f.cleaned_data['amount']
                                discount_rate = f.cleaned_data['discount_rate']
                                discount = f.cleaned_data['discount']
                                batch = f.cleaned_data['batch']
                                comments = f.cleaned_data['comments']
                                # net_rate = f.cleaned_data['net_rate']

                                selling_price = amount
                                discount_rate = discount_rate * 100 / selling_price

                                tax_amount = 0
                                tax_added_price = 0
                                tax_excluded_cost = 0
                                discount_amount = 0
                                is_varient = False
                                product_variant_instance = None

                                if product_variant:
                                    if ProductVariant.objects.filter(is_deleted=False, pk=product_variant.pk).exists():
                                        product_variant_instance = ProductVariant.objects.get(is_deleted=False, pk=product_variant.pk)
                                        is_varient = True

                                if product_variant_instance.product.hsn:
                                    hsn_number = product_variant_instance.product.hsn.hsn_number

                                    gst_rate = product_variant_instance.product.hsn.igst_rate
                                    cost = product_variant_instance.cost
                                    gst = gst_rate

                                else:
                                    hsn_number = ''
                                    gst = ''

                                if is_varient:
                                    if str(product_variant.pk) in items:
                                        dic = {
                                            "quantity": qty,
                                            "amount": amount,
                                            "price": product_variant.cost,
                                            "hsn": hsn_number,
                                            "gst": gst,
                                            # "net_rate": net_rate,
                                            "discount_rate": discount_rate,
                                            'batch': batch,
                                            "is_varient": True
                                        }
                                        q = items[str(
                                            product_variant.pk)]["quantity"]

                                        items[str(product_variant.pk)
                                              ]["quantity"] = q + qty
                                    else:
                                        dic = {
                                            "quantity": qty,
                                            "amount": amount,
                                            "price": product_variant.cost,
                                            "hsn": hsn_number,
                                            "gst": gst,
                                            # "net_rate": net_rate,
                                            "discount_rate": discount_rate,
                                            'batch': batch,
                                            "is_varient": True
                                        }
                                        items[str(product_variant.pk)] = dic

                                # if str(batch.pk) in batch_items:
                                #     batch_ok = False
                                #     if batch.product_variant:
                                #         error_message += f'same batch of {batch.product_variant} is used more than once.\n'
                                #     else:
                                #         error_message += f'same batch of {batch.product} is used more than once.\n'

                                # else:
                                obj = {
                                    'batch': batch,
                                    "quantity": qty,
                                    "amount": amount,
                                    "mrp": mrp,
                                    "hsn": product_variant_instance.product.hsn,
                                    "gst": gst,
                                    "discount": discount,
                                    "discount_rate": discount_rate,
                                }
                                batch_items.append(obj)

                                obj2 = {
                                    'batch': batch,
                                    "quantity": qty,
                                    "amount": amount,
                                    "mrp": mrp,
                                    "hsn": product_variant_instance.product.hsn,
                                    "gst": gst,
                                    "discount": discount,
                                    "discount_rate": discount_rate,
                                }
                                # to check stock availability
                                if str(batch.pk) in stock_items:
                                    stock_items[str(batch.pk)]['quantity'] += qty

                                else:
                                    stock_items[str(batch.pk)] = obj2

                    except Exception as e:
                        try_error_message += '%s (%s)' % (e.message, type(e))

                    # Checking the stock available for this product
                    try:
                        for key, value in stock_items.items():
                            batch = Batch.objects.get(pk=key)
                            product = batch.product
                            product_variant = None
                            is_varient = False
                            stock = batch.stock
                            name = product.name

                            if batch.product_variant:
                                product_variant = batch.product_variant
                                name = product_variant.title
                                is_varient = True

                            disc_limit = product_variant.discount_limit
                            quantity = value['quantity']
                            discount_rate = value['discount']/quantity

                            if discount_rate > disc_limit and disc_limit > 0:
                                discount_ok = False
                                error_message += f"discount given for {product.name} exceeded its discount limit\n"

                            if quantity > stock:
                                stock_ok = False

                                error_message += f"{name} has only {stock} in stock in batch {batch}, You entered {quantity} quantity\n"

                    except Exception as e:
                        try_error_message += '%s (%s)' % (e.message, type(e))

                    if try_error_message:
                        response_data = {
                            "status": "false",
                            "stable": "true",
                            "title": "Form validation error",
                            "message": try_error_message
                        }
                        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

                    if stock_ok and discount_ok and batch_ok:
                        auto_id = get_auto_id(Sale)
                        a_id = get_a_id(Sale, warehouse)
                        sale_date = datetime.datetime.combine(sale_date, datetime.datetime.now().time())

                        # Sale Id
                        sale_no = 1
                        if Sale.objects.filter(is_deleted=False).exists():
                            latest_sale_no = Sale.objects.filter(is_deleted=False).aggregate(Max('auto_id'))
                            latest_sale = latest_sale_no['auto_id__max']
                            sale_no = latest_sale + 1

                        track = sale_no
                        track = 1
                        if Sale.objects.all().exists():
                            latest_tracking_no = Sale.objects.all().latest("date_added")
                            track = latest_tracking_no.tracking_no + 1

                        ledger_data = None
                        sale_id = form.cleaned_data['sale_id']

                        data1 = form.save(commit=False)

                        data1.tracking_no = track
                        data1.tracking_id = "TR" + str(data1.tracking_no)
                        data1.creator = request.user
                        data1.sale_id = sale_id
                        data1.updater = request.user
                        data1.auto_id = auto_id
                        data1.a_id = a_id
                        data1.sale_date = sale_date
                        data1.discount = net_discount
                        data1.discount_rate = main_discount_rate
                        data1.customer_address = customer_address
                        data1.sale_no=sale_no
                        data1.save()

                        subtotal = 0
                        all_tax_total = 0
                        tax_excluded_amount = 0
                        discount = 0
                        actual_gst_sum = 0
                        purchase_amount = 0
                        purchase_total = 0
                        total_net_rate = 0
                        exclude_discount = 0
                        balance = 0

                        # for key, value in batch_items.items():
                        for value in batch_items:

                            batch = value['batch']
                            product_variant = None
                            is_varient = False

                            if batch.product_variant:
                                product_variant = batch.product_variant
                                is_varient = True

                            qty = value["quantity"]
                            amount = value["amount"]
                            mrp = value["mrp"]
                            discount_amount = value["discount"]
                            discount_rate = value["discount_rate"]

                            net_rate = 0

                            selling_price = amount
                            sel = selling_price

                            gst_rate = product_variant.product.hsn.igst_rate
                            cost = product_variant.cost
                            # ====pppp
                            igst_p = product_variant.igst
                            sgst_p = product_variant.sgst
                            cgst_p = product_variant.cgst

                            amount = selling_price
                            taxable_amount = (qty * sel)
                            gst_amount = 0
                            igst = gst_amount
                            cgst = 0
                            sgst = 0

                            if add_gst == True:
                                gst_amount = ((taxable_amount*gst_rate)/100)
                            else:
                                gst_amount = 0

                            if sale_category == "inter_state":
                                igst = gst_amount
                                cgst = 0
                                sgst = 0
                            elif sale_category == "intra_state":
                                igst = 0
                                cgst = gst_amount/2
                                sgst = gst_amount/2

                            if discount_rate:
                                discount = (taxable_amount * discount_rate)/100
                            else:
                                discount = 0

                            all_tax_total += gst_amount
                            tax_excluded_amount += taxable_amount
                            sub = taxable_amount-discount
                            subtotal += sub
                            exclude_discount = taxable_amount+gst_amount
                            total_net_rate += exclude_discount

                            price = product_variant.cost
                            actual_price = (price*qty)
                            actual_gst = Decimal((actual_price*gst)/100)

                            actual_gst_sum += actual_gst
                            purchase_amount = actual_price+actual_gst
                            purchase_total += purchase_amount

                            new_net_rate = round(
                                sub/(1+(sgst_p/100)+(cgst_p/100)), 2)
                            sgst_amount = round(new_net_rate * sgst_p / 100, 2)
                            cgst_amount = round(new_net_rate * cgst_p / 100, 2)
                            igst_amount = 0

                            print(sgst_p, 'sgst_p')
                            print(cgst_p, 'cgst_p')
                            # sale_taxable_amount = sel - (((sel * sgst_p)/100) + ((sel * cgst_p)/100) + ((sel * cess)/100))

                            sale_taxable_amount = round(sel/(1+(sgst_p/100)+(cgst_p/100)), 2)
                            # purchase_taxable_amount = batch.taxable_amount if batch.taxable_amount else 0

                            purchase_taxable_amount = round(cost/(1+(sgst_p/100)+(cgst_p/100)), 2)

                            hsn_number = ''
                            if product.hsn:
                                hsn_number = product.hsn.hsn_number

                            # Vendor Commission
                            commission_amount = create_or_update_commission(sale_date,product.vendor,taxable_amount)

                            if is_varient == True:
                                sale_item = SaleItem.objects.create(
                                    sale=data1,
                                    product_variant=product_variant,
                                    quantity=qty,
                                    gst_amount=gst_amount,
                                    sub_total=taxable_amount,
                                    discount_rate=discount_rate,
                                    amount=sel,
                                    mrp=mrp,
                                    discount=discount_amount,
                                    net_rate=new_net_rate,
                                    total=sub,
                                    price=product_variant.cost,
                                    hsn=str(product_variant.product.hsn),
                                    gst=gst,
                                    igst=igst_amount,
                                    sgst=sgst_amount,
                                    cgst=cgst_amount,
                                    batch=batch,
                                    purchase_taxable_amount=purchase_taxable_amount,
                                    sale_taxable_amount=sale_taxable_amount,
                                    commission_amount=commission_amount,
                                )

                                if batch:
                                    update_batch_stock(
                                        batch.pk, qty, "decrease")

                        # PrivilegePoint Start
                        privilege_point_instance = PrivilegePoint.objects.filter(is_deleted=False).first()

                        if privilege_point_instance:
                            priv_minimum_amount = privilege_point_instance.minimum_amount

                            if use_privilege_point:
                                used_amnt = privilege_point_used * privilege_point_instance.value_of_point
                                total_sale_amount = total_sale_amount - used_amnt

                                curent_point = customer.current_privilege_points - privilege_point_used

                                Customer.objects.filter(pk=customer.pk).update(current_privilege_points=curent_point)
                        else:
                            priv_minimum_amount = 0
                            data1.use_privilege_point = False

                        # Gaining Privilege Point
                        if privilege_point_instance:
                            if total_sale_amount >= priv_minimum_amount:
                                gained_point = (total_sale_amount // priv_minimum_amount) * privilege_point_instance.point_gained_offline

                                cust_current_privilege_points = customer.privilege_points + gained_point
                                cust_privilege_points = customer.privilege_points + gained_point

                                Customer.objects.filter(pk=customer.pk).update(privilege_points=cust_privilege_points, current_privilege_points=cust_current_privilege_points)
                                data1.privilege_points = gained_point

                        data1.subtotal = subtotalamount
                        data1.total = total_sale_amount

                        sale_items_data = SaleItem.objects.filter(sale=data1).annotate(
                            s_taxable = F('sale_taxable_amount') * F('quantity'),
                            p_taxable = F('purchase_taxable_amount') * F('quantity')
                        )

                        data1.cgst = sale_items_data.aggregate(Sum('cgst'))['cgst__sum']
                        data1.sgst = sale_items_data.aggregate(Sum('sgst'))['sgst__sum']
                        data1.igst = sale_items_data.aggregate(Sum('igst'))['igst__sum']
                        data1.total_gst_amount = sale_items_data.aggregate(Sum('gst_amount'))['gst_amount__sum']
                        data1.sale_taxable_amount = sale_items_data.aggregate(Sum('s_taxable'))['s_taxable__sum']
                        data1.purchase_taxable_amount = sale_items_data.aggregate(Sum('p_taxable'))['p_taxable__sum']

                        if ledger_data:
                            customer_balance = ledger_data['closing_balance']
                            customer_balance_type = 'Debit'

                            if customer_balance < 0:
                                customer_balance_type = 'Credit'
                                customer_balance = abs(customer_balance)

                            data1.customer_balance = customer_balance
                            data1.customer_balance_type = customer_balance_type

                        data1.save()

                        balance = total_sale_amount - paid
                        total_amount = total_sale_amount
                        customer = data1.customer
                        payment_method = 'credit'

                        balance = total_amount - paid
                        current_balance = customer.current_balance
                        n_balance = current_balance - balance
                        Customer.objects.filter(pk=customer.pk).update(current_balance=n_balance)

                        # Finance
                        if paid > 0:
                            account_head = AccountHead.objects.get(code="sundry_debtor_customer",is_deleted=False)

                            # Set ReceiptVoucher
                            if ReceiptVoucher.objects.all().exists():
                                number = ReceiptVoucher.objects.aggregate(voucher_number=Max('voucher_number')).get('voucher_number')
                                voucher_no = int(number) + 1
                            else:
                                voucher_no = 1

                            transfer_type = voucher_form.cleaned_data['transfer_type']

                            if transfer_type == 10:
                                receipt_voucher = ReceiptVoucher.objects.create(
                                    auto_id=get_auto_id(ReceiptVoucher),
                                    creator=request.user,
                                    updater=request.user,
                                    account_head = account_head,
                                    voucher_number = voucher_no,
                                    voucher_date = data1.sale_date,
                                    title = "Sale Payment received",
                                    description = "Sale Payment received",
                                    amount = paid,
                                    transfer_type = 10,
                                    sub_ledger = customer.pk,
                                    is_system_generated = True,

                                    financial_year=financial_year,
                                    warehouse=warehouse,
                                )

                                payment_method = 'cash'

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

                                receipt_voucher = ReceiptVoucher.objects.create(
                                    auto_id=get_auto_id(ReceiptVoucher),
                                    creator=request.user,
                                    updater=request.user,
                                    account_head = account_head,
                                    voucher_number = voucher_no,
                                    voucher_date = data1.sale_date,
                                    title = "Sale Payment received",
                                    description = "Sale Payment received",
                                    amount = paid,
                                    sub_ledger = customer.pk,
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

                                    financial_year=financial_year,
                                    warehouse=warehouse,
                                )

                        data1.receipt_voucher = receipt_voucher
                        data1.payment_method = payment_method
                        data1.save()

                        response_data = {
                            "status": "true",
                            "title": "Successfully Created",
                            "message": "Sale created successfully.",
                            "redirect": "true",
                            "redirect_url": reverse('sales:sale', kwargs={'pk': data1.pk})
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
                    message = 'Please Select Customer'
                    response_data = {
                        "status": "false",
                        "stable": "true",
                        "title": message,
                    }

            else:
                if FinancialYear.objects.filter(is_deleted=False, is_active=True,).exists():
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
            error_message1 = generate_form_errors(voucher_form, formset=False)
            error_message = generate_form_errors(form, formset=False) + error_message1
            error_message += generate_form_errors(sale_item_formset, formset=True)
            print("message")
            print(voucher_form.errors, "++++++++===")
            print(form.errors, "++++++++===")
            print(sale_item_formset.errors)

            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": str(error_message)
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        sale_no = 1
        # default_customer = SundryDebtor.objects.get(name="default",address="default")
        customer_form = CustomerCreateFromForm(initial={"country": "India"})

        if Customer.objects.filter(name='Default Customer').exists():
            customer = Customer.objects.filter(
                name='Default Customer').latest('auto_id')
        else:
            customer = Customer.objects.create(
                name='Default Customer',
                auto_id=get_auto_id(Customer),
                creator=request.user,
                updater=request.user,
            )

        sale_item_formset = SaleItemFormset(prefix='sale_item_formset')

        for form in sale_item_formset:
            form.fields['product_variant'].queryset = ProductVariant.objects.none()
            form.fields['batch'].queryset = Batch.objects.none()

        warehouse = get_warehouse(request)

        sale_form = SaleForm(initial={"customer": customer, "sale_type": "b2c", 'warehouse': warehouse})
        voucher_form = SaleVoucherForm(initial={'transfer_type': 10})

        context = {
            "redirect": True,
            "form": sale_form,
            "sale_id": sale_id,
            "is_create_page": True,
            "title": "Create Sale ",
            "url": reverse('sales:create'),
            "customer_form": customer_form,
            "sale_item_formset": sale_item_formset,
            "voucher_form":voucher_form
        }

        return render(request, 'sales/entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def edit(request, pk):
    instance = get_object_or_404(Sale.objects.filter(pk=pk, is_deleted=False))
    saleitem = SaleItem.objects.filter(sale=instance)

    customer = instance.customer
    previous_amount = instance.subtotal
    previous_customer = instance.customer
    sale_id = instance.sale_id

    previous_date = instance.sale_date
    previous_amount = instance.total
    old_paid = Sale.objects.get(pk=pk).subtotal

    account_head = AccountHead.objects.get(code="sundry_debtor_customer", is_deleted=False)
    if ReceiptVoucher.objects.filter(is_deleted=False, account_head=account_head, sub_ledger=str(pk)).exists():
        voucher_instance = ReceiptVoucher.objects.filter(is_deleted=False,account_head=account_head,sub_ledger=str(pk)).last()
        old_amount = voucher_instance.amount
    else:
        voucher_instance = None
        old_amount = 0

    if SaleItem.objects.filter(sale=instance).exists():
        extra = 0
    else:
        extra = 1

    SaleItemFormset = inlineformset_factory(
        Sale,
        SaleItem,
        can_delete=True,
        extra=extra,
        form=SaleItemForm,
    )

    old_paid = instance.paid
    old_total_amount = instance.subtotal
    old_customer = Customer.objects.get(pk=instance.customer.pk)

    if request.method == 'POST':
        ModifiedRequest = get_date_updated_request(request.POST.copy(), [
                                                   'sale_date', 'shipment_date', 'cheque_date', 'draft_date', 'transfer_date'])

        form = SaleForm(ModifiedRequest, instance=instance)
        voucher_form = SaleVoucherForm(ModifiedRequest, instance=voucher_instance)
        sale_item_formset = SaleItemFormset(request.POST, prefix='sale_item_formset', instance=instance)

        if form.is_valid() and sale_item_formset.is_valid() and voucher_form.is_valid():
            privilege_point_used = form.cleaned_data['privilege_point_used']
            privilege_point_amnt = form.cleaned_data['privilege_point_amnt']
            use_privilege_point = form.cleaned_data['use_privilege_point']
            sale_date = form.cleaned_data['sale_date']
            customer = form.cleaned_data['customer']
            total_sale_amount = form.cleaned_data['total']
            sale_category = form.cleaned_data['sale_category']
            subtotalamount = form.cleaned_data['subtotal']
            add_gst = form.cleaned_data['add_gst']
            paid = form.cleaned_data['paid']
            main_discount_rate = form.cleaned_data['discount_rate']
            net_discount = form.cleaned_data['discount']
            customer_address = form.cleaned_data['customer_address']

            count_sale = 0
            for f in sale_item_formset:
                count_sale += 1

            if use_privilege_point:
                if privilege_point_used > customer.current_privilege_points:
                    response_data = {
                        "status": "false",
                        "stable": "true",
                        "title": "Form validation error",
                        "message": "Customer have onlly" + str(customer.privilege_points) + "Points"
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

            if voucher_form.cleaned_data['transfer_type'] != 30 and not paid:
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": "Please enter paid amount or change payment method to credit."
                }
                return HttpResponse(json.dumps(response_data), content_type='application/javascript')

            if voucher_form.cleaned_data['transfer_type'] == 30 and paid:
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": "Please choose a payment method if a payment is in progress."
                }
                return HttpResponse(json.dumps(response_data), content_type='application/javascript')

            if customer.name == 'Default Customer' and not total_sale_amount == paid:
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": "Paid and total must equal to Default Customer."
                }

                return HttpResponse(json.dumps(response_data), content_type='application/javascript')

            if not count_sale:
                response_data = {
                    "status": "false",
                    "stable": "true",
                    "title": "Form validation error",
                    "message": f"No sale items"
                }

                return HttpResponse(json.dumps(response_data), content_type='application/javascript')

            if FinancialYear.objects.filter(is_deleted=False, is_active=True, start_date__date__lte=sale_date, end_date__date__gte=sale_date).exists():
                financial_year = FinancialYear.objects.get(is_deleted=False, start_date__date__lte=sale_date, end_date__date__gte=sale_date)

                items = {}
                new_total_quantity = 0
                batch_items = []
                stock_items = {}  # to check stock availability
                stock_ok = True
                batch_ok = True
                discount_ok = True
                error_message = ''

                for f in sale_item_formset:
                    if f not in sale_item_formset.deleted_forms:
                        # product = f.cleaned_data['product']
                        product_variant = f.cleaned_data['product_variant']
                        qty = f.cleaned_data['quantity']
                        amount = f.cleaned_data['amount']
                        mrp = f.cleaned_data['mrp']
                        discount = f.cleaned_data['discount']
                        discount_rate = f.cleaned_data['discount_rate']
                        # net_rate = f.cleaned_data['net_rate']

                        batch = f.cleaned_data['batch']
                        new_total_quantity += qty

                        is_varient = False
                        if product_variant:
                            if ProductVariant.objects.filter(is_deleted=False, pk=product_variant.pk).exists():
                                is_varient = True

                        if is_varient:
                            if str(product_variant.pk) in items:
                                dic = {
                                    "quantity": qty,
                                    "amount": amount,
                                    "price": product_variant.cost,
                                    "retail_price": product_variant.retail_price,
                                    "whole_sale_price": product_variant.whole_sale_price,
                                    "hsn": product_variant.product.hsn.hsn_number,
                                    "gst": product_variant.product.hsn.igst_rate,
                                    # "net_rate": net_rate,
                                    'batch': batch,
                                    "discount_rate": discount_rate,
                                    "is_varient": True
                                }
                                q = items[str(product_variant.pk)]["quantity"]
                                items[str(product_variant.pk)
                                      ]["quantity"] = q + qty
                            else:
                                dic = {
                                    "quantity": qty,
                                    "amount": amount,
                                    "price": product_variant.cost,
                                    "retail_price": product_variant.retail_price,
                                    "whole_sale_price": product_variant.whole_sale_price,
                                    "hsn": product_variant.product.hsn.hsn_number,
                                    "gst": product_variant.product.hsn.igst_rate,
                                    'batch': batch,
                                    # "net_rate": net_rate,
                                    "discount_rate": discount_rate,
                                    "is_varient": True
                                }
                                items[str(product_variant.pk)] = dic

                        obj = {
                            "quantity": qty,
                            "batch": batch,
                            "amount": amount,
                            "mrp": mrp,
                            "discount": discount,
                            "hsn": product_variant.product.hsn,
                            "gst": product_variant.product.hsn.igst_rate,
                            "discount_rate": discount_rate,
                        }
                        # batch_items[str(batch.pk)] = obj
                        batch_items.append(obj)

                        obj2 = {
                            "quantity": qty,
                            "batch": batch,
                            "amount": amount,
                            "mrp": mrp,
                            "discount": discount,
                            "hsn": product_variant.product.hsn,
                            "gst": product_variant.product.hsn.igst_rate,
                            "discount_rate": discount_rate,
                        }
                        # to check stock availability
                        if str(batch.pk) in stock_items:
                            stock_items[str(batch.pk)]['quantity'] += qty

                        else:
                            stock_items[str(batch.pk)] = obj2

                for key, value in stock_items.items():
                    batch = Batch.objects.get(pk=key)
                    # batch = value['batch']
                    product = batch.product
                    name = product.name
                    product_variant = None
                    is_varient = False
                    prev_quantity = 0

                    if batch.product_variant:
                        product_variant = batch.product_variant
                        is_varient = True
                        name = product_variant.title

                        if SaleItem.objects.filter(sale=instance, batch=batch, product_variant=product_variant).exists():
                            prev_quantity = SaleItem.objects.filter(
                                sale=instance, batch=batch, product_variant=product_variant).aggregate(Sum('quantity'))['quantity__sum']

                    quantity = value['quantity']
                    stock = batch.stock + prev_quantity
                    product_quantity = value['quantity']

                    if product_quantity > stock:
                        stock_ok = False
                        error_message += f"{name} has only {stock} in stock in batch {batch}, You entered {quantity} quantity\n"

                if stock_ok:
                    old_balance = old_total_amount - old_paid
                    current_balance = old_customer.current_balance
                    o_balance = current_balance + old_balance

                    Customer.objects.filter(pk=old_customer.pk).update(current_balance=o_balance)

                    sale_date = datetime.datetime.combine(sale_date, datetime.datetime.now().time())

                    # update sale
                    data = form.save(commit=False)
                    data.updater = request.user
                    data.is_updated = True

                    data.subtotal = 0
                    data.total = 0
                    data.sale_id = sale_id
                    data.discount = net_discount
                    data.date_updated = datetime.datetime.now()
                    data.save()

                    # delete previous items and update stock
                    previous_sale_items = SaleItem.objects.filter(sale=instance)
                    subtotal = 0
                    old_total = 0

                    for p in previous_sale_items:
                        quantity = p.quantity
                        prev_quantity = p.quantity

                        Batch.objects.filter(pk=p.batch.pk).update(
                            stock=F('stock') + quantity
                        )

                        # Returning VendorCommission
                        if p.commission_amount>0:
                            return_commission(data.sale_date,p.product_variant.product.vendor,p.commission_amount)

                        if p.product_variant:
                            p.product_variant.stock = p.product_variant.total_stock()
                            p.product_variant.save()

                        old_total += p.total

                    previous_sale_items.delete()

                    # Privilege Point Returned
                    customer = instance.customer
                    sale_privilege_point = instance.privilege_points
                    cur_point = customer.current_privilege_points - sale_privilege_point
                    customer.current_privilege_points = cur_point
                    sale_prev_point = customer.privilege_points - sale_privilege_point
                    customer.privilege_points =sale_prev_point
                    customer.save()

                    # save items
                    subtotal = 0
                    total_commission = 0
                    commission_amount = 0
                    all_tax_total = 0
                    tax_excluded_amount = 0
                    discount = 0
                    actual_gst_sum = 0
                    purchase_amount = 0
                    purchase_total = 0
                    total_net_rate = 0
                    exclude_discount = 0

                    for value in batch_items:
                        batch = value['batch']

                        product = batch.product
                        product_variant = None
                        is_varient = False

                        if batch.product_variant:
                            product_variant = batch.product_variant
                            is_varient = True

                        qty = value["quantity"]
                        amount = value["amount"]
                        mrp = value["mrp"]
                        discount_amount = value["discount"]
                        discount_rate = value["discount_rate"]

                        selling_price = amount
                        sel = selling_price

                        hsn = product_variant.product.hsn
                        gst = product_variant.product.hsn.igst_rate

                        igst_p = product_variant.product.hsn.igst_rate
                        sgst_p = product_variant.product.hsn.sgst_rate
                        cgst_p = product_variant.product.hsn.cgst_rate

                        amount = selling_price
                        taxable_amount = (qty * sel)

                        if add_gst == True:
                            gst_amount = ((taxable_amount*product_variant.product.hsn.igst_rate)/100)
                        else:
                            gst_amount = 0

                        if sale_category == "inter_state":
                            igst = gst_amount
                            cgst = 0
                            sgst = 0
                        elif sale_category == "intra_state":
                            igst = 0
                            cgst = gst_amount/2
                            sgst = gst_amount/2

                        if discount_rate:
                            discount = (taxable_amount * discount_rate)/100
                        else:
                            discount = 0

                        all_tax_total += gst_amount
                        tax_excluded_amount += taxable_amount
                        sub = taxable_amount-discount
                        subtotal += sub
                        exclude_discount = taxable_amount+gst_amount
                        total_net_rate += exclude_discount

                        price = product_variant.cost
                        actual_price = (price*qty)
                        actual_gst = Decimal((actual_price*gst)/100)

                        actual_gst_sum += actual_gst
                        purchase_amount = actual_price+actual_gst
                        purchase_total += purchase_amount

                        new_net_rate = round(sub/(1+(sgst_p/100)+(cgst_p/100)), 2)
                        sgst_amount = round(new_net_rate * sgst_p / 100, 2)
                        cgst_amount = round(new_net_rate * cgst_p / 100, 2)
                        igst_amount = 0

                        sale_taxable_amount = round(
                            sel/(1+(sgst_p/100)+(cgst_p/100)), 2)
                        purchase_taxable_amount = batch.cost if batch.cost else 0

                        # Adding Vendor Commission
                        commission_amount = create_or_update_commission(data.sale_date,product.vendor,taxable_amount)

                        if is_varient == True:
                            sale_item = SaleItem.objects.create(
                                sale=data,
                                product_variant=product_variant,
                                # product=product_variant.product,
                                batch=batch,
                                quantity=qty,
                                gst_amount=gst_amount,
                                sub_total=taxable_amount,
                                discount_rate=discount_rate,
                                amount=sel,
                                discount=discount_amount,
                                mrp=mrp,
                                net_rate=new_net_rate,
                                total=sub,
                                price=product_variant.cost,
                                hsn=product_variant.product.hsn.hsn_number,
                                gst=product_variant.product.hsn.igst_rate,
                                igst=igst_amount,
                                sgst=sgst_amount,
                                cgst=cgst_amount,
                                purchase_taxable_amount=purchase_taxable_amount,
                                sale_taxable_amount=sale_taxable_amount,
                                commission_amount=commission_amount
                            )
                            if batch:
                                try:
                                    Batch.objects.filter(pk=p.batch.pk).update(stock=F('stock') - quantity)
                                    # update_batch_stock(batch.pk, qty, "decrease")
                                except:
                                    pass
                                product_variant.stock = product_variant.total_stock()
                                product_variant.save()

                    profit_amount = total_sale_amount-purchase_total

                     # PrivilegePoint Start
                    privi_minimum_amount = 0
                    privilege_point_instance = PrivilegePoint.objects.filter(is_deleted=False).first()

                    if privilege_point_instance:
                        privi_minimum_amount = privilege_point_instance.minimum_amount

                    if use_privilege_point:
                        # privilege_point_used
                        used_amnt =  privilege_point_used * privilege_point_instance.value_of_point
                        total_sale_amount = total_sale_amount - used_amnt
                        curent_point = customer.current_privilege_points - privilege_point_used

                        Customer.objects.filter(pk=customer.pk).update(current_privilege_points=curent_point)

                    # Gaining Privilege Point
                    if privilege_point_instance:
                        if total_sale_amount >= privi_minimum_amount:
                            gained_point = total_sale_amount/privi_minimum_amount*privilege_point_instance.point_gained_offline
                            cust_current_privilege_points = customer.privilege_points + gained_point
                            cust_privilege_points = customer.privilege_points + gained_point
                            Customer.objects.filter(
                                pk=customer.pk).update(privilege_points=cust_privilege_points, current_privilege_points=cust_current_privilege_points)
                            data.privilege_points = gained_point

                    data.subtotal = subtotalamount
                    data.total = total_sale_amount
                    data.sale_date = sale_date

                    sale_items_data = SaleItem.objects.filter(sale=data).annotate(
                        s_taxable=F('sale_taxable_amount')*F('quantity'),
                        p_taxable=F('purchase_taxable_amount')*F('quantity')
                    )

                    data.cgst = sale_items_data.aggregate(Sum('cgst'))['cgst__sum']
                    data.sgst = sale_items_data.aggregate(Sum('sgst'))['sgst__sum']
                    data.igst = sale_items_data.aggregate(Sum('igst'))['igst__sum']
                    data.sale_taxable_amount = sale_items_data.aggregate(Sum('s_taxable'))['s_taxable__sum']
                    data.purchase_taxable_amount = sale_items_data.aggregate(Sum('p_taxable'))['p_taxable__sum']

                    data.save()
                    total_amount = total_sale_amount
                    balance = total_amount - paid
                    current_balance = customer.current_balance
                    n_balance = current_balance - balance
                    Customer.objects.filter(pk=customer.pk).update(current_balance=n_balance)

                    # Finance
                    transfer_type = voucher_form.cleaned_data['transfer_type']
                    voucher_date = data.sale_date
                    payment_method = 'credit'

                    if voucher_instance:
                        if transfer_type == 10:
                            payment_method = 'cash'
                            ReceiptVoucher.objects.filter(pk=voucher_instance.pk).update(
                                voucher_date = voucher_date,
                                description = "Sale creation Updated",
                                amount = paid,
                                updater=request.user,
                                date_updated = datetime.datetime.now(),
                                transfer_type = transfer_type,

                                bank = None,
                                draft_number = None,
                                draft_date = None,
                                cheque_number = None,
                                cheque_date = None,
                                cheque_status = None,
                                transaction_number = None,
                                transfer_date = None,
                            )

                        elif transfer_type in [15, 20, 25]:
                            bank_account = voucher_form.cleaned_data['bank']

                            cheque_number = None
                            cheque_date = None
                            draft_number = None
                            draft_date = None
                            transaction_number = None
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
                                transaction_number = voucher_form.cleaned_data['transaction_number']
                                transfer_date = voucher_form.cleaned_data['transfer_date']

                            ReceiptVoucher.objects.filter(pk=voucher_instance.pk).update(
                                voucher_date = voucher_date,
                                description = "Check Out Payment Received Updated",
                                amount = paid,
                                updater=request.user,
                                date_updated = datetime.datetime.now(),
                                transfer_type = transfer_type,

                                bank = bank_account,
                                draft_number = draft_number,
                                draft_date = draft_date,
                                cheque_number = cheque_number,
                                cheque_date = cheque_date,
                                cheque_status = 20,
                                transaction_number = transaction_number,
                                transfer_date = transfer_date,
                                warehouse=data.warehouse,
                                financial_year=financial_year,
                            )

                        elif transfer_type == 30:
                            voucher_instance.is_deleted = True
                            voucher_instance.description = 'Sale payment changed to credit'
                            voucher_instance.save()

                        receipt_voucher = voucher_instance

                    else:
                        if paid > 0:
                            # Set ReceiptVoucher
                            account_group, created = AccountGroup.objects.get_or_create(name='Sundry Debtor', code="sundry_debtor",is_deleted=False)
                            account_head, created = AccountHead.objects.get_or_create(name='Sundry Debtor', code="sundry_debtor",account_group=account_group,is_deleted=False)
                            # account_head.current_balance = (account_head.current_balance + paid)
                            # account_head.save()

                            if ReceiptVoucher.objects.all().exists():
                                number = ReceiptVoucher.objects.aggregate(voucher_number=Max('voucher_number')).get('voucher_number')
                                voucher_no = int(number) + 1
                            else:
                                voucher_no = 1

                            transfer_type = voucher_form.cleaned_data['transfer_type']

                            if transfer_type == 10:
                                payment_method = 'cash'
                                receipt_voucher = ReceiptVoucher.objects.create(
                                    creator=request.user,
                                    updater=request.user,
                                    account_head = account_head,
                                    voucher_number = voucher_no,
                                    voucher_date = data.sale_date,
                                    title = "Sale Payment received",
                                    description = "Sale Payment received",
                                    amount = paid,
                                    transfer_type = 10,
                                    sub_ledger = data.pk,
                                    is_system_generated = True,
                                    warehouse=data.warehouse,
                                    financial_year=financial_year,

                                )

                            elif transfer_type in [15, 20, 25]:
                                bank = voucher_form.cleaned_data['bank']
                                cheque_number = None
                                cheque_date = None
                                status = 20
                                draft_number = None
                                draft_date = None
                                transaction_number = None
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
                                    transaction_number = voucher_form.cleaned_data['transaction_number']
                                    transfer_date = voucher_form.cleaned_data['transfer_date']

                                receipt_voucher = ReceiptVoucher.objects.create(
                                    creator=request.user,
                                    updater=request.user,
                                    account_head = account_head,
                                    voucher_number = voucher_no,
                                    system_generated_number=data.sale_id,
                                    voucher_date = data.sale_date,
                                    title = "Sale Payment received",
                                    description = "Sale Payment received",
                                    amount = paid,
                                    sub_ledger = data.pk,
                                    transfer_type = transfer_type,
                                    is_system_generated = True,

                                    bank = bank,
                                    cheque_number = cheque_number,
                                    cheque_date = cheque_date,
                                    cheque_status = status,
                                    draft_number = draft_number,
                                    draft_date = draft_date,
                                    transaction_number = transaction_number,
                                    transfer_date = transfer_date,
                                    warehouse=data.warehouse,
                                    financial_year=financial_year,
                                )

                    data.receipt_voucher = receipt_voucher
                    data.payment_method = payment_method
                    data.save()

                    referer_url = request.POST.get('referer_url')
                    if not referer_url:
                        referer_url = reverse('sales:sales')

                    response_data = {
                        "status": "true",
                        "title": "Successfully Updated",
                        "message": "Sale Successfully Updated.",
                        "redirect": "true",
                        # "redirect_url": reverse('sales:sale', kwargs={'pk': data.pk})
                        "redirect_url": referer_url
                    }
                else:
                    title = "Out of Stock"
                    if not error_message:
                        error_message = title
                    response_data = {
                        "status": "false",
                        "stable": "true",
                        "title": title,
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
            print(sale_item_formset.errors)
            message = generate_form_errors(form, formset=False)
            message += generate_form_errors(
                sale_item_formset, formset=True)

            response_data = {
                "status": "false",
                "stable": "true",
                "title": "Form validation error",
                "message": message
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = SaleForm(instance=instance)
        sale_item_formset = SaleItemFormset(
            prefix='sale_item_formset', instance=instance)
        previous_sale_items = SaleItem.objects.filter(sale=instance)

        for form_item in sale_item_formset:
            form_item.fields['batch'].queryset = Batch.objects.none()

        if voucher_instance:
            voucher_initial = {}

            if voucher_instance.transfer_date:
                voucher_initial['transfer_date'] = datetime.datetime.strftime(voucher_instance.transfer_date, '%d/%m/%Y')
            elif voucher_instance.draft_date:
                voucher_initial['draft_date'] = datetime.datetime.strftime(voucher_instance.draft_date, '%d/%m/%Y')
            elif voucher_instance.cheque_date:
                voucher_initial['cheque_date'] = datetime.datetime.strftime(voucher_instance.cheque_date, '%d/%m/%Y')

            voucher_form = SaleVoucherForm(instance=voucher_instance, initial=voucher_initial)
        else:
            voucher_form = SaleVoucherForm(initial={'transfer_type': 30})

        try:
            http_referer = request.META['HTTP_REFERER']
        except:
            http_referer = reverse('sales:sale', kwargs={'pk': pk})

        context = {
            "form": form,
            'sale_id': sale_id,
            "instance": instance,
            "voucher_form": voucher_form,
            "sale_item_formset": sale_item_formset,
            'referer_url': http_referer,
            "title": "Edit Sale #: " + str(instance.auto_id),
            "url": reverse('sales:edit', kwargs={'pk': instance.pk}),

            "is_edit": True,
            "redirect": True,
            "carousel_not_required": True,
            "data_table_not_required": True,
        }

        return render(request, 'sales/entry.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def sale(request, pk):
    instance = get_object_or_404(Sale.objects.filter(pk=pk))
    sale_items = SaleItem.objects.filter(sale=instance)

    sale_items = sale_items.annotate(
        s_taxable=F('sale_taxable_amount')*F('quantity'),
        p_taxable=F('purchase_taxable_amount')*F('quantity'),
        profit=F('s_taxable') - F('p_taxable'),
        profit_percentage=(F('profit') / F('total')) * 100
    )
    for i in sale_items:
        print(i.profit_percentage)
    print("HttpResponse")
    context = {
        "instance": instance,
        "title": "Sale : " + str(instance.sale_id),
        "voucher_instance": None,
        "sale_items": sale_items,
    }

    return render(request, 'sales/sale.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def sales(request):
    title = 'Total Number of Sales'
    filter_data = {}

    instances = Sale.objects.filter().order_by('-a_id')

    query = request.GET.get('q')
    on_date = request.GET.get('on_date')
    to_date = request.GET.get('to_date')
    from_date = request.GET.get('from_date')
    invoice_id = request.GET.get('invoice_id')
    view_option = request.GET.get('view')
    payment_method = request.GET.get('payment_method')
    # to_query = request.GET.get('t')
    # print(to_query)

    if view_option == 'active':
        filter_data['view'] = 'active'
        instances = instances.filter(is_deleted=False)
    elif view_option == 'cancelled':
        filter_data['view'] = 'cancelled'
        instances = instances.filter(is_deleted=True)
    else:
        filter_data['view'] = 'all'

    if query:
        temp_instances = instances

        instances = instances.filter(
            Q(sale_id__istartswith=query) |
            Q(tracking_id__istartswith=query) |
            Q(customer__name__icontains=query) |
            Q(customer__phone__icontains=query) |
            Q(customer__email__icontains=query) |
            Q(customer__address__icontains=query)
        )
        try:
            instances |= temp_instances.filter(total=query)
        except:
            pass
        filter_data['query'] = query

    if from_date and to_date:
        print(from_date)
        f_date = datetime.datetime.strptime(from_date, '%Y-%m-%d').date()
        t_date = datetime.datetime.strptime(to_date, '%Y-%m-%d').date()
        instances = instances.filter(sale_date__date__range=[f_date, t_date])
        title = 'Total Number of Sales (from %s to %s)' % (
            str(f_date), str(t_date))

        filter_data['from_date'] = from_date
        filter_data['to_date'] = to_date

    if on_date:
        o_date = datetime.datetime.strptime(on_date, '%Y-%m-%d').date()
        instances = instances.filter(sale_date__date=on_date)
        title = 'Total Number of Sales (On %s)' % (str(o_date))
        filter_data['on_date'] = on_date

    if invoice_id:
        instances = instances.filter(Q(sale_id__istartswith=invoice_id))
        filter_data['invoice_id'] = invoice_id

    count = instances.count()

    context = {
        'count': count,
        'filter_data': filter_data,
        "title": 'Sales',
        'on_date': on_date,
        'to_date': to_date,
        'sub_title': title,
        'from_date': from_date,
        "instances": instances,
        "confirm_reject_message": "Are you sure to reject this Sale.",
        "confirm_approve_message": "Are you sure to approve this Sale.",
    }

    return render(request, 'sales/sales.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete(request, pk):
    reason = request.GET.get('reason')
    instance = get_object_or_404(Sale.objects.filter(pk=pk))
    # update stock
    sale_items = SaleItem.objects.filter(sale=instance)

    for p in sale_items:
        quantity = p.quantity

        if p.batch:
            Batch.objects.filter(pk=p.batch.pk).update(
                stock=F('stock') + quantity
            )

            if p.product_variant:
                p.product_variant.stock = p.product_variant.total_stock()
                p.product_variant.save()

    # privilege_point
    customer = instance.customer
    sale_privilege_point = instance.privilege_points
    customer.current_privilege_points -=sale_privilege_point
    customer.privilege_points -=sale_privilege_point
    customer.save()

    instance.customer
    instance.deleted_reason = reason
    instance.is_deleted = True
    instance.date_updated = datetime.datetime.now()
    instance.save()

    balance = instance.total - instance.paid

    paid = instance.paid
    total_amount = instance.subtotal

    response_data = {
        "status": "true",
        "title": "Successfully Cancelled",
        "message": "Sale Successfully Cancelled.",
        "redirect": "true",
        "redirect_url": reverse('sales:sales')
    }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_selected_sales(request):
    pks = request.GET.get('pk')
    if pks:
        pks = pks[:-1]

        pks = pks.split(',')
        for pk in pks:
            instance = get_object_or_404(
                Sale.objects.filter(pk=pk, is_deleted=False))
            instance.is_deleted = True
            instance.date_updated = datetime.datetime.now()
            instance.save()

        response_data = {
            "status": "true",
            "title": "Successfully Cancelled",
            "message": "Selected Sale(s) Successfully Cancelled.",
            "redirect": "true",
            "redirect_url": reverse('sales:sales')
        }
    else:
        response_data = {
            "status": "false",
            "title": "Nothing selected",
            "message": "Please select some items first.",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def get_product_items(request):
    pk = request.GET.get('id')
    barcode = request.GET.get('barcode')
    batch_id = request.GET.get('batch_id')
    is_purchase = request.GET.get('is_purchase')
    warehouse = request.GET.get('warehouse')

    product_exists = False
    product_variant_exists = False
    current_item = None
    current_varient = ''
    varient_barcode = False
    variences = []
    batch_list = []
    product_varience = None
    product_list_item = None
    product_name = ''
    batch = ""

    if warehouse:
        if barcode == "yes":
            if ProductVariant.objects.filter(is_deleted=False, product__vendor__isnull=True, product_code__iexact=pk).exists():
                current_item = ProductVariant.objects.get(is_deleted=False, product__vendor__isnull=True, product_code__iexact=pk)
                item = current_item.product
                batch = Batch.objects.filter(is_deleted=False, product_variant=current_item, warehouse=warehouse)
                product_varience = ProductVariant.objects.filter(is_deleted=False, product__vendor__isnull=True, product=item).exclude(pk=current_item.pk)

                product_name = str(item)
                varient_barcode = True
                product_variant_exists = True
                current_varient = str(current_item.pk)
        else:
            if ProductVariant.objects.filter(is_deleted=False, product_code=pk).exists():
                product_varience = ProductVariant.objects.get(is_deleted=False, product_code=pk)
                batch = Batch.objects.filter(is_deleted=False, product_variant=product_varience, warehouse=warehouse).exclude(product_variant__isnull=False)
                product_exists = True
                product_name = str(product_varience)

            elif Product.objects.filter(is_deleted=False, pk=pk).exists():
                item = Product.objects.get(is_deleted=False, pk=pk)
                product_varience = ProductVariant.objects.filter(is_deleted=False, product__vendor__isnull=True, product=item)
                batch = Batch.objects.filter(is_deleted=False, product=item).exclude(product_variant__isnull=False)
                product_exists = True
                product_name = str(item)

        if current_item:
            product_list_item = ProductVariant.objects.get(is_deleted=False, pk=current_item.pk)

            varian = {
                'varience_pk': str(product_list_item.pk),
                'varience_name': product_list_item.title,
            }
            variences.append(varian)

        if product_varience:
            for varience in product_varience:
                varian = {
                    'varience_pk': str(varience.pk),
                    'varience_name': varience.title,
                }
                variences.append(varian)

        default_batch = {}

        last_purchase_cost = 0

        # if is_purchase == 'yes':
        #     pass
        # else:
        #     batch = batch.filter(stock__gt=0)

        if batch_id and batch_id not in ['', 'None']:
            if not batch.filter(pk=batch_id, product_variant=product_varience, warehouse=warehouse).exists():
                batch |= Batch.objects.filter(
                    pk=batch_id, product_variant=product_varience, warehouse=warehouse)

        if batch:
            for bat in batch:
                ba_dict = {
                    'pk': str(bat.pk),
                    'stock': str(bat.stock),
                    'price': str(""),
                    'cost': str(bat.cost),
                    'mrp': str(bat.mrp),
                    'text': str(bat),
                    'retail_price': str(bat.retail_price),
                    'whole_sale_price': str(bat.whole_sale_price),
                }
                batch_list.append(ba_dict)

                if bat.batch_number == '0DEFLT':
                    default_batch = {
                        'pk': str(bat.pk),
                        'stock': str(bat.stock),
                        'price': str(""),
                        'cost': str(bat.cost),
                        'mrp': str(bat.mrp),
                        'text': str(bat),
                        'retail_price': str(bat.retail_price),
                        'whole_sale_price': str(bat.whole_sale_price),
                    }

        if product_exists:
            if item.brand:
                brand_data = {
                    'name': item.brand.name,
                    'pk': str(item.brand.pk)
                }
            else:
                brand_data = {}
            response_data = {
                'status': 'true',
                # 'price': str(item.price),
                'retail_price': str(item.retail_price),
                'whole_sale_price': str(item.whole_sale_price),
                'product_code': item.product_code,
                'mrp': str(item.mrp),
                'name': item.name,
                'pk': str(item.pk),
                # 'cost' : str(item.cost),
                'hsn': str(item.hsn),
                'igst': str(item.igst),
                'sgst': str(item.product.hsn.sgst_rate),
                'cgst': str(item.product.hsn.cgst_rate),
                'cost': str(item.cost),
                'unit': str(item.unit_type),
                # 'cess': str(item.cess),
                # 'stock': str(item.stock),
                'stock': str(0),
                'discount_limit': str(item.discount_limit),
                'varience': variences,
                'brand_data': brand_data,
                'batch_list': batch_list,
                'product_name': product_name,
                "default_batch": default_batch,
                'varient_barcode': varient_barcode,
                'current_varient': current_varient,
                'last_cost': str(last_purchase_cost)
            }

        elif product_variant_exists:
            if current_item.product.brand:
                variant_name = str(current_item.product.brand)+str('-') + \
                    str(current_item.product.name) + \
                    str('-')+str(current_item.title)
            else:
                variant_name = str(current_item.product.name) + \
                    str('-')+str(current_item.title)
            unit = None
            discount_limit = 0
            response_data = {
                'status': 'true',
                # 'price': str(current_item.price),
                'retail_price': str(current_item.retail_price),
                'whole_sale_price': str(current_item.whole_sale_price),
                'product_code': current_item.product_code,
                'mrp': str(current_item.mrp),
                'name': current_item.product.name,
                'pk': str(current_item.product.pk),
                # 'cost' : str(current_item.cost),
                'hsn': str(current_item.product.hsn),
                'igst': str(current_item.product.hsn.igst_rate),
                'sgst': str(current_item.product.hsn.sgst_rate),
                'cgst': str(current_item.product.hsn.cgst_rate),
                'cost': str(current_item.cost),
                'unit': current_item.title,
                'cess': "",
                'stock': str(0),
                # 'stock': str(current_item.stock),
                'discount_limit': discount_limit,
                'varience': variences,
                'batch_list': batch_list,
                'product_name': product_name,
                "default_batch": default_batch,
                'varient_barcode': varient_barcode,
                'current_varient': current_varient,
                'last_cost': str(last_purchase_cost),
                'variant_name': variant_name,
            }

        else:
            if barcode == "yes":
                response_data = {
                    'status': 'false',
                    'title': 'Product not found',
                    'message': "A product with given code was not found",
                }
            else:
                response_data = {
                    'status': 'false',
                    'title': 'Product data not found',
                    'message': "Details of the selected Product is not available",
                }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        response_data = {
            'status': 'false',
            'title': 'Warehouse not selected yet',
            'message': "Please Select Warehouse",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def get_product_variant_items(request):
    pk = request.GET.get('id')
    barcode = request.GET.get('barcode')
    batch_id = request.GET.get('batch_id')
    is_purchase = request.GET.get('is_purchase')
    warehouse = request.GET.get('warehouse')

    product_exists = False
    product_variant_exists = False

    if warehouse:
        if barcode == "yes":
            if ProductVariant.objects.filter(is_deleted=False, product_code__iexact=pk).exists():
                item = ProductVariant.objects.get(is_deleted=False, product_code__iexact=pk)
                batch = Batch.objects.filter(warehouse=warehouse, product_variant=item, is_deleted=False)
                product_variant_exists = True
        else:
            if ProductVariant.objects.filter(is_deleted=False, pk=pk).exists():
                item = ProductVariant.objects.get(is_deleted=False, pk=pk)
                product_variant_exists = True

                batch = Batch.objects.filter(warehouse=warehouse, product_variant=item, is_deleted=False)

        batch_list = []
        default_batch = {}

        if product_variant_exists:
            if is_purchase == 'yes':
                pass
            else:
                batch = batch.filter(warehouse=warehouse, stock__gt=0)

                if batch_id and batch_id not in ['', 'None']:
                    if not batch.filter(pk=batch_id).exists():
                        batch |= Batch.objects.filter(pk=batch_id)

        last_purchase_cost = 0

        if batch:
            for bat in batch:
                ba_dict = {
                    'pk': str(bat.pk),
                    'stock': str(bat.stock),
                    'retail_price': str(bat.retail_price),
                    'whole_sale_price': str(bat.whole_sale_price),
                    'cost': str(bat.cost),
                    'mrp': str(bat.mrp),
                    'text': str(bat),
                }
                batch_list.append(ba_dict)

                if bat.batch_number == '0DEFLT':
                    default_batch = {
                        'pk': str(bat.pk),
                        'stock': str(bat.stock),
                        'retail_price': str(bat.retail_price),
                        'whole_sale_price': str(bat.whole_sale_price),
                        'cost': str(bat.cost),
                        'mrp': str(bat.mrp),
                        'text': str(bat),
                    }

        if product_variant_exists:

            response_data = {
                'status': 'true',
                'retail_price': str(item.retail_price),
                'whole_sale_price': str(item.whole_sale_price),
                'product_code': item.product_code,
                'mrp': str(item.mrp),
                'name': item.title,
                'pk': str(item.pk),
                'cost': str(item.cost),
                'hsn': str(item.product.hsn),
                'igst': str(item.igst),

                'cost': str(item.cost),
                'unit': str(item.unit),
                'cgst': str(item.cgst),
                'sgst': str(item.sgst),
                # 'stock': str(item.stock),
                'stock': str(0),
                'batch_list': batch_list,
                'default_batch': default_batch,
                'discount_limit': str(item.discount_limit),
                'last_cost': str(last_purchase_cost),
            }

        else:
            response_data = {
                'status': 'false',
                'message': "Not exist",
            }

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')
    else:
        response_data = {
            'status': 'false',
            'message': "Please Select Warehouse",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def get_varient(request):
    pk = request.GET.get('id')
    product_variant_exists = False

    if ProductVariant.objects.filter(pk=pk).exists():
        item = ProductVariant.objects.get(pk=pk)
        product_variant_exists = True

        batch = Batch.objects.filter(is_deleted=False)

    batch_list = []
    default_batch = {}

    batch = batch.filter(stock__gt=0)
    last_purchase_cost = 0

    if batch:
        for bat in batch:
            ba_dict = {
                'pk': str(bat.pk),
                'stock': str(bat.stock),
                'retail_price': str(bat.retail_price),
                'whole_sale_price': str(bat.whole_sale_price),
                'cost': str(bat.cost),
                'mrp': str(bat.mrp),
                'text': str(bat),
            }
            batch_list.append(ba_dict)

            if bat.batch_number == '0DEFLT':
                default_batch = {
                    'pk': str(bat.pk),
                    'stock': str(bat.stock),
                    'retail_price': str(bat.retail_price),
                    'whole_sale_price': str(bat.whole_sale_price),
                    'cost': str(bat.cost),
                    'mrp': str(bat.mrp),
                    'text': str(bat),
                }

    if product_variant_exists:
        is_default = 'no'
        if item.is_default:
            is_default = 'yes'
        response_data = {
            'status': 'true',
            'title': item.title,
            'is_default': is_default,
            'product_code': item.product_code,
            'batch_number': item.batch_number,
            'igst': str(item.igst),
            'cgst': str(item.cgst),
            'sgst': str(item.sgst),
            'cost': str(item.cost),
            'mrp': str(item.mrp),
            'retail_price': str(item.retail_price),
            'whole_sale_price': str(item.whole_sale_price),
            'discount_limit': str(item.discount_limit),
            'expire_date': str(item.expire_date),
            'manufacturing_date': str(item.manufacturing_date),
            'warehouse_pk': str(item.warehouse.pk),
            'warehouse': str(item.warehouse.name),


            'hsn': str(item.product.hsn),
            'pk': str(item.pk),

            'unit_of_measurement': str(item.unit_of_measurement),
            'unit_of_measurement_pk': str(item.unit_of_measurement.pk),
            'unit': str(item.unit),
            'unit_pk': str(item.unit.pk),
            # 'stock': str(item.stock),
            'stock': str(0),
            'batch_list': batch_list,
            'default_batch': default_batch,
            'last_cost': str(last_purchase_cost)
        }
        print(response_data, "resr")
    else:
        response_data = {
            'status': 'false',
            'message': "Not exist",
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def get_sale_items(request):
    pk = request.GET.get('id')
    template_name = 'sales/includes/sale_items.html'
    sale = Sale.objects.get(pk=pk)
    instances = SaleItem.objects.filter(sale__pk=pk)

    if instances:
        context = {
            'sale_items': instances,
        }
        html_content = render_to_string(template_name, context)

        response_data = {
            "status": "true",

            'total_amount': str(sale.total),
            'sub_total_amount': str(sale.subtotal),
            'special_discount': str(sale.discount),

            'template': html_content,
            'customer': str(sale.customer.pk),
            'customer_name': str(sale.customer.name)
        }
    else:
        response_data = {
            "status": "false",
            "message": "Product not found"
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def get_customer(request):
    pk = request.GET.get('id')
    instance = Sale.objects.get(pk=pk, is_deleted=False)

    debit = 0
    credit = 0
    if instance.customer.opening_type == "debit":
        debit = instance.customer.opening_balance
        credit = 0
    if instance.customer.opening_type == "credit":
        credit = instance.customer.opening_balance
        debit = 0

    if instance.customer:
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
def create_sale_return(request):
    if request.method == "POST":
        ModifiedRequest = get_date_updated_request(
            request.POST.copy(), ['time'])
        response_data = {}
        form = SaleReturnForm(ModifiedRequest)

        if form.is_valid():
            message = ""
            is_ok = True
            products = request.POST.getlist('product_pk')
            qtys = request.POST.getlist('returned_qty')
            status = request.POST.getlist('status')
            sale = form.cleaned_data['sale']
            date = form.cleaned_data['time']

            returnable_amount = form.cleaned_data['returnable_amount']

            items = zip(products, qtys, status)
            returned_items = []

            for item in items:
                product_pk = item[0]
                try:
                    product_instance = Product.objects.get(pk=product_pk)

                except:
                    product_instance = None
                    message += "Invalid product selection"
                    is_ok = False
                unit_pk = item[0]

                qty = item[1]
                status = item[2]

                if SaleItem.objects.filter(sale=sale, product=product_instance).exists():
                    sale_item = SaleItem.objects.get(
                        sale=sale, product=product_instance)
                    qty2 = Decimal(qty) + sale_item.return_qty
                    sale_qty = sale_item.quantity - Decimal(qty2)

                    if sale_item.quantity >= Decimal(qty2):
                        pr_ins = {
                            "product": product_instance,
                            "qty": qty,
                            "price": sale_item.amount,
                            "sale_item_quantity": sale_item.quantity,
                            "status": status,
                            "sale_item_return_quantity": sale_qty
                        }
                        returned_items.append(pr_ins)

                    else:
                        print("else")
                        message += "Quantity is greater than sold quantity."
                        is_ok = False
                else:
                    message += "Product with this unit is not in this sale. Please don't edit hidden values."
                    is_ok = False

            error_messages = ""
            title = ""

            if is_ok:
                amount_returned = form.cleaned_data['amount_returned']
                customer = sale.customer
                data = form.save(commit=False)
                data.creator = request.user
                data.updater = request.user
                # data.time = datetime.now()
                data.a_id = get_a_id(SaleReturn, request)
                data.auto_id = get_auto_id(SaleReturn)
                data.sale = sale
                data.amount_returned = amount_returned
                data.customer = customer
                data.save()

                total_tax = 0
                total_taxable_amount = 0
                # Save Sale Return Item
                for f in returned_items:
                    product = f['product']
                    qty = f['qty']
                    status = f['status']
                    # exact_qty = Decimal(get_exact_qty(qty))
                    exact_qty = qty

                    price = f['price']
                    cost = product.cost
                    # discount = f['sale_item_discount']
                    sale_item_quantity = f['sale_item_quantity']
                    # item_discount = ((Decimal(discount)/Decimal(sale_item_quantity))*Decimal(qty))
                    price = Decimal(price)
                    tax_amount1 = (Decimal(price) * Decimal(product.gst)/100)
                    total_tax += tax_amount1*Decimal(qty)
                    total_taxable_amount += price*Decimal(qty)
                    tax_added_price = Decimal(
                        price) + (Decimal(price) * Decimal(product.gst)/100)
                    SaleReturnItem(
                        sale_return=data,
                        product=product,
                        qty=qty,
                        price=tax_added_price,
                        cost=cost,
                        status=status
                    ).save()

                    sale_item = SaleItem.objects.get(
                        sale=sale, product=product)
                    # returnable_amount += (tax_added_price*Decimal(qty))
                    returned_sale_items = SaleItem.objects.filter(sale=sale)

                    for item in returned_sale_items:
                        if item.product == product:
                            quantity = Decimal(qty)
                            saleitem_return_qty = SaleItem.objects.get(
                                sale=sale, product=product)

                            retuned_item_quantity = saleitem_return_qty.return_qty
                            if not retuned_item_quantity:
                                retuned_item_quantity = 0

                            retuned_item_quantity += quantity
                            sale_return_amount = saleitem_return_qty.sub_total

                            SaleItem.objects.filter(sale=sale, product=product).update(
                                return_qty=retuned_item_quantity)

                    if status == 'returnable':
                        exact_qty = Decimal(exact_qty)
                        if sale_item.batch:
                            update_batch_stock(
                                sale_item.batch.pk, qty, "increase")

                data.returnable_amount = returnable_amount
                data.save()
                transaction_mode = ''

                response_data['status'] = 'true'
                response_data['title'] = "Successfully Created"
                response_data['redirect'] = 'true'
                response_data['redirect_url'] = reverse(
                    'sales:sale_return', kwargs={'pk': data.pk})
                response_data['message'] = "Sale Return Successfully Created."
            else:
                response_data['status'] = 'false'
                response_data['title'] = "Error in input values"
                response_data['stable'] = "true"
                response_data['message'] = message
        else:
            response_data['status'] = 'false'
            response_data['stable'] = 'true'
            response_data['title'] = "Form validation error"

            message = ''
            print(form.errors)
            print('form')
            message += str(generate_form_errors(form, formset=False))
            response_data['message'] = str(message)

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = SaleReturnForm()

        context = {
            "form": form,
            "title": "Create Sale Return",
            "redirect": True,

            "is_create_page": True
        }

        return render(request, 'sales/returns/create_sale_return.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def create_sale_return_new(request):
    if request.method == "POST":
        ModifiedRequest = get_date_updated_request(
            request.POST.copy(), ['time'])
        form = SaleReturnForm(ModifiedRequest)

        if form.is_valid():
            message = ""
            is_ok = True
            response_data = {}
            amount_returned = 0

            # Get the return items
            sale_item_pk = request.POST.getlist('sale_item_pk')
            qtys = request.POST.getlist('returned_qty')
            status = request.POST.getlist('status')
            sale = form.cleaned_data['sale']

            # Set using values
            items = zip(sale_item_pk, qtys, status)
            returned_items = []

            for item in items:
                product_pk = item[0]

                try:
                    sale_item_instance = SaleItem.objects.get(pk=product_pk)

                    qty = Decimal(item[1])
                    status = item[2]
                    if sale_item_instance.quantity >= qty and sale_item_instance.return_qty < sale_item_instance.quantity:

                        if sale_item_instance.product_variant:
                            product_variant = sale_item_instance.product_variant
                            pr_ins = {
                                "product": product_variant.product.pk,
                                "product_variant": product_variant.pk,
                                "qty": qty,
                                "price": sale_item_instance.amount,
                                "sale_item_quantity": sale_item_instance.quantity,
                                "status": status,
                                "sale_item_return_quantity": qty,
                                "is_varient": True,
                                "batch": sale_item_instance.batch.pk,
                                "sale_item_instance": sale_item_instance,
                            }
                        # else:
                        #     product = sale_item_instance.product
                        #     pr_ins = {
                        #         "product": product.pk,
                        #         "qty": qty,
                        #         "price": sale_item_instance.amount,
                        #         "sale_item_quantity": sale_item_instance.quantity,
                        #         "status": status,
                        #         "sale_item_return_quantity": qty,
                        #         "is_varient": False,
                        #         "batch": sale_item_instance.batch.pk,
                        #         "sale_item_instance": sale_item_instance,
                        #     }

                        returned_items.append(pr_ins)

                    else:
                        message += "Quantity is greater than sold quantity."
                        is_ok = False

                except:
                    sale_item_instance = None
                    message += "Invalid sale selection"
                    is_ok = False

                # Save Sale Return Item

            if is_ok:
                customer = sale.customer
                data = form.save(commit=False)
                data.creator = request.user
                data.updater = request.user
                data.warehouse = sale.warehouse
                data.a_id = get_a_id(SaleReturn, sale.warehouse)
                data.auto_id = get_auto_id(SaleReturn)
                data.sale = sale
                data.customer = customer
                data.amount_returned = amount_returned
                data.save()

                for f in returned_items:
                    qty = f['qty']
                    status = f['status']
                    price = f['price']
                    sale_item_quantity = f['sale_item_quantity']
                    sale_item_return_quantity = f['sale_item_return_quantity']
                    is_varient = f['is_varient']

                    if is_varient:
                        SaleReturnItem(
                            product_id=f["product"],
                            product_variant_id=f["product_variant"],
                            batch_id=f["batch"],
                            sale_return=data,
                            qty=qty,
                            price=price,
                            cost=0,
                            status=status,
                            sale_item=f['sale_item_instance']
                        ).save()

                    # else:
                    #     SaleReturnItem(
                    #         product_id=f["product"],
                    #         batch_id=f["batch"],
                    #         sale_return=data,
                    #         qty=qty,
                    #         price=price,
                    #         cost=0,
                    #         status=status,
                    #         sale_item=f['sale_item_instance']
                    #     ).save()

                    if status == 'returnable':
                        update_batch_stock(
                            f['batch'], sale_item_return_quantity, "increase")

                    f['sale_item_instance'].return_qty += qty
                    f['sale_item_instance'].save()
                    amount_returned += price * sale_item_return_quantity

                data.amount_returned = amount_returned
                data.save()

                response_data['status'] = 'true'
                response_data['title'] = "Successfully Created"
                response_data['redirect'] = 'true'
                response_data['redirect_url'] = reverse(
                    'sales:sale_return', kwargs={'pk': data.pk})
                response_data['message'] = "Sale Return Successfully Created."
            else:
                response_data = {
                    'status': 'false',
                    'title': "Error in input values",
                    'stable': "true",
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
            message += str(generate_form_errors(form, formset=False))
            response_data['message'] = str(message)

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = SaleReturnForm()

        context = {
            "form": form,
            "title": "Create Sale Return",
            "redirect": True,

            "is_create_page": True
        }

        return render(request, 'sales/returns/create_sale_return.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def edit_sale_return(request, pk):
    instance = get_object_or_404(
        SaleReturn.objects.filter(pk=pk, is_deleted=False))
    sale_return_items = SaleReturnItem.objects.filter(sale_return_id=pk)

    if request.method == "POST":
        response_data = {}
        amount_returned = 0
        ModifiedRequest = get_date_updated_request(
            request.POST.copy(), ['time'])
        form = SaleReturnForm(ModifiedRequest, instance=instance)

        if form.is_valid():
            message = ""
            is_ok = True

            # Get the return items
            sale_item_pk = request.POST.getlist('sale_item_pk')
            qtys = request.POST.getlist('returned_qty')
            status = request.POST.getlist('status')
            sale = form.cleaned_data['sale']

            # Set using values
            items = zip(sale_item_pk, qtys, status)
            returned_items = []

            for item in items:
                product_pk = item[0]

                try:
                    sale_item_instance = SaleItem.objects.get(pk=product_pk)
                    qty = Decimal(item[1])
                    status = item[2]

                    if sale_item_instance.quantity >= qty and sale_item_instance.return_qty < sale_item_instance.quantity:

                        if sale_item_instance.product_variant:
                            product_variant = sale_item_instance.product_variant
                            pr_ins = {
                                "product": sale_item_instance.product.pk,
                                "product_variant": product_variant.pk,
                                "qty": qty,
                                "price": sale_item_instance.amount,
                                "sale_item_quantity": sale_item_instance.quantity,
                                "status": status,
                                "sale_item_return_quantity": qty,
                                "is_varient": True,
                                "batch": sale_item_instance.batch.pk,
                                "sale_item_instance": sale_item_instance,
                            }

                        else:
                            product = sale_item_instance.product
                            pr_ins = {
                                "product": product.pk,
                                "qty": qty,
                                "price": sale_item_instance.amount,
                                "sale_item_quantity": sale_item_instance.quantity,
                                "status": status,
                                "sale_item_return_quantity": qty,
                                "is_varient": False,
                                "batch": sale_item_instance.batch.pk,
                                "sale_item_instance": sale_item_instance,
                            }

                        returned_items.append(pr_ins)

                    else:
                        message += "Quantity is greater than sold quantity."
                        is_ok = False

                except:
                    sale_item_instance = None
                    message += "Invalid sale selection"
                    is_ok = False

                # Save Sale Return Item

            if is_ok:
                customer = sale.customer
                data = form.save(commit=False)
                data.sale = sale
                data.updater = request.user
                data.customer = customer
                data.is_updated = True
                data.amount_returned = 0
                data.save()

                sale_objs = SaleReturnItem.objects.filter(sale_return=instance)
                for sale_obj in sale_objs:
                    update_batch_stock(
                        sale_obj.sale_item.batch.pk, sale_obj.qty, "decrease")
                    sale_obj.sale_item.return_qty -= qty
                    sale_obj.sale_item.save()
                    sale_obj.delete()

                for f in returned_items:
                    qty = f['qty']
                    status = f['status']
                    price = f['price']
                    sale_item_quantity = f['sale_item_quantity']
                    sale_item_return_quantity = f['sale_item_return_quantity']
                    is_varient = f['is_varient']

                    amount_returned += price * sale_item_return_quantity

                    if is_varient:
                        SaleReturnItem.objects.create(
                            product_id=f["product"],
                            batch_id=f["batch"],
                            product_variant_id=f["product_variant"],
                            sale_return=data,
                            qty=qty,
                            price=price,
                            cost=0,
                            status=status,
                            sale_item=f['sale_item_instance']
                        )

                        if status == 'returnable':
                            update_batch_stock(
                                f['batch'], sale_item_return_quantity, "increase")
                    else:
                        SaleReturnItem.objects.create(
                            product_id=f["product"],
                            batch_id=f["batch"],
                            sale_return=data,
                            qty=qty,
                            price=price,
                            cost=0,
                            status=status,
                            sale_item=f['sale_item_instance']
                        )

                        if status == 'returnable':
                            update_batch_stock(
                                f['batch'], sale_item_return_quantity, "increase")

                data.amount_returned = amount_returned
                data.save()

                response_data['status'] = 'true'
                response_data['title'] = "Successfully Updated"
                response_data['redirect'] = 'true'
                # response_data['redirect_url'] = reverse('sales:sale_return', kwargs={'pk': data.pk})
                response_data['redirect_url'] = reverse('sales:sale_returns'),
                response_data['message'] = "Sale Return Successfully Updated."
            else:
                response_data['status'] = 'false'
                response_data['title'] = "Error in input values"
                response_data['stable'] = "true"
                response_data['message'] = message
        else:
            response_data['status'] = 'false'
            response_data['stable'] = 'true'
            response_data['title'] = "Form validation error"

            message = ''
            print(form.errors)
            print('form')
            message += str(generate_form_errors(form, formset=False))
            response_data['message'] = str(message)

        return HttpResponse(json.dumps(response_data), content_type='application/javascript')

    else:
        form = SaleReturnForm(instance=instance)

        context = {
            "form": form,
            "title": "Edit Sale Return",
            'return_items': sale_return_items,
            "redirect": True,

            "is_edit": True
        }

        return render(request, 'sales/returns/edit_sale_return.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def sale_returns(request):
    filter_data = {}
    query = request.GET.get('q')
    on_date = request.GET.get('on_date')
    to_date = request.GET.get('to_date')
    from_date = request.GET.get('from_date')

    instances = SaleReturn.objects.all().order_by('-auto_id')

    if query:
        filter_data['query'] = query
        instances = instances.filter(
            Q(auto_id__iexact=query) |
            Q(sale__auto_id__iexact=query) |
            Q(customer__name__icontains=query) |
            Q(customer__address__icontains=query)
        )

    if from_date and to_date:
        f_date = datetime.datetime.strptime(from_date, '%d/%m/%Y').date()
        t_date = datetime.datetime.strptime(to_date, '%d/%m/%Y').date()
        instances = instances.filter(time__date__range=[f_date, t_date])

        filter_data['from_date'] = from_date
        filter_data['to_date'] = to_date

    if on_date:
        o_date = datetime.datetime.strptime(on_date, '%d/%m/%Y').date()
        instances = instances.filter(time__date=o_date)
        filter_data['on_date'] = on_date

    context = {
        "title": "Sale Returns",
        "filter_data": filter_data,
        "instances": instances
    }

    return render(request, 'sales/returns/sale_returns.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def sale_return(request, pk):
    instance = get_object_or_404(SaleReturn.objects.filter(pk=pk))
    sale_items = SaleReturnItem.objects.filter(sale_return=instance)

    context = {
        "title": "Sale Return: " + str(instance.auto_id),
        "instance": instance,
        "sale_items": sale_items
    }

    return render(request, 'sales/returns/sale_return.html', context)


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def delete_sale_return(request, pk):
    reason = request.GET.get('reason')
    instance = SaleReturn.objects.get(pk=pk)
    instance.deleted_reason = reason
    instance.is_deleted = True
    instance.save()

    return_items = SaleReturnItem.objects.filter(sale_return=instance)

    for p in return_items:
        quantity = p.qty
        p.sale_item.return_qty -= quantity
        p.sale_item.save()
        update_batch_stock(p.sale_item.batch.pk, quantity, "decrease")

    response_data = {
        'status': 'true',
        'title': "Successfully Cancelled",
        'redirect': 'true',
        'redirect_url': reverse('sales:sale_returns'),
        'message': "Sale Return Successfully Cancelled.",
    }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def print_sale_return(request, pk):
    instance = get_object_or_404(SaleReturn.objects.filter(pk=pk))
    # sale_category = instance.sale_category

    sale_return_items = SaleReturnItem.objects.filter(sale_return=instance)
    total_subtotal = 0
    grant_total = 0
    total_discount = 0

    for return_item in sale_return_items:
        # gst_amount = return_item.gst_amount
        subtotal = return_item.t()
        # gst_added_total = return_item.total
        # discount = return_item.discount
        grant_total += subtotal
        total_subtotal += subtotal

    grant_total_value = grant_total

    context = {
        "title": "Sale Return ",
        "instance": instance,
        "sale_items": sale_return_items,
        "total_subtotal": total_subtotal,
        "grant_total_value": grant_total_value,
    }

    return render(request, 'invoice/print_return.html', context)


@login_required
@ajax_required
@role_required(['superadmin', 'warehouse_manager'])
def get_sale_returns(request):
    pk = request.GET.get('customer_id')
    if pk:
        customer = get_object_or_404(Customer, pk=pk)
        instances = SaleReturn.objects.filter(customer_id=pk, is_deleted=False)

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
                "message": "Sale returns Not found"
            }

    else:
        response_data = {
            "status": "false",
            "message": "customer data unavailable"
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@ajax_required
@role_required(['superadmin', 'warehouse_manager'])
def get_sale_return_amount(request):
    pk = request.GET.get('id')

    if pk:
        if SaleReturn.objects.filter(pk=pk, is_deleted=False):
            instance = SaleReturn.objects.get(pk=pk, is_deleted=False)

            response_data = {
                "status": "true",

                'total_amount': str(instance.sale.total),
                'sub_total_amount': str(instance.sale.subtotal),
                'special_discount': str(instance.sale.discount),

                "amount": str(instance.amount_returned)
            }

        else:
            response_data = {
                "status": "false",
                "message": "Sale return Not found"
            }

    else:
        response_data = {
            "status": "false",
            "message": "Key unavailable"
        }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def get_return_customer(request):
    pk = request.GET.get('id')
    instance = SaleReturn.objects.get(pk=pk)

    response_data = {
        "status": "true",
        'customer': str(instance.customer.pk),
        'customer_name': str(instance.customer.name)
    }
    # else:
    #     response_data = {
    #         "status": "false",
    #         "message": "Product not found"
    #     }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')


@login_required
@role_required(['superadmin', 'warehouse_manager'])
def get_prifix_sale_id(request):
    pk = request.GET.get('id')
    sale_type = request.GET.get('sale_type')
    # for generating order id
    prefix = InvoicePrefix.objects.get(pk=pk,is_deleted=False)
    if Sale.objects.filter(sale_prifix=prefix,is_deleted=False,sale_type=sale_type).exists():
        sale_no = Sale.objects.filter(sale_prifix=prefix,is_deleted=False,sale_type=sale_type).aggregate(Max('sale_no'))['sale_no__max']
    else:
        sale_no = 1

    if sale_type == "b2b":
        sale_id = f"{prefix.whole_sale}{str(sale_no).zfill(6)}"
    elif sale_type == "b2c":
        sale_id = f"{prefix.retail_sale}{str(sale_no).zfill(6)}"

    response_data = {
        "status": "true",
        'sale_id': str(sale_id),
    }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')

@login_required
@role_required(['superadmin', 'warehouse_manager'])
def get_prifix_sale_type(request):
    sale_type = request.GET.get('sale_type')
    # for generating order id
    instance_prefix = InvoicePrefix.objects.filter(is_deleted=False, financial_year__is_active=True)
    data = []

    if sale_type == "b2b":
        for prif in instance_prefix:
            dic = {
                'id': str(prif.pk),
                'title': prif.whole_sale,
            }
            data.append(dic)

    elif sale_type == "b2c":
        for prif in instance_prefix:
            dic = {
                'id': str(prif.pk),
                'title': prif.retail_sale,
            }
            data.append(dic)

    response_data = {
        "status": "true",
        'data': data,
    }

    return HttpResponse(json.dumps(response_data), content_type='application/javascript')



@login_required
@role_required(['superadmin', 'staff_user'])
def print_sale(request, pk):
    instance = get_object_or_404(Sale.objects.filter(pk=pk))
    state = 'instance.customer.state'
    sale_category = instance.sale_category
    invoice_design = None
    if InvoiceDesign.objects.filter(is_deleted=False,is_active=True):
        invoice_design = InvoiceDesign.objects.filter(is_deleted=False,is_active=True).first()

    sale_items = SaleItem.objects.filter(sale=instance)
    total_subtotal = 0
    grant_total = 0
    total_cgst = 0
    total_sgst = 0
    total_igst = 0
    total_discount = 0

    for sale_item in sale_items:
        gst_amount = sale_item.gst_amount
        subtotal = sale_item.sub_total
        gst_added_total = sale_item.total
        discount = sale_item.discount
        grant_total += gst_added_total
        total_discount += discount
        total_subtotal += subtotal

        if instance.add_gst:
            if sale_category == "intra_state":
                sgst = gst_amount/2
                cgst = gst_amount/2
                sgst_rate = sale_item.gst/2
                cgst_rate = sale_item.gst/2
                igst = 0
                igst_rate = 0

                total_cgst += cgst
                total_sgst += sgst
            else:
                igst = gst_amount
                igst_rate = sale_item.gst
                sgst = 0
                cgst = 0
                sgst_rate = 0
                cgst_rate = 0

                total_igst += igst
        else:
            total_cgst = 0
            total_sgst = 0
            total_igst = 0

    grant_total_value = grant_total

    # get custoemr's current balance
    head = AccountHead.objects.filter(name='Sundry Debtor', is_deleted=False).last()
    date = datetime.datetime.now().date()

    # data = get_ledger_data(head, date, date, str(instance.customer.pk), 'current balance')
    # balance = data['closing_balance']
    balance = 0
    # if balance > 0:
    #     balance_type = 'Debit'
    # else:
    #     balance_type = 'Credit'
    #     balance = abs(balance)

    context = {
        "title": "Quotation ",
        "instance": instance,
        "sale_items": sale_items,
        "sale_category": sale_category,
        "grant_total_value": grant_total_value,
        "total_subtotal": total_subtotal,
        "total_cgst": total_cgst,
        "total_sgst": total_sgst,
        "total_igst": total_igst,
        # "balance_type": balance_type,
        "balance": balance,
        "invoice_design": invoice_design,
    }

    return render(request, 'invoice/print_sale.html', context)



@login_required
@role_required(['superadmin', 'staff_user'])
def print_invoice(request, pk):
    instance = get_object_or_404(Sale.objects.filter(pk=pk))
    state = 'instance.customer.state'
    sale_category = instance.sale_category
    invoice_design = None
    if InvoiceDesign.objects.filter(is_deleted=False,is_active=True):
        invoice_design = InvoiceDesign.objects.filter(is_deleted=False,is_active=True).first()

    sale_items = SaleItem.objects.filter(sale=instance)
    total_subtotal = 0
    grant_total = 0
    total_cgst = 0
    total_sgst = 0
    total_igst = 0
    total_discount = 0

    for sale_item in sale_items:
        gst_amount = sale_item.gst_amount
        subtotal = sale_item.sub_total
        gst_added_total = sale_item.total
        discount = sale_item.discount
        grant_total += gst_added_total
        total_discount += discount
        total_subtotal += subtotal

        if instance.add_gst:
            if sale_category == "intra_state":
                sgst = gst_amount/2
                cgst = gst_amount/2
                sgst_rate = sale_item.gst/2
                cgst_rate = sale_item.gst/2
                igst = 0
                igst_rate = 0

                total_cgst += cgst
                total_sgst += sgst
            else:
                igst = gst_amount
                igst_rate = sale_item.gst
                sgst = 0
                cgst = 0
                sgst_rate = 0
                cgst_rate = 0

                total_igst += igst
        else:
            total_cgst = 0
            total_sgst = 0
            total_igst = 0

    grant_total_value = grant_total

    # get custoemr's current balance
    head = AccountHead.objects.filter(name='Sundry Debtor', is_deleted=False).last()
    date = datetime.datetime.now().date()

    # data = get_ledger_data(head, date, date, str(instance.customer.pk), 'current balance')
    # balance = data['closing_balance']
    balance = 0
    # if balance > 0:
    #     balance_type = 'Debit'
    # else:
    #     balance_type = 'Credit'
    #     balance = abs(balance)

    context = {
        "title": "Quotation ",
        "instance": instance,
        "sale_items": sale_items,
        "sale_category": sale_category,
        "grant_total_value": grant_total_value,
        "total_subtotal": total_subtotal,
        "total_cgst": total_cgst,
        "total_sgst": total_sgst,
        "total_igst": total_igst,
        # "balance_type": balance_type,
        "balance": balance,
        "invoice_design": invoice_design,
    }

    return render(request, 'invoice/print_invoice.html', context)

@login_required
def sale_export(request):
    purchase_filter = SaleFilter(request)
    instances = purchase_filter.get_filtered_results()
    print("Instances===>>>",instances)

    export_to_excel_utils = ExportToExcelUtils(instances, SaleExportSerializer, request, "sales_export")
    returned_file_url = export_to_excel_utils.export_to_excel()
    return HttpResponseRedirect(returned_file_url)