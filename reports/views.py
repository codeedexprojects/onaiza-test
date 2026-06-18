import datetime
from django.shortcuts import render
from django.http.response import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from main.decorators import role_required
from django.db.models import Sum, Count, Q, Max, F, ExpressionWrapper, FloatField
from sales.models import Sale
from warehouses.models import Warehouse
from customers.models import Customer
from staffs.models import Staff
from vendors.models import Vendor
from suppliers.models import Supplier
from purchases.models import *
from general.models import Batch
from products.models import *
from finance.models import *
from reports.functions import *
from sales.models import *
from orders.models import Orders


@login_required
def sales_report(request):
    filter_params = {}
    is_admin = None
    if request.user.is_superuser:
        is_admin = True

    warehouse = request.GET.get('warehouse')
    to_date = request.GET.get('to_date')
    customer = request.GET.get('customer')
    sale_type = request.GET.get('sale_type')
    from_date = request.GET.get('from_date')
    user_role = request.GET.get('user_role')

    customers = Customer.objects.filter(is_deleted=False)
    instances = Sale.objects.filter().order_by('-a_id')

    url = '?'

    if user_role:
        if 'warehouse_manager' in user_role:
            staff_instance = Staff.objects.get(user=request.user)
            is_admin = False
            instances = Sale.objects.filter(warehouse=staff_instance.warehouse).order_by('-a_id')

    if from_date and to_date:
        url += f'to_date={to_date}&'
        url += f'from_date={from_date}&'

        filter_params = {
            "to_date": to_date,
            "from_date": from_date,
        }
        from_date = datetime.datetime.strptime(from_date, '%d/%m/%Y').date()
        to_date = datetime.datetime.strptime(to_date, '%d/%m/%Y').date()

        instances = instances.filter(sale_date__date__range=[from_date, to_date])

    if warehouse:
        url += f'warehouse={warehouse}&'
        instances = instances.filter(warehouse__pk=warehouse)
        filter_params["warehouse"] = warehouse

    if customer:
        url += f'customer={customer}&'
        instances = instances.filter(customer__pk=customer)
        filter_params["customer"] = customer

    if sale_type:
        url += f'sale_type={sale_type}&'
        instances = instances.filter(sale_type=sale_type)
        filter_params["sale_type"] = sale_type

    warehouse_instances = Warehouse.objects.filter(is_deleted=False)

    instances = instances.annotate(total_tax=F('sgst') + F('cgst') + F('igst'))

    totals = {
        'sale_taxable_amount': instances.aggregate(Sum('sale_taxable_amount'))['sale_taxable_amount__sum'],
        'purchase_taxable_amount': instances.aggregate(Sum('purchase_taxable_amount'))['purchase_taxable_amount__sum'],
        'gst_amount_total': instances.aggregate(Sum('total_tax'))['total_tax__sum'],
        'discount_total': instances.aggregate(Sum('discount'))['discount__sum'],
        'all_total': instances.aggregate(Sum('total'))['total__sum'],
        'paid_total': instances.aggregate(Sum('paid'))['paid__sum'],
    }

    context = {
        "title": "Sales Report",
        "is_admin": is_admin,
        "instances": instances,
        "customers": customers,
        "filter_params": filter_params,
        "warehouse_instances": warehouse_instances,
        "totals": totals,
    }

    return render(request, 'reports/sales/sale_reports.html', context)


@login_required
def print_sales_report(request):
    query = request.GET.get('q')
    on_date = request.GET.get('on_date')
    to_date = request.GET.get('to_date')
    from_date = request.GET.get('from_date')
    customer = request.GET.get('customer')
    payment_method = request.GET.get('payment_method')
    title = "Sales Report"
    filter_data = {}

    instances = Sale.objects.filter(is_deleted=False).order_by('-a_id')

    if query:
        instances = instances.filter(
            Q(total=query) |
            Q(sale_id__istartswith=query) |
            Q(tracking_id__istartswith=query) |
            Q(customer__name__icontains=query) |
            Q(customer__phone__icontains=query) |
            Q(customer__email__icontains=query) |
            Q(customer__address__icontains=query)
        )
        filter_data['query'] = query

    if from_date and to_date:
        f_date = datetime.datetime.strptime(from_date, '%d/%m/%Y').date()
        t_date = datetime.datetime.strptime(to_date, '%d/%m/%Y').date()
        instances = instances.filter(sale_date__date__range=[f_date, t_date])
        title = 'Total Number of Sales (from %s to %s)' % (str(f_date), str(t_date))

        filter_data['from_date'] = from_date
        filter_data['to_date'] = to_date

    if on_date:
        o_date = datetime.datetime.strptime(on_date, '%d/%m/%Y').date()
        instances = instances.filter(sale_date__date=o_date)
        title = 'Total Number of Sales (On %s)' % (str(o_date))
        filter_data['on_date'] = on_date

    if customer:
        instances = instances.filter(customer_id=customer)
        filter_data['customer'] = customer

    if payment_method:
        instances = instances.filter(payment_method=payment_method)
        filter_data['payment_method'] = payment_method

    context = {
        "data": filter_data,
        "title": title,
        "instances": instances,

        "is_need_popup_box": True,
        "is_need_grid_system": True,
        "is_need_wave_effect": True,
        "is_need_select_picker": True,
        "is_need_chosen_select": True,
        "is_need_bootstrap_growl": True,
        "is_need_datetime_picker": True,
        "is_need_custom_scroll_bar": True,
    }

    return render(request, 'reports/sales/sale_report_print.html', context)


