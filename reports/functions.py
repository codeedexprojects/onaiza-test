import json
import datetime
from itertools import chain
from operator import attrgetter, itemgetter
from icecream import ic as printing
from django.db.models import Q, F, Sum, Count

from finance.models import *
from orders.models import Orders
from purchases.models import Purchase
from sales.models import Sale
from vendors.models import Vendor
from customers.models import Customer
from suppliers.models import Supplier
from warehouses.models import Warehouse
from delivery_agent.models import DeliveryAgents
from orders.serializers import OrdersSerializer
from purchases.serializers import PurchaseSerializer, VendorPurchaseSerializer
from sales.serializers import SaleSerializer
from finance.serializers import PaymentVoucherSerializer, ReceiptVoucherSerializer, JournalVoucherItemSerializer, CreditNoteVoucherSerializer, DebitNoteVoucherSerializer


def get_ledger_data(head, from_date, to_date, sub_ledger, report='ledger', warehouse_pk=[]):
    is_need_closing = False
    is_need_instances = False
    # amount_type = 10(credit)
    # amount_type = 20(debit)

    if report in ['ledger', 'day book']:
        is_need_instances = True
        instances = []

    elif report in ['trial balance', 'current balance', 'profit and loss', 'balance sheet']:
        is_need_closing = True

    ac_head_code = head.code
    date_range = from_date - datetime.timedelta(days=1)

    data = {}
    ac_opening = 0
    debit_total = 0
    credit_total = 0
    opening_balance = 0
    closing_balance = 0
    ac_opening_type = ''
    is_sub_ledger = False

    if sub_ledger:
        is_sub_ledger = True
    else:
        sub_ledger = ''

    # set opening bal of subledger
    financial_year = None
    opening_debit_amount = 0
    opening_credit_amount = 0
    previous_payment_vouchers = PaymentVoucher.objects.none()
    previous_receipt_vouchers = ReceiptVoucher.objects.none()

    if FinancialYear.objects.filter(is_deleted=False, is_active=True).exists():
        financial_year = FinancialYear.objects.filter(is_deleted=False, is_active=True).last()
        first_date = financial_year.start_date.date()

        # checking if account head is in the list that can have subledger
        if ac_head_code in ['sundry_debtor_customer', 'sundry_creditor_supplier', 'sundry_creditor_delivery_agent']:
            if ac_head_code == 'sundry_debtor_customer':
                sub_ledger_type = 10
            elif ac_head_code == 'sundry_creditor_supplier':
                sub_ledger_type = 20
            elif ac_head_code == 'sundry_creditor_vendor':
                sub_ledger_type = 30
            elif ac_head_code == 'sundry_creditor_delivery_agent':
                sub_ledger_type = 40
            else:
                sub_ledger_type = 0

            if sub_ledger != '':  # to take only chosen customer's opening balance
                opening_balance_instances = SubledgerOpening.objects.filter(financial_year__pk=financial_year.pk, sub_ledger_type=sub_ledger_type, is_deleted=False, sub_ledger=sub_ledger)

                if opening_balance_instances.exists():
                    if opening_balance_instances.filter(amount_type=20).exists():
                        opening_debit_amount = opening_balance_instances.filter(amount_type=20).last().amount
                    if opening_balance_instances.filter(amount_type=10).exists():
                        opening_credit_amount = opening_balance_instances.filter(amount_type=10).last().amount

            else:  # to take all customer's opening balance since no customer has been chosen
                is_sub_ledger = False
                opening_balance_instances = SubledgerOpening.objects.filter(financial_year__pk=financial_year.pk, sub_ledger=sub_ledger_type, is_deleted=False)

                if opening_balance_instances.exists():
                    if opening_balance_instances.filter(amount_type=20).exists():
                        opening_debit_amount = opening_balance_instances.filter(amount_type=20).aggregate(amount=Sum('amount')).get('amount', 0)
                    if opening_balance_instances.filter(amount_type=10).exists():
                        opening_credit_amount = opening_balance_instances.filter(amount_type=10).aggregate(amount=Sum('amount')).get('amount', 0)
        else:
            is_sub_ledger = False
            # get opening balance of account head which won't have subledger
            opening_balance_instances = AccountHeadOpening.objects.filter(financial_year__pk=financial_year.pk, is_deleted=False, account_head=head, warehouse__pk__in=warehouse_pk)

            if opening_balance_instances.exists():
                if opening_balance_instances.filter(amount_type__in=[20, 'debit']).exists():
                    opening_debit_amount = opening_balance_instances.filter(amount_type__in=[20, 'debit']).aggregate(Sum('amount'))['amount__sum']
                if opening_balance_instances.filter(amount_type__in=[10, 'credit']).exists():
                    opening_credit_amount = opening_balance_instances.filter(amount_type__in=[10, 'credit']).aggregate(Sum('amount'))['amount__sum']

    opening_balance -= opening_credit_amount
    opening_balance += opening_debit_amount

    credit_total += opening_credit_amount
    debit_total += opening_debit_amount

    if is_sub_ledger:
        payment_vouchers = PaymentVoucher.objects.filter(is_deleted=False, sub_ledger=sub_ledger, account_head=head, warehouse__pk__in=warehouse_pk).order_by('voucher_date')
        receipt_vouchers = ReceiptVoucher.objects.filter(is_deleted=False, sub_ledger=sub_ledger, account_head=head, warehouse__pk__in=warehouse_pk).order_by('voucher_date')
        journal_voucher_items = JournalVoucherItem.objects.filter(journal__is_deleted=False, sub_ledger=sub_ledger, account_head=head, warehouse__pk__in=warehouse_pk).order_by('journal__voucher_date')

    else:
        payment_vouchers = PaymentVoucher.objects.filter(is_deleted=False, account_head=head, warehouse__pk__in=warehouse_pk).order_by('voucher_date')
        receipt_vouchers = ReceiptVoucher.objects.filter(is_deleted=False, account_head=head, warehouse__pk__in=warehouse_pk).order_by('voucher_date')
        journal_voucher_items = JournalVoucherItem.objects.filter(journal__is_deleted=False, account_head=head, warehouse__pk__in=warehouse_pk).order_by('journal__voucher_date')

    # opening balance calculations of all vouchers
    if payment_vouchers.exists():
        if not financial_year:
            first_date = payment_vouchers.first().voucher_date.date()
        previous_payment_voucher = payment_vouchers.filter(voucher_date__date__range=[first_date, date_range])

        if previous_payment_voucher.exists():
            previous_amount = previous_payment_voucher.aggregate(amount=Sum('amount')).get('amount', 0)
            opening_balance += previous_amount
            debit_total += previous_amount

    if receipt_vouchers.exists():
        if not financial_year:
            first_date = receipt_vouchers.first().voucher_date.date()
        previous_receipt_voucher = receipt_vouchers.filter(voucher_date__date__range=[first_date, date_range])

        if previous_receipt_voucher.exists():
            previous_amount = previous_receipt_voucher.aggregate(amount=Sum('amount')).get('amount', 0)
            opening_balance -= previous_amount
            credit_total += previous_amount

    if journal_voucher_items.exists():
        if not financial_year:
            first_date = journal_voucher_items.first().journal.voucher_date.date()
        previous_journal_voucher_items = journal_voucher_items.filter(journal__voucher_date__date__range=[first_date, date_range])

        if previous_journal_voucher_items.exists():
            if previous_journal_voucher_items.filter(amount_type=20).exists():
                previous_debit_amount = previous_journal_voucher_items.filter(amount_type=20).aggregate(amount=Sum('amount')).get('amount', 0)
                opening_balance += previous_debit_amount

            if previous_journal_voucher_items.filter(amount_type=10).exists():
                previous_credit_amount = previous_journal_voucher_items.filter(amount_type=10).aggregate(amount=Sum('amount')).get('amount', 0)
                opening_balance -= previous_credit_amount
    # Opening Balance of vouchers calculations ends here

    # vouchers on period
    current_payment_vouchers = payment_vouchers.filter(amount__gt=0, voucher_date__date__range=[from_date, to_date])
    current_receipt_vouchers = receipt_vouchers.filter(amount__gt=0, voucher_date__date__range=[from_date, to_date])
    current_journal_voucher_items = journal_voucher_items.filter(amount__gt=0, journal__voucher_date__date__range=[from_date, to_date])

    closing_balance = opening_balance

    if head.bank_account:
        bank_payment_vouchers = PaymentVoucher.objects.filter(transfer_type__in=[15, 20, 25], bank=head.bank_account,is_deleted=False,warehouse__pk__in=warehouse_pk).order_by('voucher_date')
        bank_receipt_vouchers = ReceiptVoucher.objects.filter(transfer_type__in=[15, 20, 25], bank=head.bank_account,is_deleted=False,warehouse__pk__in=warehouse_pk).order_by('voucher_date')
        bank_credit_note_vouchers = CreditNoteVoucher.objects.filter(transfer_type__in=[15, 20, 25], bank=head.bank_account,is_deleted=False,warehouse__pk__in=warehouse_pk).order_by('voucher_date')
        bank_debit_note_vouchers = DebitNoteVoucher.objects.filter(transfer_type__in=[15, 20, 25], bank=head.bank_account,is_deleted=False,warehouse__pk__in=warehouse_pk).order_by('voucher_date')

        # opening balance calculations of all vouchers
        if bank_payment_vouchers:
            if not financial_year:
                first_date = bank_payment_vouchers.first().voucher_date.date()

            bank_previous_payment_voucher = bank_payment_vouchers.filter(voucher_date__date__range=[first_date, date_range])
            if bank_previous_payment_voucher.exists():
                total_voucher_amount = bank_previous_payment_voucher.aggregate(amount=Sum('amount')).get('amount', 0)
                opening_balance -= total_voucher_amount

        if bank_receipt_vouchers:
            if not financial_year:
                first_date = bank_receipt_vouchers.first().voucher_date.date()

            bank_previous_receipt_voucher = bank_receipt_vouchers.filter(voucher_date__date__range=[first_date, date_range])
            if bank_previous_receipt_voucher.exists():
                total_voucher_amount = bank_previous_receipt_voucher.aggregate(amount=Sum('amount')).get('amount', 0)
                opening_balance += total_voucher_amount

        if bank_credit_note_vouchers:
            if not financial_year:
                first_date = bank_credit_note_vouchers.first().voucher_date.date()

            bank_previous_credit_note_voucher = bank_credit_note_vouchers.filter(voucher_date__date__range=[first_date, date_range])
            if bank_previous_credit_note_voucher.exists():
                total_voucher_amount = bank_previous_credit_note_voucher.aggregate(amount=Sum('amount')).get('amount', 0)
                opening_balance -= total_voucher_amount

        if bank_debit_note_vouchers:
            if not financial_year:
                first_date = bank_debit_note_vouchers.first().voucher_date.date()

            bank_previous_debit_note_voucher = bank_debit_note_vouchers.filter(voucher_date__date__range=[first_date, date_range])
            if bank_previous_debit_note_voucher.exists():
                total_voucher_amount = bank_previous_debit_note_voucher.aggregate(amount=Sum('amount')).get('amount', 0)
                opening_balance += total_voucher_amount

        bank_payment_vouchers = bank_payment_vouchers.filter(voucher_date__date__range=[from_date, to_date])
        bank_receipt_vouchers = bank_receipt_vouchers.filter(voucher_date__date__range=[from_date, to_date])
        bank_debit_note_vouchers = bank_debit_note_vouchers.filter(voucher_date__date__range=[from_date, to_date])
        bank_credit_note_vouchers = bank_credit_note_vouchers.filter(voucher_date__date__range=[from_date, to_date])
        # Opening Balance calculations ends here

        closing_balance = opening_balance

        if bank_payment_vouchers.exists():
            total_voucher_amount = bank_payment_vouchers.aggregate(amount=Sum('amount')).get('amount', 0)
            closing_balance -= total_voucher_amount

        if bank_receipt_vouchers.exists():
            total_voucher_amount = bank_receipt_vouchers.aggregate(amount=Sum('amount')).get('amount', 0)
            closing_balance += total_voucher_amount

        if bank_credit_note_vouchers.exists():
            total_voucher_amount = bank_credit_note_vouchers.aggregate(amount=Sum('amount')).get('amount', 0)
            closing_balance -= total_voucher_amount

        if bank_debit_note_vouchers.exists():
            total_voucher_amount = bank_debit_note_vouchers.aggregate(amount=Sum('amount')).get('amount', 0)
            closing_balance += total_voucher_amount

        if is_need_instances:
            payment_serialized = PaymentVoucherSerializer(bank_payment_vouchers, many=True,context={"head": head, 'amount_type': 10, })
            instances += payment_serialized.data

            receipt_serialized = ReceiptVoucherSerializer(bank_receipt_vouchers, many=True,context={"head": head, 'amount_type': 20, })
            instances += receipt_serialized.data

            credit_note_serialized = CreditNoteVoucherSerializer(bank_credit_note_vouchers, many=True,context={"head": head, 'amount_type': 10, })
            instances += credit_note_serialized.data

            debit_note_serialized = DebitNoteVoucherSerializer(bank_debit_note_vouchers, many=True,context={"head": head, 'amount_type': 20, })
            instances += debit_note_serialized.data

    elif ac_head_code == 'cash_account':
        cash_payment_vouchers = PaymentVoucher.objects.filter(transfer_type=10, is_deleted=False,warehouse__pk__in=warehouse_pk).order_by('voucher_date')
        cash_receipt_vouchers = ReceiptVoucher.objects.filter(transfer_type=10, is_deleted=False,warehouse__pk__in=warehouse_pk).order_by('voucher_date')
        cash_debit_note_vouchers = DebitNoteVoucher.objects.filter(transfer_type=10, is_deleted=False,warehouse__pk__in=warehouse_pk).order_by('voucher_date')
        cash_credit_note_vouchers = CreditNoteVoucher.objects.filter(transfer_type=10, is_deleted=False,warehouse__pk__in=warehouse_pk).order_by('voucher_date')

        # opening balance calculations of all vouchers
        if cash_payment_vouchers:
            if not financial_year:
                first_date = cash_payment_vouchers.first().voucher_date.date()

            cash_previous_payment_voucher = cash_payment_vouchers.filter(voucher_date__date__range=[first_date, date_range])
            if cash_previous_payment_voucher.exists():
                total_voucher_amount = cash_previous_payment_voucher.aggregate(amount=Sum('amount')).get('amount', 0)
                opening_balance -= total_voucher_amount

        if cash_receipt_vouchers:
            if not financial_year:
                first_date = cash_receipt_vouchers.first().voucher_date.date()

            cash_previous_receipt_voucher = cash_receipt_vouchers.filter(voucher_date__date__range=[first_date, date_range])
            if cash_previous_receipt_voucher.exists():
                total_voucher_amount = cash_previous_receipt_voucher.aggregate(amount=Sum('amount')).get('amount', 0)
                opening_balance += total_voucher_amount

        if cash_credit_note_vouchers:
            if not financial_year:
                first_date = cash_credit_note_vouchers.first().voucher_date.date()

            cash_previous_credit_note_voucher = cash_credit_note_vouchers.filter(voucher_date__date__range=[first_date, date_range])
            if cash_previous_credit_note_voucher.exists():
                total_voucher_amount = cash_previous_credit_note_voucher.aggregate(amount=Sum('amount')).get('amount', 0)
                opening_balance -= total_voucher_amount

        if cash_debit_note_vouchers:
            if not financial_year:
                first_date = cash_debit_note_vouchers.first().voucher_date.date()

            cash_previous_debit_note_voucher = cash_debit_note_vouchers.filter(voucher_date__date__range=[first_date, date_range])
            if cash_previous_debit_note_voucher.exists():
                total_voucher_amount = cash_previous_debit_note_voucher.aggregate(amount=Sum('amount')).get('amount', 0)
                opening_balance += total_voucher_amount

        cash_payment_vouchers = cash_payment_vouchers.filter(voucher_date__date__range=[from_date, to_date])
        cash_receipt_vouchers = cash_receipt_vouchers.filter(voucher_date__date__range=[from_date, to_date])
        cash_debit_note_vouchers = cash_debit_note_vouchers.filter(voucher_date__date__range=[from_date, to_date])
        cash_credit_note_vouchers = cash_credit_note_vouchers.filter(voucher_date__date__range=[from_date, to_date])
        # Opening Balance calculations ends here

        closing_balance = opening_balance

        if cash_payment_vouchers.exists():
            total_voucher_amount = cash_payment_vouchers.aggregate(amount=Sum('amount')).get('amount', 0)
            closing_balance -= total_voucher_amount

        if cash_receipt_vouchers.exists():
            total_voucher_amount = cash_receipt_vouchers.aggregate(amount=Sum('amount')).get('amount', 0)
            closing_balance += total_voucher_amount

        if cash_credit_note_vouchers.exists():
            total_voucher_amount = cash_credit_note_vouchers.aggregate(amount=Sum('amount')).get('amount', 0)
            closing_balance -= total_voucher_amount

        if cash_debit_note_vouchers.exists():
            total_voucher_amount = cash_debit_note_vouchers.aggregate(amount=Sum('amount')).get('amount', 0)
            closing_balance += total_voucher_amount

        if is_need_instances:
            payment_serialized = PaymentVoucherSerializer(cash_payment_vouchers, many=True,context={"head": head, 'amount_type': 10, })
            instances += payment_serialized.data

            receipt_serialized = ReceiptVoucherSerializer(cash_receipt_vouchers, many=True,context={"head": head, 'amount_type': 20, })
            instances += receipt_serialized.data

            credit_note_serialized = CreditNoteVoucherSerializer(cash_credit_note_vouchers, many=True,context={"head": head, 'amount_type': 10, })
            instances += credit_note_serialized.data

            debit_note_serialized = DebitNoteVoucherSerializer(cash_debit_note_vouchers, many=True,context={"head": head, 'amount_type': 20, })
            instances += debit_note_serialized.data

    elif ac_head_code == 'purchases':
        if Purchase.objects.filter(is_deleted=False,warehouse__pk__in=warehouse_pk).exists():
            purchases = Purchase.objects.filter(is_deleted=False,warehouse__pk__in=warehouse_pk).order_by('date')
            if not financial_year:
                first_date = purchases.first().date.date()

            if purchases.filter(date__date__range=[first_date, date_range]).exists():
                previous_purchases = purchases.filter(date__date__range=[first_date, date_range])

                total_purchase_amount = previous_purchases.aggregate(subtotal=Sum('subtotal')).get('subtotal', 0)
                opening_balance += total_purchase_amount

        closing_balance = opening_balance

        if Purchase.objects.filter(is_deleted=False, date__date__range=[from_date, to_date],warehouse__pk__in=warehouse_pk).exists():
            purchases = Purchase.objects.filter(is_deleted=False, date__date__range=[from_date, to_date],warehouse__pk__in=warehouse_pk)

            purchase_total = purchases.aggregate(subtotal=Sum('subtotal')).get('subtotal', 0)
            closing_balance += purchase_total

            if is_need_instances:
                # Serialized purchase items to array
                serialized_data = PurchaseSerializer(purchases, many=True, context={'head': head})
                instances += serialized_data.data

    elif ac_head_code == 'sales_account':
        if Sale.objects.filter(is_deleted=False,warehouse__pk__in=warehouse_pk).exists():
            sales = Sale.objects.filter(is_deleted=False,warehouse__pk__in=warehouse_pk).order_by('sale_date')
            if not financial_year:
                first_date = sales.first().sale_date

            if sales.filter(is_deleted=False, sale_date__date__range=[first_date, date_range],warehouse__pk__in=warehouse_pk).exists():
                previous_sales = sales.filter(is_deleted=False, sale_date__date__range=[first_date, date_range])

                total_sale_amount = previous_sales.aggregate(total=Sum('total')).get('total', 0)
                opening_balance -= total_sale_amount

        closing_balance = opening_balance

        if Sale.objects.filter(is_deleted=False, sale_date__date__range=[from_date, to_date],warehouse__pk__in=warehouse_pk).exists():
            sales = Sale.objects.filter(is_deleted=False, sale_date__date__range=[from_date, to_date],warehouse__pk__in=warehouse_pk)

            sale_total = sales.aggregate(total=Sum('total')).get('total', 0)
            closing_balance -= sale_total

            if is_need_instances:
                # Serialized sale items to array
                serialized_data = SaleSerializer(sales, many=True, context={'head': head, 'amount_type': 10})
                instances += serialized_data.data

    elif ac_head_code == 'online_sales':

        if Orders.objects.filter(is_deleted=False, order_status='30',warehouse__pk__in=warehouse_pk).exists():
            orders = Orders.objects.filter(is_deleted=False, order_status='30',warehouse__pk__in=warehouse_pk).order_by('date_added')
            if not financial_year:
                first_date = orders.first().date_added.date()

            if orders.filter(date_added__date__range=[first_date, date_range]).exists():
                previous_orders = orders.filter(date_added__date__range=[first_date, date_range])

                total_order_amount = previous_orders.aggregate(total_amt=Sum('total_amt')).get('total_amt', 0)
                opening_balance -= total_order_amount

        closing_balance = opening_balance

        if Orders.objects.filter(is_deleted=False, order_status='10',date_added__date__range=[from_date, to_date],warehouse__pk__in=warehouse_pk).exists():
            orders = Orders.objects.filter(is_deleted=False, order_status='10',date_added__date__range=[from_date, to_date],warehouse__pk__in=warehouse_pk)

            order_total = orders.aggregate(total_amt=Sum('total_amt')).get('total_amt', 0)
            closing_balance -= order_total

            if is_need_instances:
                # Serialized order items to array
                serialized_data = OrdersSerializer(orders, many=True, context={'head': head, 'amount_type': 10})
                instances += serialized_data.data

    elif ac_head_code == "sundry_creditor_supplier":
        purchases = Purchase.objects.none()
        suppliers = Supplier.objects.filter(is_deleted=False)
        debit_notes = DebitNoteVoucher.objects.none()

        if is_sub_ledger:
            if suppliers.filter(pk=sub_ledger).exists():
                supplier = suppliers.get(pk=sub_ledger)

                debit_notes = DebitNoteVoucher.objects.filter(supplier=supplier, is_deleted=False, warehouse__pk__in=warehouse_pk)
                purchases = Purchase.objects.filter(is_deleted=False, supplier=supplier, warehouse__pk__in=warehouse_pk).order_by('date')
        else:
            debit_notes = DebitNoteVoucher.objects.filter(is_deleted=False,warehouse__pk__in=warehouse_pk)
            purchases = Purchase.objects.filter(is_deleted=False, warehouse__pk__in=warehouse_pk).order_by('date')

        if purchases.exists():
            if not financial_year:
                first_date = purchases.first().date.date()

            if purchases.filter(date__date__range=[first_date, date_range]).exists():
                previous_purchases = purchases.filter(date__date__range=[first_date, date_range])

                previous_purchases_dict = previous_purchases.aggregate(Sum('subtotal'), Sum('paid'))
                previous_purchases_total = previous_purchases_dict['subtotal__sum']

                opening_balance -= previous_purchases_total

        if debit_notes.filter(transfer_type=30).exists():
            if not financial_year:
                first_date = debit_notes.filter(transfer_type=30).order_by('voucher_date').first().voucher_date.date()
            if debit_notes.filter(transfer_type=30, voucher_date__date__range=[first_date, date_range]).exists():
                prev_debit_notes = debit_notes.filter(transfer_type=30, voucher_date__date__range=[first_date, date_range]).aggregate(amount=Sum('amount'))
                # debit_note_total_payable = prev_debit_notes.get('payable_amount', 0)
                debit_note_total_amount = prev_debit_notes.get('amount', 0)
                # opening_balance += debit_note_total_payable
                opening_balance += debit_note_total_amount

        closing_balance = opening_balance

        if purchases.filter(date__date__range=[from_date, to_date],warehouse__pk__in=warehouse_pk).exists():
            purchases = purchases.filter(date__date__range=[from_date, to_date],warehouse__pk__in=warehouse_pk).order_by('date')

            purchases_dict = purchases.aggregate(Sum('subtotal'), Sum('paid'))
            purchases_total = purchases_dict['subtotal__sum']

            closing_balance -= purchases_total

            if is_need_instances:
                serialized_purchase_credit = VendorPurchaseSerializer(purchases, many=True, context={'amount_type': 10, 'head': head})
                instances += serialized_purchase_credit.data

                # serialized_purchase_debit = VendorPurchaseSerializer(purchases, many=True, context={'amount_type': 20, 'head': head})
                # instances += serialized_purchase_debit.data

        if debit_notes.filter(voucher_date__date__range=[from_date, to_date]).exists():
            debit_notes = debit_notes.filter(voucher_date__date__range=[from_date, to_date])
            debit_note_data = debit_notes.aggregate(amount=Sum('amount'))
            debit_note_total_amount = debit_note_data.get('amount', 0)

            closing_balance += debit_note_total_amount

            if is_need_instances:
                debit_note_serialized = DebitNoteVoucherSerializer(debit_notes, many=True, context={"head": head, 'amount_type': 20, })
                instances += debit_note_serialized.data

        if debit_notes.filter(voucher_date__date__range=[from_date, to_date]).exclude(transfer_type=30).exists():
            debit_notes = debit_notes.filter(voucher_date__date__range=[from_date, to_date]).exclude(transfer_type=30)
            debit_note_data = debit_notes.aggregate(amount=Sum('amount'))
            debit_note_total_amount = debit_note_data.get('amount', 0)

            closing_balance -= debit_note_total_amount

            if is_need_instances:
                debit_note_serialized = DebitNoteVoucherSerializer(debit_notes, many=True, context={"head": head, 'amount_type': 10, })
                instances += debit_note_serialized.data

    elif ac_head_code == "sundry_debtor_customer":
        sales = Sale.objects.none()
        orders = Orders.objects.none()
        credit_notes = CreditNoteVoucher.objects.none()
        customers = Customer.objects.filter(is_deleted=False)

        if is_sub_ledger:
            if customers.filter(pk=sub_ledger).exists():
                customer = customers.get(pk=sub_ledger)

                credit_notes = CreditNoteVoucher.objects.filter(is_deleted=False, customer=customer,warehouse__pk__in=warehouse_pk)
                sales = Sale.objects.filter(is_deleted=False, customer=customer,warehouse__pk__in=warehouse_pk).order_by('sale_date')
                orders = Orders.objects.filter(is_deleted=False, order_status='30', customer=customer,warehouse__pk__in=warehouse_pk).order_by('date_added')
        else:
            credit_notes = CreditNoteVoucher.objects.filter(is_deleted=False)
            sales = Sale.objects.filter(is_deleted=False,warehouse__pk__in=warehouse_pk).order_by('sale_date')
            orders = Orders.objects.filter(is_deleted=False, order_status='30',warehouse__pk__in=warehouse_pk).order_by('date_added')

        if sales.exists():
            if not financial_year:
                first_date = sales.first().sale_date.date()

            if sales.filter(sale_date__date__range=[first_date, date_range]).exists():
                previous_sales = sales.filter(sale_date__date__range=[first_date, date_range])

                previous_sales_dict = previous_sales.aggregate(Sum('total'), Sum('paid'))
                previous_sales_total = previous_sales_dict['total__sum']
                opening_balance += previous_sales_total

        if credit_notes.filter(transfer_type=30).exists():
            if not financial_year:
                first_date = credit_notes.filter(transfer_type=30).order_by('voucher_date').first().voucher_date.date()

            if credit_notes.filter(transfer_type=30, voucher_date__date__range=[first_date, date_range]).exists():
                prev_credit_notes = credit_notes.filter(transfer_type=30,voucher_date__date__range=[first_date, date_range]).aggregate(amount=Sum('amount'))
                credit_note_total_amount = prev_credit_notes.get('amount', 0)
                opening_balance -= credit_note_total_amount

        if orders.exists():
            if not financial_year:
                first_date = orders.first().date_added.date()

            if orders.filter(date_added__date__range=[first_date, date_range]).exists():
                previous_orders = orders.filter(date_added__date__range=[first_date, date_range])

                previous_orders_dict = previous_orders.aggregate(Sum('amount_payable'), Sum('paid_amount'))
                previous_orders_total = previous_orders_dict['amount_payable__sum']
                opening_balance += previous_orders_total

        closing_balance = opening_balance

        if sales.filter(sale_date__date__range=[from_date, to_date],warehouse__pk__in=warehouse_pk).exists():
            sales = sales.filter(sale_date__date__range=[from_date, to_date],warehouse__pk__in=warehouse_pk).order_by('sale_date')

            sales_dict = sales.aggregate(Sum('total'), Sum('paid'))
            sales_total = sales_dict['total__sum']
            closing_balance += sales_total

            if is_need_instances:
                serialized_sale_debit = SaleSerializer(sales, many=True, context={'amount_type': 20, 'head': head})
                instances += serialized_sale_debit.data

        if credit_notes.filter(voucher_date__date__range=[from_date, to_date]).exists():
            credit_notes = credit_notes.filter(voucher_date__date__range=[from_date, to_date])
            credit_note_data = credit_notes.aggregate(amount=Sum('amount'))
            credit_note_total_amount = credit_note_data.get('amount', 0)

            closing_balance -= credit_note_total_amount

            if is_need_instances:
                credit_note_serialized = CreditNoteVoucherSerializer(credit_notes, many=True,context={"head": head, 'amount_type': 10, })
                instances += credit_note_serialized.data

        if credit_notes.filter(voucher_date__date__range=[from_date, to_date]).exclude(transfer_type=30).exists():
            credit_notes = credit_notes.filter(voucher_date__date__range=[from_date, to_date]).exclude(transfer_type=30)
            credit_note_data = credit_notes.aggregate(amount=Sum('amount'))
            credit_note_total_amount = credit_note_data.get('amount', 0)

            closing_balance += credit_note_total_amount

            if is_need_instances:
                credit_note_serialized = CreditNoteVoucherSerializer(credit_notes, many=True,context={"head": head, 'amount_type': 20, })
                instances += credit_note_serialized.data

        if orders.filter(date_added__date__range=[from_date, to_date]).exists():
            orders = orders.filter(date_added__date__range=[from_date, to_date]).order_by('date_added')

            orders_dict = orders.aggregate(Sum('amount_payable'), Sum('paid_amount'))
            orders_total = orders_dict['amount_payable__sum']
            closing_balance += orders_total

            if is_need_instances:
                serialized_data = OrdersSerializer(orders, many=True, context={'head': head, 'amount_type': 20})
                instances += serialized_data.data

    elif ac_head_code == "sales_returns_account":
        credit_note_vouchers = CreditNoteVoucher.objects.none()

        if CreditNoteVoucher.objects.filter(is_deleted=False,warehouse__pk__in=warehouse_pk).exists():
            credit_note_vouchers = CreditNoteVoucher.objects.filter(is_deleted=False,warehouse__pk__in=warehouse_pk).order_by('voucher_date')
            if not financial_year:
                first_date = credit_note_vouchers.first().voucher_date.date()

            previous_credit_note_voucher = credit_note_vouchers.filter(voucher_date__date__range=[first_date, date_range])
            if previous_credit_note_voucher.exists():
                total_voucher_amount = previous_credit_note_voucher.aggregate(amount=Sum('amount')).get('amount', 0)
                opening_balance += total_voucher_amount

        closing_balance = opening_balance

        if credit_note_vouchers.filter(voucher_date__date__range=[from_date, to_date]).exists():
            total_voucher_amount = credit_note_vouchers.filter(voucher_date__date__range=[from_date, to_date]).aggregate(amount=Sum('amount')).get('amount', 0)
            closing_balance += total_voucher_amount

            if is_need_instances:
                credit_note_serialized = CreditNoteVoucherSerializer(credit_note_vouchers, many=True,context={"head": head, 'amount_type': 20, })
                instances += credit_note_serialized.data

    elif ac_head_code == "purchase_returns_account":
        debit_note_vouchers = DebitNoteVoucher.objects.none()

        if DebitNoteVoucher.objects.filter(is_deleted=False,warehouse__pk__in=warehouse_pk).exists():
            debit_note_vouchers = DebitNoteVoucher.objects.filter(is_deleted=False,warehouse__pk__in=warehouse_pk).order_by('voucher_date')
            if not financial_year:
                first_date = debit_note_vouchers.first().voucher_date.date()

            previous_debit_note_voucher = debit_note_vouchers.filter(voucher_date__date__range=[first_date, date_range])
            if previous_debit_note_voucher.exists():
                total_voucher_amount = previous_debit_note_voucher.aggregate(amount=Sum('amount')).get('amount', 0)
                opening_balance -= total_voucher_amount

        closing_balance = opening_balance

        if debit_note_vouchers.filter(voucher_date__date__range=[from_date, to_date]).exists():
            total_voucher_amount = debit_note_vouchers.filter(voucher_date__date__range=[from_date, to_date]).aggregate(amount=Sum('amount')).get('amount', 0)
            closing_balance -= total_voucher_amount

            if is_need_instances:
                debit_note_serialized = DebitNoteVoucherSerializer(debit_note_vouchers, many=True,context={"head": head, 'amount_type': 10, })
                instances += debit_note_serialized.data

    if current_payment_vouchers.exists():
        if is_need_instances:
            payment_serialized = PaymentVoucherSerializer(current_payment_vouchers, many=True, context={'head': head})
            instances += payment_serialized.data

        current_p_total = current_payment_vouchers.aggregate(amount=Sum('amount')).get('amount', 0)
        closing_balance += current_p_total

    if current_receipt_vouchers.exists():
        if is_need_instances:
            payment_serialized = ReceiptVoucherSerializer(current_receipt_vouchers, many=True, context={'head': head})
            instances += payment_serialized.data

        current_p_total = current_receipt_vouchers.aggregate(amount=Sum('amount')).get('amount', 0)
        closing_balance -= current_p_total

    if current_journal_voucher_items.exists():
        if is_need_instances:
            journal_items_serialized = JournalVoucherItemSerializer(current_journal_voucher_items, many=True,context={})
            instances += journal_items_serialized.data

        if current_journal_voucher_items.filter(amount_type=20).exists():
            current_j_debit_total = current_journal_voucher_items.filter(amount_type=20).aggregate(amount=Sum('amount')).get('amount', 0)
            closing_balance += current_j_debit_total

        if current_journal_voucher_items.filter(amount_type=10).exists():
            current_j_credit_total = current_journal_voucher_items.filter(amount_type=10).aggregate(amount=Sum('amount')).get('amount', 0)
            closing_balance -= current_j_credit_total

    if is_need_instances:
        data = {
            'instances': instances,
            'closing_balance': closing_balance,
            'opening_balance': opening_balance,
        }

    elif is_need_closing:
        data = {
            'debit_total': debit_total,
            'credit_total': credit_total,
            'opening_balance': opening_balance,
            'closing_balance': closing_balance,
        }

    return data