@login_required
def purchase_report(request):
    filter_params = {}
    is_admin = None
    if request.user.is_superuser:
        is_admin = True

    warehouse = request.GET.get('warehouse')
    to_date = request.GET.get('to_date')
    from_date = request.GET.get('from_date')
    user_role = request.GET.get('user_role')
    supplier = request.GET.get('supplier')

    suppliers_instance = Supplier.objects.filter(is_deleted=False)
    instances = Purchase.objects.filter(is_deleted=False).order_by('-date')

    url = '?'

    if user_role:
        if 'warehouse_manager' in user_role:
            staff_instance = Staff.objects.get(user=request.user)
            is_admin = False
            instances = Purchase.objects.filter(warehouse=staff_instance.warehouse).order_by('-date')

    if from_date and to_date:
        url += f'to_date={to_date}&'
        url += f'from_date={from_date}&'

        filter_params = {
            "to_date": to_date,
            "from_date": from_date,
        }
        from_date = datetime.datetime.strptime(from_date, '%d/%m/%Y').date()
        to_date = datetime.datetime.strptime(to_date, '%d/%m/%Y').date()

        instances = instances.filter(date__date__range=[from_date, to_date])

    if warehouse:
        url += f'warehouse={warehouse}&'
        instances = instances.filter(warehouse__pk=warehouse)
        filter_params["warehouse"] = warehouse

    if supplier:
        url += f'supplier={supplier}&'
        instances = instances.filter(supplier__pk=supplier)
        filter_params["supplier"] = supplier

    warehouse_instances = Warehouse.objects.filter(is_deleted=False)

    instances = instances.annotate(
        discountamount=(F('product_total') * F('discount')) / 100
    )

    try:
        totals = {
            'product_total': round(instances.aggregate(Sum('product_total'))['product_total__sum'], 3),
            'discount_total': round(instances.aggregate(Sum('discountamount'))['discountamount__sum'], 2),
            'total': round(instances.aggregate(Sum('subtotal'))['subtotal__sum'], 3),
            'paid_total': round(instances.aggregate(Sum('paid'))['paid__sum'], 3),
            'balance_total': round(instances.aggregate(Sum('balance'))['balance__sum'], 3),
        }
    except:
        totals = {
            'product_total': 0,
            'discount_total': 0,
            'total': 0,
            'paid_total': 0,
            'balance_total': 0,
        }

    context = {
        "filter_params": filter_params,
        "title": "Purchase Report",
        "suppliers": suppliers_instance,
        "instances": instances,
        "totals": totals,
        "is_admin": is_admin,
        "warehouse_instances": warehouse_instances,
    }

    return render(request, 'reports/purchases/purchases_reports.html', context)


@login_required
def print_purchase_report(request):
    to_date = request.GET.get('to_date')
    from_date = request.GET.get('from_date')
    supplier = request.GET.get('supplier')
    warehouse = request.GET.get('warehouse')
    filter_params = {}

    instances = Purchase.objects.filter(is_deleted=False).order_by('-date')
    if not request.user.is_superuser:
        staff_instance = Staff.objects.get(user=request.user)
        instances = Purchase.objects.filter(warehouse=staff_instance.warehouse, is_deleted=False).order_by('-date')

    if from_date and to_date:
        from_date = datetime.datetime.strptime(from_date, '%d/%m/%Y').date()
        to_date = datetime.datetime.strptime(to_date, '%d/%m/%Y').date()
        instances = instances.filter(date__date__range=[from_date, to_date])

    if supplier:
        instances = instances.filter(supplier_pk=supplier)

    if warehouse:
        instances = instances.filter(warehouse_pk=warehouse)

    instances = instances.annotate(
        discountamount=(F('product_total') * F('discount')) / 100
    )

    totals = {
        'product_total': round(instances.aggregate(Sum('product_total'))['product_total__sum'], 3),
        'discount_total': round(instances.aggregate(Sum('discountamount'))['discountamount__sum'], 2),
        'total': round(instances.aggregate(Sum('subtotal'))['subtotal__sum'], 3),
        'paid_total': round(instances.aggregate(Sum('paid'))['paid__sum'], 3),
        'balance_total': round(instances.aggregate(Sum('balance'))['balance__sum'], 3),
    }

    context = {
        "filter_params": filter_params,
        "title": "Purchase Report",
        "instances": instances,
        "totals": totals,
    }
    return render(request, 'reports/purchases/purchases_report_print.html', context)


@login_required
def batch_stock_report(request):
    filter_params = {}
    title = "Batch Stock Report"
    is_admin = True

    instances = Batch.objects.filter(is_deleted=False, stock__gt=0).order_by('product__name', 'product_variant__title',
                                                                             'batch_number')

    query = request.GET.get("q")
    brand = request.GET.get("brand")
    product = request.GET.get("product")
    category = request.GET.get("category")
    sub_category = request.GET.get("sub_category")
    warehouse = request.GET.get("warehouse")
    user_role = request.GET.get('user_role')

    if query:
        instances = instances.filter(
            Q(batch_number__istartswith=query) |
            Q(product_variant__title__icontains=query) |
            Q(product__category__name__icontains=query) |
            Q(product__subcategory__name__icontains=query) |
            Q(product__brand__name__icontains=query)
        )

        title = "Batches - %s" % query
        filter_params['query'] = query

    if brand:
        instances = instances.filter(product__brand_id=brand)
        filter_params['brand'] = brand

    if category:
        instances = instances.filter(product__category_id=category)
        filter_params['category'] = category

    if sub_category:
        instances = instances.filter(product__subcategory_id=sub_category)
        filter_params['sub_category'] = sub_category

    if product:
        instances = instances.filter(product_id=product)
        filter_params['product'] = product

    if warehouse:
        instances = instances.filter(warehouse_id=warehouse)
        filter_params['warehouse'] = warehouse

    if user_role:
        if 'warehouse_manager' in user_role:
            staff_instance = Staff.objects.get(user=request.user)
            is_admin = False
            instances = Batch.objects.filter(is_deleted=False, stock__gt=0,
                                             warehouse=staff_instance.warehouse).order_by('product__name',
                                                                                          'product_variant__title',
                                                                                          'batch_number')

    brands = Brand.objects.filter(is_deleted=False)
    products = Product.objects.filter(is_deleted=False)
    categories = Category.objects.filter(is_deleted=False)
    warehouse = Warehouse.objects.filter(is_deleted=False)

    instances = instances.annotate(
        total_cost=ExpressionWrapper(F('cost') * F('stock'), output_field=FloatField()),
        total_mrp=ExpressionWrapper(F('mrp') * F('stock'), output_field=FloatField()),
        # total_price=ExpressionWrapper(F('price') * F('stock'), output_field=FloatField()),
    )

    totals = {
        'total_cost': instances.aggregate(Sum('total_cost'))['total_cost__sum'],
        'total_mrp': instances.aggregate(Sum('total_mrp'))['total_mrp__sum'],
        # 'total_price': instances.aggregate(Sum('total_price'))['total_price__sum'],
    }

    context = {
        'title': title,
        'brands': brands,
        "products": products,
        'instances': instances,
        'categories': categories,
        "warehouse": warehouse,
        "filter_params": filter_params,
        "totals": totals,
        "is_admin": is_admin,
    }

    return render(request, 'reports/stock/stock_report.html', context)


@login_required
def daily_report(request):
    instances = {}
    f_date = request.GET.get('from_date')
    t_date = request.GET.get('to_date')

    if not f_date:
        f_date = datetime.datetime.strftime(datetime.datetime.now(), '%d/%m/%Y')
    if not t_date:
        t_date = datetime.datetime.strftime(datetime.datetime.now(), '%d/%m/%Y')

    from_date = datetime.datetime.strptime(f_date, '%d/%m/%Y')
    to_date = datetime.datetime.strptime(t_date, '%d/%m/%Y')

    title = f'Daily Report {f_date} - {t_date}'

    bank_heads = AccountHead.objects.filter(bank_account__isnull=False, is_deleted=False)
    bank_opening_balance = 0
    bank_closing_balance = 0

    for head in bank_heads:
        ledger_data = get_ledger_data(head, from_date, to_date, None, 'current balance')

        opening_balance = ledger_data['opening_balance']
        bank_opening_balance += opening_balance
        closing_balance = ledger_data['closing_balance']
        bank_closing_balance += closing_balance

    cash_opening_balance = 0
    cash_closing_balance = 0

    cash_head = AccountHead.objects.get(name='Cash A/C',  is_deleted=False)
    ledger_data = get_ledger_data(cash_head, from_date, to_date, None, 'current balance')

    opening_balance = ledger_data['opening_balance']
    cash_opening_balance += opening_balance
    closing_balance = ledger_data['closing_balance']
    cash_closing_balance += closing_balance

    total_opening_balance = cash_opening_balance + bank_opening_balance
    total_closing_balance = cash_closing_balance + bank_closing_balance

    instances['opening'] = {
        'cash': cash_opening_balance,
        'bank': bank_opening_balance,
        'total': total_opening_balance,
        'credit': 0,
    }

    instances['closing'] = {
        'cash': cash_closing_balance,
        'bank': bank_closing_balance,
        'total': total_closing_balance,
        'credit': 0,
    }

    # sales calculations
    cash_sales = 0
    bank_sales = 0
    total_sales = 0
    credit_sales = 0

    sale_receipts = ReceiptVoucher.objects.filter(is_deleted=False, is_system_generated=True,
                                                  voucher_date__date__range=[from_date, to_date],
                                                  account_head__name='Sales A/C')
    sales = Sale.objects.filter(is_deleted=False, sale_date__date__range=[from_date, to_date]).annotate(
        balance=F('total') - F('paid'))

    # # first method by using payment method only balances are ignored
    # if sales.filter(payment_method='cash').exists():
    #     cash_sales = sales.filter(payment_method='cash').aggregate(Sum('total'))['total__sum']
    # if sales.filter(payment_method='credit').exists():
    #     credit_sales = sales.filter(payment_method='credit').aggregate(Sum('total'))['total__sum']
    # if sales.filter(payment_method__in=['cheque', 'draft', 'bank transfer']).exists():
    #     bank_sales = sales.filter(payment_method__in=['cheque', 'draft', 'bank transfer']).aggregate(Sum('total'))['total__sum']

    # second method by using vouchers total amount is not considered except in credit sales
    if sale_receipts.filter(transfer_type=10).exists():
        cash_sales = sale_receipts.filter(transfer_type=10).aggregate(Sum('amount'))['amount__sum']
    if sale_receipts.filter(transfer_type__in=[15, 20, 25]).exists():
        bank_sales = sale_receipts.filter(transfer_type__in=[15, 20, 25]).aggregate(Sum('amount'))['amount__sum']
    if sales.filter(balance__gt=0).exists():
        credit_sales = sales.filter(balance__gt=0).aggregate(Sum('balance'))['balance__sum']

    total_sales = cash_sales + bank_sales + credit_sales

    instances['offline'] = {
        'cash': cash_sales,
        'bank': bank_sales,
        'total': total_sales,
        'credit': credit_sales,
    }

    # orders calculations
    cash_orders = 0
    bank_orders = 0
    total_orders = 0
    credit_orders = 0

    orders_receipts = ReceiptVoucher.objects.filter(is_deleted=False, is_system_generated=True,
                                                    voucher_date__date__range=[from_date, to_date],
                                                    account_head__name='Online Sales')
    orders = Orders.objects.filter(is_deleted=False, date_added__date__range=[from_date, to_date])

    instances['online'] = {
        'cash': cash_orders,
        'bank': bank_orders,
        'total': total_orders,
        'credit': credit_orders,
    }

    # purchase calculations
    cash_purchases = 0
    bank_purchases = 0
    total_purchases = 0
    credit_purchases = 0

    purchase_payments = PaymentVoucher.objects.filter(is_deleted=False, is_system_generated=True,
                                                      voucher_date__date__range=[from_date, to_date],
                                                      account_head__name='Purchases')
    purchases = Purchase.objects.filter(is_deleted=False, date__date__range=[from_date, to_date])

    if purchase_payments.filter(transfer_type=10).exists():
        cash_purchases = purchase_payments.filter(transfer_type=10).aggregate(Sum('amount'))['amount__sum']
    if purchase_payments.filter(transfer_type__in=[15, 20, 25]).exists():
        bank_purchases = purchase_payments.filter(transfer_type__in=[15, 20, 25]).aggregate(Sum('amount'))[
            'amount__sum']
    if purchases.filter(balance__gt=0).exists():
        credit_purchases = purchases.filter(balance__gt=0).aggregate(Sum('balance'))['balance__sum']

    total_purchases = cash_purchases + bank_purchases + credit_purchases

    instances['purchases'] = {
        'cash': cash_purchases,
        'bank': bank_purchases,
        'total': total_purchases,
        'credit': credit_purchases,
    }

    # withdrawal voucher calculations
    cash_payments = 0
    bank_payments = 0
    total_payments = 0
    credit_payments = 0

    withdrawals = JournalVoucherItem.objects.filter(journal__is_deleted=False,
                                                    journal__voucher_date__date__range=[from_date, to_date],
                                                    amount_type=10)  # credit is withdraw

    if withdrawals.filter(account_head__name='Cash A/C').exists():
        cash_payments = withdrawals.filter(account_head__name='Cash A/C').aggregate(Sum('amount'))['amount__sum']
    if withdrawals.filter(account_head__bank_account__isnull=False).exists():
        bank_payments = withdrawals.filter(account_head__bank_account__isnull=False).aggregate(Sum('amount'))['amount__sum']

    total_payments = cash_payments + bank_payments

    instances['withdraw'] = {
        'cash': cash_payments,
        'bank': bank_payments,
        'total': total_payments,
        'credit': credit_payments,
    }

    # deposit voucher calculations
    cash_payments = 0
    bank_payments = 0
    total_payments = 0
    credit_payments = 0

    deposits = JournalVoucherItem.objects.filter(journal__is_deleted=False,
                                                 journal__voucher_date__date__range=[from_date, to_date],
                                                 amount_type=20)  # credit is deposit

    if deposits.filter(account_head__name='Cash A/C').exists():
        cash_payments = deposits.filter(account_head__name='Cash A/C').aggregate(Sum('amount'))['amount__sum']
    if deposits.filter(account_head__bank_account__isnull=False).exists():
        bank_payments = deposits.filter(account_head__bank_account__isnull=False).aggregate(Sum('amount'))['amount__sum']

    total_payments = cash_payments + bank_payments

    instances['deposit'] = {
        'cash': cash_payments,
        'bank': bank_payments,
        'total': total_payments,
        'credit': credit_payments,
    }

    # Payment voucher calculations
    cash_payments = 0
    bank_payments = 0
    total_payments = 0
    credit_payments = 0

    payment_vouchers = PaymentVoucher.objects.filter(is_deleted=False, is_system_generated=False,
                                                     voucher_date__date__range=[from_date, to_date])

    if payment_vouchers.filter(transfer_type=10).exists():
        cash_payments = payment_vouchers.filter(transfer_type=10).aggregate(Sum('amount'))['amount__sum']
    if payment_vouchers.filter(transfer_type__in=[15, 20, 25]).exists():
        bank_payments = payment_vouchers.filter(transfer_type__in=[15, 20, 25]).aggregate(Sum('amount'))['amount__sum']

    total_payments = cash_payments + bank_payments + credit_payments

    instances['payments'] = {
        'cash': cash_payments,
        'bank': bank_payments,
        'total': total_payments,
        'credit': credit_payments,
    }

    # Reciept voucher calculations
    cash_receipts = 0
    bank_receipts = 0
    total_receipts = 0
    credit_receipts = 0

    receipt_vouchers = ReceiptVoucher.objects.filter(is_deleted=False, is_system_generated=False,
                                                     voucher_date__date__range=[from_date, to_date])

    if receipt_vouchers.filter(transfer_type=10).exists():
        cash_receipts = receipt_vouchers.filter(transfer_type=10).aggregate(Sum('amount'))['amount__sum']
    if receipt_vouchers.filter(transfer_type__in=[15, 20, 25]).exists():
        bank_receipts = receipt_vouchers.filter(transfer_type__in=[15, 20, 25]).aggregate(Sum('amount'))['amount__sum']

    total_receipts = cash_receipts + bank_receipts + credit_receipts

    instances['receipts'] = {
        'cash': cash_receipts,
        'bank': bank_receipts,
        'total': total_receipts,
        'credit': credit_receipts,
    }

    # credit note voucher calculations
    cash_credit_note = 0
    bank_credit_note = 0
    total_credit_note = 0
    credit_credit_note = 0

    credit_note_vouchers = CreditNoteVoucher.objects.filter(is_deleted=False,
                                                            voucher_date__date__range=[from_date, to_date])

    if credit_note_vouchers.filter(transfer_type=10).exists():
        cash_credit_note = credit_note_vouchers.filter(transfer_type=10).aggregate(Sum('amount'))['amount__sum']
    if credit_note_vouchers.filter(transfer_type=30).exists():
        credit_credit_note = credit_note_vouchers.filter(transfer_type=30).aggregate(Sum('amount'))['amount__sum']
    if credit_note_vouchers.filter(transfer_type__in=[15, 20, 25]).exists():
        bank_credit_note = credit_note_vouchers.filter(transfer_type__in=[15, 20, 25]).aggregate(Sum('amount'))[
            'amount__sum']

    total_credit_note = cash_credit_note + bank_credit_note + credit_credit_note

    instances['credit_note'] = {
        'cash': cash_credit_note,
        'bank': bank_credit_note,
        'total': total_credit_note,
        'credit': credit_credit_note,
    }

    # debit note voucher calculations
    cash_debit_note = 0
    bank_debit_note = 0
    total_debit_note = 0
    credit_debit_note = 0

    debit_note_vouchers = DebitNoteVoucher.objects.filter(is_deleted=False,
                                                          voucher_date__date__range=[from_date, to_date])

    if debit_note_vouchers.filter(transfer_type=10).exists():
        cash_debit_note = debit_note_vouchers.filter(transfer_type=10).aggregate(Sum('amount'))['amount__sum']
    if debit_note_vouchers.filter(transfer_type=30).exists():
        credit_debit_note = debit_note_vouchers.filter(transfer_type=30).aggregate(Sum('amount'))['amount__sum']
    if debit_note_vouchers.filter(transfer_type__in=[15, 20, 25]).exists():
        bank_debit_note = debit_note_vouchers.filter(transfer_type__in=[15, 20, 25]).aggregate(Sum('amount'))[
            'amount__sum']

    total_debit_note = cash_debit_note + bank_debit_note + credit_debit_note

    instances['debit_note'] = {
        'cash': cash_debit_note,
        'bank': bank_debit_note,
        'total': total_debit_note,
        'credit': credit_debit_note,
    }
    special_discounts = 0
    if sales.exists():
        special_discounts = sales.aggregate(Sum('discount'))['discount__sum']

    context = {
        'title': title,
        "instances": instances,
        "special_discounts": special_discounts,
        "from_date": f_date,
        "to_date": t_date,
    }

    return render(request, 'reports/daily/daily_report.html', context)


@login_required
def ledger_report(request):
    instances = []
    title = 'Ledger Report:'

    t_date = request.GET.get('to_date')
    f_date = request.GET.get('from_date')
    head = request.GET.get('account_head')
    sub_ledger = request.GET.get('sub_ledger')
    warehouse = request.GET.get('warehouse')

    is_admin = True
    warehouse_instances = Warehouse.objects.filter(is_deleted=False)
    account_heads = AccountHead.objects.filter(is_deleted=False)

    if Staff.objects.filter(user=request.user).exists():
        staff_instance = Staff.objects.get(user=request.user)
        warehouse_pks = [staff_instance.warehouse.pk]
        is_admin = False
        warehouse_instances = warehouse_instances.filter(pk=staff_instance.warehouse.pk)

    else:
        if warehouse:
            if warehouse_instances.filter(pk=warehouse).exists():
                warehouse_pks = [warehouse]
            else:
                warehouse_pks = warehouse_instances.values_list('pk', flat=True)
        else:
            warehouse_pks = warehouse_instances.values_list('pk', flat=True)

    today = datetime.datetime.now()

    if not t_date:
        today = datetime.datetime.now()
        t_date = "%s/%s/%s" % (str(today.day), str(today.month), str(today.year))
    if not f_date:
        today = datetime.datetime.now()
        f_date = "%s/%s/%s" % (str(today.day), str(today.month), str(today.year))

    filter_data = {
        'to_date': t_date,
        'from_date': f_date,
        'account_head': head,
        'sub_ledger': sub_ledger,
        'warehouse': warehouse,
    }

    from_date = datetime.datetime.strptime(f_date, '%d/%m/%Y').date()
    to_date = datetime.datetime.strptime(t_date, '%d/%m/%Y').date()

    open_debit = True
    close_debit = True
    closing_balance = 0
    opening_balance = 0
    instances = None

    if head:
        account_head = account_heads.get(pk=head)
        data = get_ledger_data(account_head, from_date, to_date, sub_ledger, 'ledger', warehouse_pk=warehouse_pks)

        closing_balance = data['closing_balance']
        opening_balance = data['opening_balance']
        instances = data['instances']

        if opening_balance < 0:
            open_debit = False
            opening_balance *= -1

        if closing_balance < 0:
            close_debit = False
            closing_balance *= -1

        if instances:
            instances = sorted(instances, key = itemgetter('voucher_date'))

    context = {
        'title': title,
        'filter_data': filter_data,
        "is_admin":is_admin,
        "warehouse_instances": warehouse_instances,
        "account_heads": account_heads,

        "open_debit": open_debit,
        "close_debit": close_debit,
        "closing_balance": closing_balance,
        "opening_balance": opening_balance,
        "instances": instances,
    }

    return render(request, 'reports/final_accounts/ledger.html', context)


@login_required
def trial_balance(request):
    instances = []
    title = 'Trial Balance:'

    f_date = request.GET.get('date')
    warehouse = request.GET.get('warehouse')

    is_admin = True
    warehouse_instances = Warehouse.objects.filter(is_deleted=False)

    if Staff.objects.filter(user=request.user).exists():
        staff_instance = Staff.objects.get(user=request.user)
        warehouse_pks = [staff_instance.warehouse.pk]
        is_admin = False
        warehouse_instances = warehouse_instances.filter(pk=staff_instance.warehouse.pk)

    else:
        if warehouse:
            if warehouse_instances.filter(pk=warehouse).exists():
                warehouse_pks = [warehouse]
            else:
                warehouse_pks = warehouse_instances.values_list('pk', flat=True)
        else:
            warehouse_pks = warehouse_instances.values_list('pk', flat=True)

    today = datetime.datetime.now()

    if not f_date:
        today = datetime.datetime.now()
        f_date = "%s/%s/%s" % (str(today.day), str(today.month), str(today.year))

    filter_date = datetime.datetime.strptime(f_date, '%d/%m/%Y').date()
    date_string = str(filter_date.month) + "%2F" + str(filter_date.day) + "%2F" + str(filter_date.year)

    account_heads = AccountHead.objects.filter(is_deleted=False)
    print("Account Heads ===>",account_heads)

    # new_current_balance = 0
    for head in account_heads:
        data = get_ledger_data(head, filter_date, filter_date, None, 'trial balance', warehouse_pk=warehouse_pks)

        closing_balance = data['closing_balance']
        close_debit = True

        if closing_balance < 0:
            close_debit = False
            closing_balance *= -1

        # ledger_url = reverse('finance:ledger') + "?account_head=%s&from_date=%s&to_date=%s"%(head.pk, date_string, date_string)

        obj = {
            # "url": ledger_url,
            "account_head": head.name,
            "close_debit": close_debit,
            "closing_balance": closing_balance,
        }
        instances.append(obj)

    print("Instances ==>>",instances)

    context = {
        'title': title,
        'filter_date': f_date,
        "instances": instances,
        "is_admin":is_admin,
        "warehouse_instances":warehouse_instances,
        "warehouse":warehouse,
        # "new_current_balance" : new_current_balance,
        # "new_current_debit" : new_current_debit,
    }

    return render(request, 'reports/final_accounts/trial_balance.html', context)




def gstr1_report(request):
    cgst = 0
    sgst = 0
    sales = []
    instances = []
    returns_instances = []
    staff_instance = None
    is_admin = None

    if request.user.is_superuser:
        is_admin = True

    title = "GSTR-1 Report"
    today = datetime.datetime.now().date()
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    warehouse = request.GET.get('warehouse')
    user_role = request.GET.get('user_role')

    if user_role:
        if 'warehouse_manager' in user_role:
            staff_instance = Staff.objects.get(user=request.user)
            is_admin = False

    if not from_date:
        from_date = f'01/{today.month}/{today.year}'
    if not to_date:
        to_date = f'{today.day}/{today.month}/{today.year}'

    if from_date and to_date:
        data = {
            "from_date": from_date,
            "to_date": to_date,
        }
        try:
            from_date = datetime.datetime.strptime(from_date, '%d/%m/%Y').date()
            to_date = datetime.datetime.strptime(to_date, '%d/%m/%Y').date()
        except ValueError:
            date_error = "yes"

    warehouse_instances = Warehouse.objects.filter(is_deleted=False)

    sales = []
    sales = Sale.objects.filter(is_deleted=False, sale_date__date__range=[from_date, to_date]).order_by('sale_date')

    instances = sales
    sale_returns = SaleReturn.objects.filter(is_deleted=False, time__date__range=[from_date, to_date]).order_by('time')

    if staff_instance:
        sales = Sale.objects.filter(warehouse=staff_instance.warehouse,is_deleted=False, sale_date__date__range=[from_date, to_date]).order_by('sale_date')
        sale_returns = SaleReturn.objects.filter(sale__warehouse=staff_instance.warehouse,is_deleted=False, time__date__range=[from_date, to_date]).order_by('time')

    # query section
    if warehouse:
        sales = Sale.objects.filter(warehouse=warehouse, is_deleted=False,
                                    sale_date__date__range=[from_date, to_date]).order_by('sale_date')
        sale_returns = SaleReturn.objects.filter(sale__warehouse=warehouse, is_deleted=False,
                                                 time__date__range=[from_date, to_date]).order_by('time')

    if sale_returns :
        for item in sale_returns:
            cess = 0
            cgst = 0
            sgst = 0
            igst = 0
            tax = 0

            if SaleReturnItem.objects.filter(sale_return=item).exists():
                sale_return_items = SaleReturnItem.objects.filter(sale_return=item)

                for return_item in sale_return_items:
                    sale_item = return_item.sale_item
                    selling_price = sale_item.amount

                    cgst += return_item.qty * (sale_item.cgst / sale_item.quantity)
                    sgst += return_item.qty * (sale_item.sgst / sale_item.quantity)
                    cess += return_item.qty * (sale_item.cess / sale_item.quantity)

            obj = {
                "cess": round(cess, 2),
                "cgst": round(cgst, 2),
                "sgst": round(sgst, 2),
                "igst": igst,
                "date": item.time,
                'sale_id': item.sale.sale_id,
                "amount": item.amount_returned,
                # "gst_in": item.customer.customer_gstn,
            }
            returns_instances.append(obj)
    url_string = f'?from_date={from_date.day}%2F{from_date.month}%2F{from_date.year}&to_date={to_date.day}%2F{to_date.month}%2F{to_date.year}'

    context = {
        "data": data,
        'title': title,
        "today": today,
        "instances": instances,
        "url_string": url_string,
        "returns_instances": returns_instances,
        "is_admin":is_admin,
        "warehouse_instances":warehouse_instances,
        "warehouse":warehouse,
    }

    return render(request, 'reports/gst/gstr1_report.html', context)


@login_required
def gstr2_report(request):
    cgst = 0
    sgst = 0
    sales = []
    instances = []
    returns_instances = []
    is_admin = None
    staff_instance = None

    if request.user.is_superuser:
        is_admin = True

    title = "GSTR-2 Report"
    today = datetime.datetime.now().date()
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    user_role = request.GET.get('user_role')
    warehouse = request.GET.get('warehouse')

    warehouse_instances = Warehouse.objects.filter(is_deleted=False)

    if user_role:
        if 'warehouse_manager' in user_role:
            staff_instance = Staff.objects.get(user=request.user)
            is_admin = False

    if not from_date:
        new_date = today
        if today.day == 1:
            new_date = today - datetime.timedelta(days=1)
        from_date = f'01/{new_date.month}/{new_date.year}'
    if not to_date:
        to_date = f'{today.day}/{today.month}/{today.year}'

    if from_date and to_date:
        data = {
            "from_date": from_date,
            "to_date": to_date,
        }
        try:
            from_date = datetime.datetime.strptime(from_date, '%d/%m/%Y').date()
            to_date = datetime.datetime.strptime(to_date, '%d/%m/%Y').date()
        except ValueError:
            date_error = "yes"

    purchases = []
    if Purchase.objects.filter(is_deleted=False, date__date__range=[from_date, to_date]).exists():
        purchases = Purchase.objects.filter(is_deleted=False, date__date__range=[from_date, to_date]).order_by('date')

    if warehouse:
        if PurchaseReturn.objects.filter(purchase__warehouse=warehouse, is_deleted=False,
                                         date__range=[from_date, to_date]).exists():
            purchase_returns = PurchaseReturn.objects.filter(purchase__warehouse=warehouse,
                                                             is_deleted=False,
                                                             date__range=[from_date, to_date]).order_by('date')

    for purchase in purchases:
        tax = 0
        cgst = 0
        sgst = 0
        igst = 0
        gross_amount = 0
        total_amount = 0

        if PurchaseItem.objects.filter(purchase=purchase).exists():
            purchase_items = PurchaseItem.objects.filter(purchase=purchase)

        if staff_instance:
            if PurchaseItem.objects.filter(purchase=purchase,purchase__warehouse=staff_instance.warehouse).exists():
                purchase_items = PurchaseItem.objects.filter(purchase=purchase,purchase__warehouse=staff_instance.warehouse)

            cgst += purchase_items.aggregate(Sum('cgst_amount'))['cgst_amount__sum']
            sgst += purchase_items.aggregate(Sum('sgst_amount'))['sgst_amount__sum']
            igst += purchase_items.aggregate(Sum('Igst_amount'))['Igst_amount__sum']
            total_amount += purchase_items.aggregate(Sum('total'))['total__sum']
            gross_amount += purchase_items.aggregate(Sum('net_rate'))['net_rate__sum']

        obj = {
            "rate": 0,
            "tax": tax,
            "cgst": cgst,
            "sgst": sgst,
            "igst": igst,
            'date': purchase.date,
            'total': total_amount,
            'gross_amount': gross_amount,
            "state": purchase.warehouse.state,
            'purchase_id': purchase.purchase_id,
            # "gst_in": purchase.warehouse.gst_number,
        }
        instances.append(obj)
    purchase_returns = []

    if PurchaseReturn.objects.filter(is_deleted=False, date__range=[from_date, to_date]).exists():
        purchase_returns = PurchaseReturn.objects.filter(is_deleted=False, date__range=[from_date, to_date]).order_by('date')

    if staff_instance:
        if PurchaseReturn.objects.filter(purchase__warehouse=staff_instance.warehouse,is_deleted=False, date__range=[from_date, to_date]).exists():
            purchase_returns = PurchaseReturn.objects.filter(purchase__warehouse=staff_instance.warehouse,is_deleted=False, date__range=[from_date, to_date]).order_by('date')

    if purchase_returns:
        for purchase_return in purchase_returns:
            cgst = 0
            sgst = 0
            igst = 0
            tax = 0

            if PurchaseReturnItem.objects.filter(purchase_return=purchase_return).exists():
                purchase_return_items = PurchaseReturnItem.objects.filter(purchase_return=purchase_return)

                for return_item in purchase_return_items:
                    purchase_item = return_item.purchase_item
                    purchase_price = purchase_item.net_rate
                    tax += purchase_price - purchase_item.amount

                    cgst += return_item.quantity * (purchase_item.cgst_amount / purchase_item.quantity)
                    sgst += return_item.quantity * (purchase_item.sgst_amount / purchase_item.quantity)
                    igst += return_item.quantity * (purchase_item.Igst_amount / purchase_item.quantity)

            obj = {
                "cgst": round(cgst, 2),
                "sgst": round(sgst, 2),
                "igst": round(igst, 2),
                "date": purchase_return.date,
                "amount": purchase_return.amount_returned,
                "taxable": purchase_return.amount_returned - tax,
                'purchase_id': purchase_return.purchase.purchase_id,
                "gst_in": purchase_return.supplier.gst_number,
            }
            returns_instances.append(obj)

    url_string = f'?from_date={from_date.day}%2F{from_date.month}%2F{from_date.year}&to_date={to_date.day}%2F{to_date.month}%2F{to_date.year}'

    context = {
        "data": data,
        'title': title,
        "today": today,
        "instances": instances,
        "url_string": url_string,
        "returns_instances": returns_instances,
        "is_admin":is_admin,
        "warehouse_instances":warehouse_instances,
        "warehouse":warehouse,
    }

    return render(request, 'reports/gst/gstr2_report.html', context)


@login_required
def gstr3_report(request):
    cgst = 0
    sgst = 0
    sale_instances = []
    purchase_instances = []
    sale_returns_instances = []
    purchase_returns_instances = []
    today = datetime.datetime.now().date()

    is_admin = None
    if request.user.is_superuser:
        is_admin = True

    title = "GSTR-3 Report"

    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    warehouse = request.GET.get('warehouse')
    user_role = request.GET.get('user_role')

    warehouse_instances = Warehouse.objects.filter(is_deleted=False)

    if not from_date:
        from_date = f'01/{today.month}/{today.year}'
    if not to_date:
        to_date = f'{today.day}/{today.month}/{today.year}'

    if from_date and to_date:
        data = {
            "from_date": from_date,
            "to_date": to_date,
        }
        try:
            from_date = datetime.datetime.strptime(from_date, '%d/%m/%Y').date()
            to_date = datetime.datetime.strptime(to_date, '%d/%m/%Y').date()
        except ValueError:
            date_error = "yes"

    sales = Sale.objects.filter(is_deleted=False, sale_date__date__range=[from_date, to_date]).order_by('sale_date')
    sale_returns = SaleReturn.objects.filter(is_deleted=False, time__date__range=[from_date, to_date]).order_by('time')

    if user_role:
        if 'warehouse_manager' in user_role:
            staff_instance = Staff.objects.get(user=request.user)
            is_admin = False
            sales = Sale.objects.filter(warehouse=staff_instance.warehouse,is_deleted=False, sale_date__date__range=[from_date, to_date]).order_by(
                'sale_date')
            sale_returns = SaleReturn.objects.filter(sale__warehouse=staff_instance.warehouse,is_deleted=False, time__date__range=[from_date, to_date]).order_by(
                'time')

    if warehouse:
        sales = Sale.objects.filter(warehouse=warehouse, is_deleted=False,
                                    sale_date__date__range=[from_date, to_date]).order_by(
            'sale_date')
        sale_returns = SaleReturn.objects.filter(sale__warehouse=warehouse, is_deleted=False,
                                                 time__date__range=[from_date, to_date]).order_by(
            'time')

    for sale in sales:
        obj = {
            "cgst": sale.cgst,
            "sgst": sale.sgst,
            "igst": sale.igst,
            'total': sale.subtotal,
            'gross_amount': sale.sale_taxable_amount,
        }
        sale_instances.append(obj)

    for sale_return in sale_returns:
        cess = 0
        cgst = 0
        sgst = 0
        igst = 0
        tax = 0
        if SaleReturnItem.objects.filter(sale_return=sale_return).exists():
            sale_return_items = SaleReturnItem.objects.filter(sale_return=sale_return)

            for return_item in sale_return_items:
                sale_item = return_item.sale_item

                cgst += return_item.qty * (sale_item.cgst / sale_item.quantity)
                sgst += return_item.qty * (sale_item.sgst / sale_item.quantity)
                cess += return_item.qty * (sale_item.cess / sale_item.quantity)

        obj = {
            "cess": round(cess, 2),
            "cgst": round(cgst, 2),
            "sgst": round(sgst, 2),
            "igst": round(igst, 2),
            "date": sale_return.time,
            'sale_id': sale_return.sale.sale_id,
            "gross_amount": sale_return.amount_returned,
        }
        sale_returns_instances.append(obj)

    # sale total calculation
    sale_tax = 0
    sale_cgst = 0
    sale_sgst = 0
    sale_igst = 0
    sale_total = 0
    sale_cess = 0
    sale_gross_amount = 0
    for instance in sale_instances:
        sale_cgst += float(instance['cgst'])
        sale_sgst += float(instance['sgst'])
        sale_igst += float(instance['igst'])
        sale_total += float(instance['total'])
        sale_gross_amount += float(instance['gross_amount'])

    sale_total_obj = {
        'cgst': sale_cgst,
        'sgst': sale_sgst,
        'igst': sale_igst,
        'total': sale_total,
        'gross_amount': sale_gross_amount,
    }

    return_cess = 0
    return_cgst = 0
    return_sgst = 0
    return_igst = 0
    return_amount = 0
    return_gross_amount = 0
    for instance in sale_returns_instances:
        return_cgst += float(instance['cgst'])
        return_sgst += float(instance['sgst'])
        return_igst += float(instance['igst'])
        return_amount += float(instance['gross_amount'])
        return_gross_amount += float(instance['gross_amount'])
    sale_return_total_obj = {
        'cgst': return_cgst,
        'sgst': return_sgst,
        'igst': return_igst,
        'amount': return_amount,
        'gross_amount': return_gross_amount,
    }
    sale_final_obj = {
        'cgst': round((sale_total_obj['cgst'] - sale_return_total_obj['cgst']), 2),
        'sgst': round((sale_total_obj['sgst'] - sale_return_total_obj['sgst']), 2),
        'igst': round((sale_total_obj['igst'] - sale_return_total_obj['igst']), 2),
        'total': round((sale_total_obj['total'] - sale_return_total_obj['amount']), 2),
        'gross_amount': round((sale_total_obj['gross_amount'] - sale_return_total_obj['gross_amount']), 2),
    }

    purchases = Purchase.objects.filter(is_deleted=False, date__date__range=[from_date, to_date]).order_by('date')
    purchase_returns = PurchaseReturn.objects.filter(is_deleted=False, date__range=[from_date, to_date]).order_by('date')

    if user_role:
        if 'warehouse_manager' in user_role:
            purchases = Purchase.objects.filter(warehouse=staff_instance.warehouse,is_deleted=False, date__date__range=[from_date, to_date]).order_by(
                'date')
            purchase_returns = PurchaseReturn.objects.filter(purchase__warehouse=staff_instance.warehouse,is_deleted=False,
                                                             date__range=[from_date, to_date]).order_by('date')

    if warehouse:
        purchases = Purchase.objects.filter(warehouse=warehouse, is_deleted=False,
                                            date__date__range=[from_date, to_date]).order_by(
            'date')
        purchase_returns = PurchaseReturn.objects.filter(purchase__warehouse=warehouse, is_deleted=False,
                                                         date__range=[from_date, to_date]).order_by('date')

    for purchase in purchases:
        tax = 0
        cgst = 0
        sgst = 0
        igst = 0
        gross_amount = 0
        total_amount = 0
        if PurchaseItem.objects.filter(purchase=purchase).exists():
            purchase_items = PurchaseItem.objects.filter(purchase=purchase)

            cgst += purchase_items.aggregate(Sum('cgst_amount'))['cgst_amount__sum']
            sgst += purchase_items.aggregate(Sum('sgst_amount'))['sgst_amount__sum']
            igst += purchase_items.aggregate(Sum('igst_amount'))['igst_amount__sum']
            total_amount += purchase_items.aggregate(Sum('total'))['total__sum']
            gross_amount += purchase_items.aggregate(Sum('net_rate'))['net_rate__sum']

        obj = {
            "rate": 0,
            "tax": tax,
            "cgst": cgst,
            "sgst": sgst,
            "igst": igst,
            'date': purchase.date,
            'total': total_amount,
            'gross_amount': gross_amount,
            "state": purchase.warehouse.state,
            'purchase_id': purchase.purchase_id,
            "gst_in": purchase.supplier.gst_number,
        }
        purchase_instances.append(obj)

    if purchase_returns:
        for purchase_return in purchase_returns:
            cgst = 0
            sgst = 0
            igst = 0
            tax = 0

            if PurchaseReturnItem.objects.filter(purchase_return=purchase_return).exists():
                purchase_return_items = PurchaseReturnItem.objects.filter(purchase_return=purchase_return)

                for return_item in purchase_return_items:
                    purchase_item = return_item.purchase_item
                    purchase_price = purchase_item.net_rate
                    tax += purchase_price - purchase_item.amount

                    cgst += return_item.quantity * (purchase_item.cgst_amount / purchase_item.quantity)
                    sgst += return_item.quantity * (purchase_item.sgst_amount / purchase_item.quantity)
                    igst += return_item.quantity * (purchase_item.Igst_amount / purchase_item.quantity)

            obj = {
                "cgst": round(cgst, 2),
                "sgst": round(sgst, 2),
                "igst": round(igst, 2),
                "date": purchase_return.date,
                "gross_amount": purchase_return.amount_returned,
                "taxable": purchase_return.amount_returned - tax,
                'purchase_id': purchase_return.purchase.purchase_id,
                "gst_in": purchase_return.vendor.gst_number,
            }
            purchase_returns_instances.append(obj)

    # Total purchase calculations
    purchase_cgst = 0
    purchase_sgst = 0
    purchase_igst = 0
    purchase_total = 0
    purchase_gross_amount = 0
    for instance in purchase_instances:
        purchase_cgst += float(instance['cgst'])
        purchase_sgst += float(instance['sgst'])
        purchase_igst += float(instance['igst'])
        purchase_total += float(instance['total'])
        purchase_gross_amount += float(instance['gross_amount'])
    purchase_total_obj = {
        'cgst': purchase_cgst,
        'sgst': purchase_sgst,
        'igst': purchase_igst,
        'total': purchase_total,
        'gross_amount': purchase_gross_amount,
    }
    return_cgst = 0
    return_sgst = 0
    return_igst = 0
    return_amount = 0
    return_taxable = 0
    for instance in purchase_returns_instances:
        return_cgst += float(instance['cgst'])
        return_sgst += float(instance['sgst'])
        return_igst += float(instance['igst'])
        return_amount += float(instance['gross_amount'])
        return_taxable += float(instance['gross_amount'])
    purchase_return_total_obj = {
        'cgst': return_cgst,
        'sgst': return_sgst,
        'igst': return_igst,
        'total': return_amount,
        'gross_amount': return_taxable,
    }
    purchase_final_obj = {
        'cgst': round((purchase_total_obj['cgst'] - purchase_return_total_obj['cgst']), 2),
        'sgst': round((purchase_total_obj['sgst'] - purchase_return_total_obj['sgst']), 2),
        'igst': round((purchase_total_obj['igst'] - purchase_return_total_obj['igst']), 2),
        'total': round((purchase_total_obj['total'] - purchase_return_total_obj['total']), 2),
        'gross_amount': round((purchase_total_obj['gross_amount'] - purchase_return_total_obj['gross_amount']), 2),
    }

    # ---------- final report -----------

    final_obj = {
        'cgst': round(sale_final_obj['cgst'] - purchase_final_obj['cgst'], 2),
        'sgst': round(sale_final_obj['sgst'] - purchase_final_obj['sgst'], 2),
        'igst': round(sale_final_obj['igst'] - purchase_final_obj['igst'], 2),
        'total': round(sale_final_obj['total'] - purchase_final_obj['total'], 2),
        'gross_amount': round(sale_final_obj['gross_amount'] - purchase_final_obj['gross_amount'], 2),
    }

    url_string = f'?from_date={from_date.day}%2F{from_date.month}%2F{from_date.year}'
    url_string += f'&to_date={to_date.day}%2F{to_date.month}%2F{to_date.year}'
    context = {
        "data": data,
        'title': title,
        "today": today,
        "total": final_obj,
        "url_string": url_string,
        "sale_final": sale_final_obj,
        "purchase_final": purchase_final_obj,
        "warehouse_instances":warehouse_instances,
        "warehouse":warehouse,
        "is_admin":is_admin,
    }

    return render(request, 'reports/gst/gstr3_report.html', context)