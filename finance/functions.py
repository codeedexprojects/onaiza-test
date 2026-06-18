# import json
# import datetime
# from itertools import chain
# from operator import attrgetter, itemgetter
# from icecream import ic as printing
# # ------------------------
# from django.db.models import Q, F, Sum, Count
# from django.urls import reverse
# from django.shortcuts import render, get_object_or_404
# from django.contrib.auth.decorators import login_required
# from django.http.response import HttpResponse, HttpResponseRedirect
# from django.forms.models import inlineformset_factory, formset_factory
# from django.forms.widgets import Select, TextInput
# # ------------------------
# from finance.models import *
# from vendors.models import Vendor
# from customers.models import Customer
# from sales.models import Sale, SaleItem
# from sales.serializers import SaleSerializer, CustomerSaleSerializer
# from purchases.serializers import PurchaseSerializer, VendorPurchaseSerializer
# from purchases.models import Purchase
# from orders.models import Order, OrderItem
# from orders.serializers import OrderSerializer, CustomerOrderSerializer
# from .serializers import PaymentVoucherSerializer, ReceiptVoucherSerializer, JournalVoucherItemSerializer, CreditNoteVoucherSerializer, DebitNoteVoucherSerializer


# def get_ledger_data(head, from_date, to_date, sub_ledger, report='ledger'):
#     is_need_closing = False
#     is_need_instances = False

#     if report in ['ledger', 'day book']:
#         is_need_instances = True
#         instances = []

#     elif report in ['trial balance', 'current balance', 'profit and loss', 'balance sheet']:
#         is_need_closing = True

#     ac_head_name = head.name
#     date_range = from_date - datetime.timedelta(days=1)

#     data = {}
#     ac_opening = 0
#     debit_total = 0
#     credit_total = 0
#     opening_balance = 0
#     closing_balance = 0
#     ac_opening_type = ''
#     is_sub_ledger = False

#     if sub_ledger:
#         is_sub_ledger = True
#     else:
#         sub_ledger = ''

#     # set opening bal of subledger
#     financial_year = None
#     opening_debit_amount = 0
#     opening_credit_amount = 0
#     previous_payment_vouchers = PaymentVoucher.objects.none()
#     previous_receipt_vouchers = ReceiptVoucher.objects.none()

#     if FinancialYear.objects.filter(is_deleted=False,  is_active=True).exists():
#         financial_year = FinancialYear.objects.filter(is_deleted=False, is_active=True).last()
#         first_date = financial_year.start_date.date()

#         # checking if account head is in the list that can have subledger
#         if ac_head_name in ['Sundry Debtor', 'Sundry Creditor (Vendor)', 'Sundry Creditor (Delivery Agent)']:
#             if ac_head_name == 'Sundry Debtor':
#                 sub_ledger_type = 10
#             elif ac_head_name == 'Sundry Creditor (Vendor)':
#                 sub_ledger_type = 20
#             elif ac_head_name == 'Sundry Creditor (Delivery Agent)':
#                 sub_ledger_type = 30
#             else:
#                 sub_ledger_type = 0

#             if sub_ledger != '': # to take only chosen customer's opening balance
#                 if SubledgerOpening.objects.filter(financial_year__pk=financial_year.pk, sub_ledger_type=sub_ledger_type, is_deleted=False, sub_ledger=sub_ledger).exists():
#                     if SubledgerOpening.objects.filter(financial_year__pk=financial_year.pk, sub_ledger_type=sub_ledger_type, is_deleted=False, sub_ledger=sub_ledger, amount_type=20).exists():
#                         opening_debit_amount = SubledgerOpening.objects.filter(financial_year__pk=financial_year.pk, sub_ledger_type=sub_ledger_type, is_deleted=False, sub_ledger=sub_ledger, amount_type=20).last().amount
#                     if SubledgerOpening.objects.filter(financial_year__pk=financial_year.pk, sub_ledger_type=sub_ledger_type, is_deleted=False, sub_ledger=sub_ledger, amount_type=10).exists():
#                         opening_credit_amount = SubledgerOpening.objects.filter(financial_year__pk=financial_year.pk, sub_ledger_type=sub_ledger_type, is_deleted=False, sub_ledger=sub_ledger, amount_type=10).last().amount

#             else: # to take all customer's opening balance since no customer has been chosen
#                 is_sub_ledger = False
#                 if SubledgerOpening.objects.filter(financial_year__pk=financial_year.pk, sub_ledger_type=sub_ledger_type, is_deleted=False).exists():
#                     if SubledgerOpening.objects.filter(financial_year__pk=financial_year.pk, sub_ledger_type=sub_ledger_type, is_deleted=False, amount_type=20).exists():
#                         opening_debit_amount = SubledgerOpening.objects.filter(financial_year__pk=financial_year.pk, sub_ledger_type=sub_ledger_type, is_deleted=False, amount_type=20).aggregate(amount=Sum('amount')).get('amount', 0)
#                     if SubledgerOpening.objects.filter(financial_year__pk=financial_year.pk, sub_ledger_type=sub_ledger_type, is_deleted=False, amount_type=10).exists():
#                         opening_credit_amount = SubledgerOpening.objects.filter(financial_year__pk=financial_year.pk, sub_ledger_type=sub_ledger_type, is_deleted=False, amount_type=10).aggregate(amount=Sum('amount')).get('amount', 0)
#         else:
#             is_sub_ledger = False
#             # get opening balance of account head which won't have subledger

#             # if FinancialAccountOpening.objects.filter(financial_year__pk=financial_year.pk, is_deleted=False, account_head=head).exists():
#             #     if FinancialAccountOpening.objects.filter(financial_year__pk=financial_year.pk, is_deleted=False, account_head=head, amount_type=20).exists():
#             #         opening_debit_amount = FinancialAccountOpening.objects.filter(financial_year__pk=financial_year.pk, is_deleted=False, account_head=head, amount_type=20).last().amount
#             #     if FinancialAccountOpening.objects.filter(financial_year__pk=financial_year.pk, is_deleted=False, account_head=head, amount_type=10).exists():
#             #         opening_credit_amount = FinancialAccountOpening.objects.filter(financial_year__pk=financial_year.pk, is_deleted=False,account_head=head, amount_type=10).last().amount

#     opening_balance -= opening_credit_amount
#     opening_balance += opening_debit_amount

#     credit_total += opening_credit_amount
#     debit_total += opening_debit_amount

#     if is_sub_ledger:
#         payment_vouchers = PaymentVoucher.objects.filter(is_deleted=False, sub_ledger=sub_ledger, account_head=head).order_by('voucher_date')
#         receipt_vouchers = ReceiptVoucher.objects.filter(is_deleted=False, sub_ledger=sub_ledger, account_head=head).order_by('voucher_date')
#         journal_voucher_items = JournalVoucherItem.objects.filter(journal__is_deleted=False, sub_ledger=sub_ledger, account_head=head).order_by('journal__voucher_date')

#     else:
#         payment_vouchers = PaymentVoucher.objects.filter(is_deleted=False, account_head=head).order_by('voucher_date')
#         receipt_vouchers = ReceiptVoucher.objects.filter(is_deleted=False, account_head=head).order_by('voucher_date')
#         journal_voucher_items = JournalVoucherItem.objects.filter(journal__is_deleted=False, account_head=head).order_by('journal__voucher_date')

#         # cash_opening_balance = head.opening_balance

#         # if head.opening_balance_type == 20:
#         #     opening_balance -= cash_opening_balance
#         # elif head.opening_balance_type == 10:
#         #     opening_balance += cash_opening_balance

#     # if ac_head_name != 'Cash A/C' and head.bank == None:
#     # opening balance calculations of all vouchers

#     if payment_vouchers.exists():
#         if not financial_year:
#             first_date = payment_vouchers.first().voucher_date.date()
#         previous_payment_voucher = payment_vouchers.filter(voucher_date__date__range=[first_date, date_range])

#         if previous_payment_voucher.exists():
#             previous_amount = previous_payment_voucher.aggregate(amount=Sum('amount')).get('amount', 0)
#             opening_balance += previous_amount
#             debit_total += previous_amount

#     if receipt_vouchers.exists():
#         if not financial_year:
#             first_date = receipt_vouchers.first().voucher_date.date()
#         previous_receipt_voucher = receipt_vouchers.filter(voucher_date__date__range=[first_date, date_range])

#         if previous_receipt_voucher.exists():
#             previous_amount = previous_receipt_voucher.aggregate(amount=Sum('amount')).get('amount', 0)
#             opening_balance -= previous_amount
#             credit_total += previous_amount

#     if journal_voucher_items.exists():
#         if not financial_year:
#             first_date = journal_voucher_items.first().journal.voucher_date.date()
#         previous_journal_voucher_items = journal_voucher_items.filter(journal__voucher_date__date__range=[first_date, date_range])

#         if previous_journal_voucher_items.exists():
#             if previous_journal_voucher_items.filter(amount_type=20).exists():
#                 previous_debit_amount = previous_journal_voucher_items.filter(amount_type=20).aggregate(amount=Sum('amount')).get('amount', 0)
#                 opening_balance += previous_debit_amount

#             if previous_journal_voucher_items.filter(amount_type=10).exists():
#                 previous_credit_amount = previous_journal_voucher_items.filter(amount_type=10).aggregate(amount=Sum('amount')).get('amount', 0)
#                 opening_balance -= previous_credit_amount

#     # Opening Balance of vouchers calculations ends here

#     # vouchers on period
#     current_payment_vouchers = payment_vouchers.filter(amount__gt=0, voucher_date__date__range=[from_date, to_date])
#     current_receipt_vouchers = receipt_vouchers.filter(amount__gt=0, voucher_date__date__range=[from_date, to_date])
#     current_journal_voucher_items = journal_voucher_items.filter(amount__gt=0, journal__voucher_date__date__range=[from_date, to_date])

#     closing_balance = opening_balance

#     if head.bank:
#         payment_vouchers = PaymentVoucher.objects.filter(transfer_type__in=[15, 20, 25], bank=head.bank, is_deleted=False).order_by('voucher_date')
#         receipt_vouchers = ReceiptVoucher.objects.filter(transfer_type__in=[15, 20, 25], bank=head.bank, is_deleted=False).order_by('voucher_date')
#         credit_note_vouchers = CreditNoteVoucher.objects.filter(transfer_type__in=[15, 20, 25], bank=head.bank, is_deleted=False).order_by('voucher_date')
#         debit_note_vouchers = DebitNoteVoucher.objects.filter(transfer_type__in=[15, 20, 25], bank=head.bank, is_deleted=False).order_by('voucher_date')

#         payment_vouchers_from_bank = PaymentVoucher.objects.filter(account_head=head, is_deleted=False).order_by('voucher_date')
#         receipt_vouchers_from_bank = ReceiptVoucher.objects.filter(account_head=head, is_deleted=False).order_by('voucher_date')
#         payment_vouchers_from_cash = payment_vouchers_from_bank.none()
#         receipt_vouchers_from_cash = receipt_vouchers_from_bank.none()
#         # opening balance calculations of all vouchers
#         if payment_vouchers:
#             if not financial_year:
#                 first_date = payment_vouchers.first().voucher_date.date()

#             previous_payment_voucher = payment_vouchers.filter(voucher_date__date__range=[first_date, date_range])
#             if previous_payment_voucher.exists():
#                 total_voucher_amount = previous_payment_voucher.aggregate(amount=Sum('amount')).get('amount', 0)
#                 opening_balance -= total_voucher_amount

#         if receipt_vouchers:
#             if not financial_year:
#                 first_date = receipt_vouchers.first().voucher_date.date()

#             previous_receipt_voucher = receipt_vouchers.filter(voucher_date__date__range=[first_date, date_range])
#             if previous_receipt_voucher.exists():
#                 total_voucher_amount = previous_receipt_voucher.aggregate(amount=Sum('amount')).get('amount', 0)
#                 opening_balance += total_voucher_amount

#         if receipt_vouchers_from_bank:
#             if not financial_year:
#                 first_date = receipt_vouchers_from_bank.first().voucher_date.date()

#             previous_bank_receipt_vouchers = receipt_vouchers_from_bank.filter(voucher_date__date__range=[first_date, date_range])
#             if previous_bank_receipt_vouchers.exists():
#                 total_voucher_amount = previous_bank_receipt_vouchers.aggregate(amount=Sum('amount')).get('amount', 0)
#                 opening_balance -= total_voucher_amount

#         if payment_vouchers_from_bank:
#             if not financial_year:
#                 first_date = payment_vouchers_from_bank.first().voucher_date.date()

#             previous_bank_payment_vouchers = payment_vouchers_from_bank.filter(voucher_date__date__range=[first_date, date_range])
#             if previous_bank_payment_vouchers.exists():
#                 total_voucher_amount = previous_bank_payment_vouchers.aggregate(amount=Sum('amount')).get('amount', 0)
#                 opening_balance += total_voucher_amount

#         if credit_note_vouchers:
#             if not financial_year:
#                 first_date = credit_note_vouchers.first().voucher_date.date()

#             previous_credit_note_voucher = credit_note_vouchers.filter(voucher_date__date__range=[first_date, date_range])
#             if previous_credit_note_voucher.exists():
#                 total_voucher_amount = previous_credit_note_voucher.aggregate(amount=Sum('amount')).get('amount', 0)
#                 opening_balance -= total_voucher_amount

#         if debit_note_vouchers:
#             if not financial_year:
#                 first_date = debit_note_vouchers.first().voucher_date.date()

#             previous_debit_note_voucher = debit_note_vouchers.filter(voucher_date__date__range=[first_date, date_range])
#             if previous_debit_note_voucher.exists():
#                 total_voucher_amount = previous_debit_note_voucher.aggregate(amount=Sum('amount')).get('amount', 0)
#                 opening_balance += total_voucher_amount

#         payment_vouchers = payment_vouchers.filter(voucher_date__date__range=[from_date, to_date])
#         receipt_vouchers = receipt_vouchers.filter(voucher_date__date__range=[from_date, to_date])
#         payment_vouchers_from_bank = payment_vouchers_from_bank.filter(voucher_date__date__range=[from_date, to_date])
#         receipt_vouchers_from_bank = receipt_vouchers_from_bank.filter(voucher_date__date__range=[from_date, to_date])
#         debit_note_vouchers = debit_note_vouchers.filter(voucher_date__date__range=[from_date, to_date])
#         credit_note_vouchers = credit_note_vouchers.filter(voucher_date__date__range=[from_date, to_date])
#         # Opening Balance calculations ends here

#         closing_balance = opening_balance

#         if payment_vouchers.exists():
#             total_voucher_amount = payment_vouchers.aggregate(amount=Sum('amount')).get('amount', 0)
#             closing_balance -= total_voucher_amount

#         if receipt_vouchers.exists():
#             total_voucher_amount = receipt_vouchers.aggregate(amount=Sum('amount')).get('amount', 0)
#             closing_balance += total_voucher_amount

#         if payment_vouchers_from_bank.exists():
#             total_voucher_amount = payment_vouchers_from_bank.aggregate(amount=Sum('amount')).get('amount', 0)
#             closing_balance += total_voucher_amount

#         if receipt_vouchers_from_bank.exists():
#             total_voucher_amount = receipt_vouchers_from_bank.aggregate(amount=Sum('amount')).get('amount', 0)
#             closing_balance -= total_voucher_amount

#         if credit_note_vouchers.exists():
#             total_voucher_amount = credit_note_vouchers.aggregate(amount=Sum('amount')).get('amount', 0)
#             closing_balance -= total_voucher_amount

#         if debit_note_vouchers.exists():
#             total_voucher_amount = debit_note_vouchers.aggregate(amount=Sum('amount')).get('amount', 0)
#             closing_balance += total_voucher_amount

#         if is_need_instances:
#             payment_serialized = PaymentVoucherSerializer(payment_vouchers, many=True, context={"head": head, 'amount_type': 10, })
#             instances += payment_serialized.data

#             receipt_serialized = ReceiptVoucherSerializer(receipt_vouchers, many=True, context={"head": head, 'amount_type': 20, })
#             instances += receipt_serialized.data

#             payment_from_bank_serialized = PaymentVoucherSerializer(payment_vouchers_from_bank, many=True, context={"head": head, 'amount_type': 20, })
#             instances += payment_from_bank_serialized.data

#             receipt_from_bank_serialized = ReceiptVoucherSerializer(receipt_vouchers_from_bank, many=True, context={"head": head, 'amount_type': 10, })
#             instances += receipt_from_bank_serialized.data

#             credit_note_serialized = CreditNoteVoucherSerializer(credit_note_vouchers, many=True, context={"head": head, 'amount_type': 10, })
#             instances += credit_note_serialized.data

#             debit_note_serialized = DebitNoteVoucherSerializer(debit_note_vouchers, many=True, context={"head": head, 'amount_type': 20, })
#             instances += debit_note_serialized.data

#     elif ac_head_name == 'Cash A/C':
#         payment_vouchers = PaymentVoucher.objects.filter(transfer_type=10, is_deleted=False).order_by('voucher_date')
#         receipt_vouchers = ReceiptVoucher.objects.filter(transfer_type=10, is_deleted=False).order_by('voucher_date')
#         debit_note_vouchers = DebitNoteVoucher.objects.filter(transfer_type=10, is_deleted=False).order_by('voucher_date')
#         credit_note_vouchers = CreditNoteVoucher.objects.filter(transfer_type=10, is_deleted=False).order_by('voucher_date')

#         payment_vouchers_from_cash = PaymentVoucher.objects.filter(account_head=head, is_deleted=False).order_by('voucher_date')
#         receipt_vouchers_from_cash = ReceiptVoucher.objects.filter(account_head=head, is_deleted=False).order_by('voucher_date')
#         payment_vouchers_from_cash = payment_vouchers_from_cash.none()
#         receipt_vouchers_from_cash = receipt_vouchers_from_cash.none()

#         # opening balance calculations of all vouchers
#         if payment_vouchers:
#             if not financial_year:
#                 first_date = payment_vouchers.first().voucher_date.date()

#             previous_payment_voucher = payment_vouchers.filter(voucher_date__date__range=[first_date, date_range])
#             if previous_payment_voucher.exists():
#                 total_voucher_amount = previous_payment_voucher.aggregate(amount=Sum('amount')).get('amount', 0)
#                 opening_balance -= total_voucher_amount

#         if receipt_vouchers:
#             if not financial_year:
#                 first_date = receipt_vouchers.first().voucher_date.date()

#             previous_receipt_voucher = receipt_vouchers.filter(voucher_date__date__range=[first_date, date_range])
#             if previous_receipt_voucher.exists():
#                 total_voucher_amount = previous_receipt_voucher.aggregate(amount=Sum('amount')).get('amount', 0)
#                 opening_balance += total_voucher_amount

#         if credit_note_vouchers:
#             if not financial_year:
#                 first_date = credit_note_vouchers.first().voucher_date.date()

#             previous_credit_note_voucher = credit_note_vouchers.filter(voucher_date__date__range=[first_date, date_range])
#             if previous_credit_note_voucher.exists():
#                 total_voucher_amount = previous_credit_note_voucher.aggregate(amount=Sum('amount')).get('amount', 0)
#                 opening_balance -= total_voucher_amount

#         if debit_note_vouchers:
#             if not financial_year:
#                 first_date = debit_note_vouchers.first().voucher_date.date()

#             previous_debit_note_voucher = debit_note_vouchers.filter(voucher_date__date__range=[first_date, date_range])
#             if previous_debit_note_voucher.exists():
#                 total_voucher_amount = previous_debit_note_voucher.aggregate(amount=Sum('amount')).get('amount', 0)
#                 opening_balance += total_voucher_amount

#         if receipt_vouchers_from_cash.exists():
#             if not financial_year:
#                 first_date = receipt_vouchers_from_cash.first().voucher_date.date()

#             previous_bank_receipt_vouchers = receipt_vouchers_from_cash.filter(voucher_date__date__range=[first_date, date_range])
#             if previous_bank_receipt_vouchers.exists():
#                 total_voucher_amount = previous_bank_receipt_vouchers.aggregate(amount=Sum('amount')).get('amount', 0)
#                 opening_balance -= total_voucher_amount

#         if payment_vouchers_from_cash.exists():
#             if not financial_year:
#                 first_date = payment_vouchers_from_cash.first().voucher_date.date()

#             previous_bank_payment_vouchers = payment_vouchers_from_cash.filter(voucher_date__date__range=[first_date, date_range])
#             if previous_bank_payment_vouchers.exists():
#                 total_voucher_amount = previous_bank_payment_vouchers.aggregate(amount=Sum('amount')).get('amount', 0)
#                 opening_balance += total_voucher_amount

#         payment_vouchers = payment_vouchers.filter(voucher_date__date__range=[from_date, to_date])
#         receipt_vouchers = receipt_vouchers.filter(voucher_date__date__range=[from_date, to_date])
#         debit_note_vouchers = debit_note_vouchers.filter(voucher_date__date__range=[from_date, to_date])
#         credit_note_vouchers = credit_note_vouchers.filter(voucher_date__date__range=[from_date, to_date])
#         payment_vouchers_from_cash = payment_vouchers_from_cash.filter(voucher_date__date__range=[from_date, to_date])
#         receipt_vouchers_from_cash = receipt_vouchers_from_cash.filter(voucher_date__date__range=[from_date, to_date])
#         # Opening Balance calculations ends here

#         closing_balance = opening_balance

#         if payment_vouchers.exists():
#             total_voucher_amount = payment_vouchers.aggregate(amount=Sum('amount')).get('amount', 0)
#             closing_balance -= total_voucher_amount

#         if receipt_vouchers.exists():
#             total_voucher_amount = receipt_vouchers.aggregate(amount=Sum('amount')).get('amount', 0)
#             closing_balance += total_voucher_amount

#         if payment_vouchers_from_cash.exists():
#             total_voucher_amount = payment_vouchers_from_cash.aggregate(amount=Sum('amount')).get('amount', 0)
#             closing_balance += total_voucher_amount

#         if receipt_vouchers_from_cash.exists():
#             total_voucher_amount = receipt_vouchers_from_cash.aggregate(amount=Sum('amount')).get('amount', 0)
#             closing_balance -= total_voucher_amount

#         if credit_note_vouchers.exists():
#             total_voucher_amount = credit_note_vouchers.aggregate(amount=Sum('amount')).get('amount', 0)
#             closing_balance -= total_voucher_amount

#         if debit_note_vouchers.exists():
#             total_voucher_amount = debit_note_vouchers.aggregate(amount=Sum('amount')).get('amount', 0)
#             closing_balance += total_voucher_amount

#         if is_need_instances:
#             payment_serialized = PaymentVoucherSerializer(payment_vouchers, many=True, context={"head": head, 'amount_type': 10, })
#             instances += payment_serialized.data
#             receipt_serialized = ReceiptVoucherSerializer(receipt_vouchers, many=True, context={"head": head, 'amount_type': 20, })
#             instances += receipt_serialized.data
#             credit_note_serialized = CreditNoteVoucherSerializer(credit_note_vouchers, many=True, context={"head": head, 'amount_type': 10, })
#             instances += credit_note_serialized.data
#             debit_note_serialized = DebitNoteVoucherSerializer(debit_note_vouchers, many=True, context={"head": head, 'amount_type': 20, })
#             instances += debit_note_serialized.data

#             payment_from_cash_serialized = PaymentVoucherSerializer(payment_vouchers_from_cash, many=True, context={"head": head, 'amount_type': 20, })
#             instances += payment_from_cash_serialized.data

#             receipt_from_cash_serialized = ReceiptVoucherSerializer(receipt_vouchers_from_cash, many=True, context={"head": head, 'amount_type': 10, })
#             instances += receipt_from_cash_serialized.data

#     elif ac_head_name == 'Purchases':
#         if Purchase.objects.filter(is_deleted=False).exists():
#             purchases = Purchase.objects.filter(is_deleted=False).order_by('date')
#             if not financial_year:
#                 first_date = purchases.first().date.date()

#             if purchases.filter(date__date__range=[first_date, date_range]).exists():
#                 previous_purchases = purchases.filter(date__date__range=[first_date, date_range])
#                 previous_purchase_pks = map(str, previous_purchases.values_list('pk', flat=True))

#                 total_voucher_amount = 0
#                 p_vouchers = PaymentVoucher.objects.filter(sub_ledger__in=previous_purchase_pks, account_head=head)
#                 if p_vouchers.exists():
#                     total_voucher_amount = p_vouchers.aggregate(amount=Sum('amount')).get('amount', 0)
#                     opening_balance -= total_voucher_amount

#                 total_purchase_amount = previous_purchases.aggregate(subtotal=Sum('subtotal')).get('subtotal', 0)

#                 opening_balance += total_purchase_amount

#         closing_balance = opening_balance

#         if Purchase.objects.filter(is_deleted=False,  date__date__range=[from_date, to_date]).exists():
#             purchases = Purchase.objects.filter(is_deleted=False,  date__date__range=[from_date, to_date])

#             purchase_total = purchases.aggregate(subtotal=Sum('subtotal')).get('subtotal', 0)
#             closing_balance += purchase_total

#             if is_need_instances:
#                 # Serialized purchase items to array
#                 serialized_data = PurchaseSerializer(purchases, many=True, context={'head': head})
#                 instances += serialized_data.data

#             purchase_pks = map(str, purchases.values_list('pk', flat=True))
#             p_voucher_pks = PaymentVoucher.objects.filter(sub_ledger__in=purchase_pks, account_head=head).values_list('pk', flat=True)
#             current_payment_vouchers = current_payment_vouchers.exclude(pk__in=p_voucher_pks)

#     elif ac_head_name == 'Sales A/C':
#         if Sale.objects.filter(is_deleted=False).exists():
#             sales = Sale.objects.filter(is_deleted=False).order_by('sale_date')
#             if not financial_year:
#                 first_date = sales.first().sale_date

#             if sales.filter(is_deleted=False, sale_date__date__range=[first_date, date_range]).exists():
#                 previous_sales = sales.filter(is_deleted=False, sale_date__date__range=[first_date, date_range])
#                 previous_sale_pks = map(str, previous_sales.values_list('pk', flat=True))

#                 total_sale_amount = previous_sales.aggregate(total=Sum('total')).get('total', 0)
#                 opening_balance -= total_sale_amount

#                 r_vouchers = ReceiptVoucher.objects.filter(is_deleted=False, sub_ledger__in=previous_sale_pks, account_head=head)

#                 if r_vouchers.exists():
#                     total_voucher_amount = r_vouchers.aggregate(amount=Sum('amount')).get('amount', 0)
#                     opening_balance += total_voucher_amount

#         closing_balance = opening_balance

#         if Sale.objects.filter(is_deleted=False, sale_date__date__range=[from_date, to_date]).exists():
#             sales = Sale.objects.filter(is_deleted=False, sale_date__date__range=[from_date, to_date])

#             sale_total = sales.aggregate(total=Sum('total')).get('total', 0)
#             closing_balance -= sale_total

#             if is_need_instances:
#                 # Serialized sale items to array
#                 serialized_data = SaleSerializer(sales, many=True, context={'head': head})
#                 instances += serialized_data.data

#             sale_pks = map(str, sales.values_list('pk', flat=True))
#             r_voucher_pks = ReceiptVoucher.objects.filter(is_deleted=False, sub_ledger__in=sale_pks, account_head=head).values_list('pk', flat=True)
#             current_receipt_vouchers = current_receipt_vouchers.exclude(pk__in=r_voucher_pks)

#     elif ac_head_name == 'Online Sales':

#         if Order.objects.filter(is_deleted=False, order_status='delivered').exists():
#             orders = Order.objects.filter(is_deleted=False, order_status='delivered').order_by('date_added')
#             if not financial_year:
#                 first_date = orders.first().date_added.date()

#             if orders.filter(date_added__date__range=[first_date, date_range]).exists():
#                 previous_orders = orders.filter(date_added__date__range=[first_date, date_range])
#                 previous_order_pks = map(str, previous_orders.values_list('pk', flat=True))

#                 total_order_amount = previous_orders.aggregate(amount_payable=Sum('amount_payable')).get('amount_payable', 0)
#                 opening_balance -= total_order_amount

#                 r_vouchers = ReceiptVoucher.objects.filter(sub_ledger__in=previous_order_pks, account_head=head)

#                 if r_vouchers.exists():
#                     total_voucher_amount = r_vouchers.aggregate(amount=Sum('amount')).get('amount', 0)
#                     opening_balance += total_voucher_amount

#         closing_balance = opening_balance

#         if Order.objects.filter(is_deleted=False, order_status='delivered', date_added__date__range=[from_date, to_date]).exists():
#             orders = Order.objects.filter(is_deleted=False, order_status='delivered', date_added__date__range=[from_date, to_date])

#             order_total = orders.aggregate(amount_payable=Sum('amount_payable')).get('amount_payable', 0)
#             closing_balance -= order_total

#             if is_need_instances:
#                 # Serialized order items to array
#                 serialized_data = OrderSerializer(orders, many=True, context={'head': head})
#                 instances += serialized_data.data

#             order_pks = map(str, orders.values_list('pk', flat=True))
#             r_voucher_pks = ReceiptVoucher.objects.filter(sub_ledger__in=order_pks, account_head=head).values_list('pk', flat=True)
#             current_receipt_vouchers = current_receipt_vouchers.exclude(pk__in=r_voucher_pks)

#     elif ac_head_name == "Sundry Creditor (Vendor)":
#         purchases = Purchase.objects.none()
#         vendors = Vendor.objects.filter(is_deleted=False)
#         debit_notes = DebitNoteVoucher.objects.none()

#         if is_sub_ledger:
#             if vendors.filter(pk=sub_ledger).exists():
#                 vendor = vendors.get(pk=sub_ledger)
#                 debit_notes = DebitNoteVoucher.objects.filter(vendor=vendor, is_deleted=False)

#                 if Purchase.objects.filter(is_deleted=False, vendor=vendor).exists():
#                     purchases = Purchase.objects.filter(is_deleted=False, vendor=vendor).order_by('date')
#         else:
#             debit_notes = DebitNoteVoucher.objects.filter(is_deleted=False)

#             if Purchase.objects.filter(is_deleted=False).exists():
#                 purchases = Purchase.objects.filter(is_deleted=False).order_by('date')

#         if purchases:
#             if not financial_year:
#                 first_date = purchases.first().date.date()

#             if purchases.filter(date__date__range=[first_date, date_range]).exists():
#                 previous_purchases = purchases.filter(date__date__range=[first_date, date_range])

#                 previous_purchases_dict = previous_purchases.aggregate(Sum('subtotal'), Sum('paid'))
#                 previous_purchases_paid = previous_purchases_dict['paid__sum']
#                 previous_purchases_total = previous_purchases_dict['subtotal__sum']

#                 previous_purchases_balance = previous_purchases_total - previous_purchases_paid
#                 opening_balance -= previous_purchases_balance

#         if debit_notes.filter(transfer_type=30).exists():
#             if not financial_year:
#                 first_date = debit_notes.filter(transfer_type=30).order_by('voucher_date').first().voucher_date.date()
#             if debit_notes.filter(transfer_type=30, voucher_date__date__range=[first_date, date_range]).exists():
#                 prev_debit_notes = debit_notes.filter(transfer_type=30, voucher_date__date__range=[first_date, date_range]).aggregate(amount=Sum('amount'))
#                 # debit_note_total_payable = prev_debit_notes.get('payable_amount', 0)
#                 debit_note_total_amount = prev_debit_notes.get('amount', 0)
#                 # opening_balance += debit_note_total_payable
#                 opening_balance += debit_note_total_amount

#         closing_balance = opening_balance

#         if purchases.filter(date__date__range=[from_date, to_date]).exists():
#             purchases = purchases.filter(date__date__range=[from_date, to_date]).order_by('date')

#             purchases_dict = purchases.aggregate(Sum('subtotal'), Sum('paid'))
#             purchases_paid = purchases_dict['paid__sum']
#             purchases_total = purchases_dict['subtotal__sum']

#             purchases_balance = purchases_total - purchases_paid
#             closing_balance -= purchases_balance

#             if is_need_instances:
#                 serialized_purchase_debit = VendorPurchaseSerializer(purchases, many=True, context={'amount_type': 20, 'head': head})
#                 serialized_purchase_credit = VendorPurchaseSerializer(purchases, many=True, context={'amount_type': 10, 'head': head})

#                 instances += serialized_purchase_debit.data
#                 instances += serialized_purchase_credit.data

#         if debit_notes.filter(voucher_date__date__range=[from_date, to_date]).exists():
#             debit_notes = debit_notes.filter(voucher_date__date__range=[from_date, to_date])
#             debit_note_data = debit_notes.aggregate(amount=Sum('amount'))
#             debit_note_total_amount = debit_note_data.get('amount', 0)

#             closing_balance += debit_note_total_amount

#             if is_need_instances:
#                 debit_note_serialized = DebitNoteVoucherSerializer(debit_notes, many=True, context={"head": head, 'amount_type': 20, })
#                 instances += debit_note_serialized.data

#         if debit_notes.filter(voucher_date__date__range=[from_date, to_date]).exclude(transfer_type=30).exists():
#             debit_notes = debit_notes.filter(voucher_date__date__range=[from_date, to_date]).exclude(transfer_type=30)
#             debit_note_data = debit_notes.aggregate(amount=Sum('amount'))
#             debit_note_total_amount = debit_note_data.get('amount', 0)

#             closing_balance -= debit_note_total_amount

#             if is_need_instances:
#                 debit_note_serialized = DebitNoteVoucherSerializer(debit_notes, many=True, context={"head": head, 'amount_type': 10, })
#                 instances += debit_note_serialized.data

#     elif ac_head_name == "Sundry Debtor":
#         sales = Sale.objects.none()
#         orders = Order.objects.none()
#         credit_notes = CreditNoteVoucher.objects.none()
#         customers = Customer.objects.filter(is_deleted=False)

#         if is_sub_ledger:
#             if customers.filter(pk=sub_ledger).exists():
#                 customer = customers.get(pk=sub_ledger)

#                 credit_notes = CreditNoteVoucher.objects.filter(is_deleted=False, customer=customer)
#                 sales = Sale.objects.filter(is_deleted=False, customer=customer).order_by('sale_date')
#                 orders = Order.objects.filter(is_deleted=False, order_status='delivered', customer=customer).order_by('date_added')
#         else:
#             credit_notes = CreditNoteVoucher.objects.filter(is_deleted=False)
#             sales = Sale.objects.filter(is_deleted=False).order_by('sale_date')
#             orders = Order.objects.filter(is_deleted=False, order_status='delivered').order_by('date_added')

#         if sales:
#             if not financial_year:
#                 first_date = sales.first().sale_date.date()

#             if sales.filter(sale_date__date__range=[first_date, date_range]).exists():
#                 previous_sales = sales.filter(sale_date__date__range=[first_date, date_range])

#                 previous_sales_dict = previous_sales.aggregate(Sum('total'), Sum('paid'))
#                 previous_sales_paid = previous_sales_dict['paid__sum']
#                 previous_sales_total = previous_sales_dict['total__sum']

#                 previous_sales_balance = previous_sales_total - previous_sales_paid
#                 opening_balance += previous_sales_balance

#         if credit_notes.filter(transfer_type=30).exists():
#             if not financial_year:
#                 first_date = credit_notes.filter(transfer_type=30).order_by('voucher_date').first().voucher_date.date()

#             if credit_notes.filter(transfer_type=30, voucher_date__date__range=[first_date, date_range]).exists():
#                 prev_credit_notes = credit_notes.filter(transfer_type=30, voucher_date__date__range=[first_date, date_range]).aggregate(amount=Sum('amount'))
#                 credit_note_total_amount = prev_credit_notes.get('amount', 0)
#                 opening_balance -= credit_note_total_amount

#         if orders:
#             if not financial_year:
#                 first_date = orders.first().date_added.date()

#             if orders.filter(date_added__date__range=[first_date, date_range]).exists():
#                 previous_orders = orders.filter(date_added__date__range=[first_date, date_range])
#                 previous_orders_dict = previous_orders.aggregate(Sum('amount_payable'), Sum('paid_amount'))
#                 previous_orders_total = previous_orders_dict['amount_payable__sum']
#                 previous_paid_amount = previous_orders_dict['paid_amount__sum']

#                 opening_balance += previous_orders_total
#                 opening_balance -= previous_paid_amount

#         closing_balance = opening_balance

#         if sales.filter(sale_date__date__range=[from_date, to_date]).exists():
#             sales = sales.filter(sale_date__date__range=[from_date, to_date]).order_by('sale_date')

#             sales_dict = sales.aggregate(Sum('total'), Sum('paid'))
#             sales_paid = sales_dict['paid__sum']
#             sales_total = sales_dict['total__sum']

#             sales_balance = sales_total - sales_paid
#             closing_balance += sales_balance

#             if is_need_instances:
#                 serialized_sale_debit = CustomerSaleSerializer(sales, many=True, context={'amount_type': 20, 'head': head})
#                 serialized_sale_credit = CustomerSaleSerializer(sales.filter(paid__gt=0), many=True, context={'amount_type': 10, 'head': head})

#                 instances += serialized_sale_debit.data
#                 instances += serialized_sale_credit.data

#         if credit_notes.filter(voucher_date__date__range=[from_date, to_date]).exists():
#             credit_notes = credit_notes.filter(voucher_date__date__range=[from_date, to_date])
#             credit_note_data = credit_notes.aggregate(amount=Sum('amount'))
#             credit_note_total_amount = credit_note_data.get('amount', 0)

#             closing_balance -= credit_note_total_amount

#             if is_need_instances:
#                 credit_note_serialized = CreditNoteVoucherSerializer(credit_notes, many=True, context={"head": head, 'amount_type': 10, })
#                 instances += credit_note_serialized.data

#         if credit_notes.filter(voucher_date__date__range=[from_date, to_date]).exclude(transfer_type=30).exists():
#             credit_notes = credit_notes.filter(voucher_date__date__range=[from_date, to_date]).exclude(transfer_type=30)
#             credit_note_data = credit_notes.aggregate(amount=Sum('amount'))
#             credit_note_total_amount = credit_note_data.get('amount', 0)

#             closing_balance += credit_note_total_amount

#             if is_need_instances:
#                 credit_note_serialized = CreditNoteVoucherSerializer(credit_notes, many=True, context={"head": head, 'amount_type': 20, })
#                 instances += credit_note_serialized.data

#         if orders.filter(date_added__date__range=[from_date, to_date]).exists():
#             orders = orders.filter(date_added__date__range=[from_date, to_date]).order_by('date_added')

#             orders_dict = orders.aggregate(Sum('amount_payable'), Sum('paid_amount'))
#             orders_total = orders_dict['amount_payable__sum']
#             total_paid = orders_dict['paid_amount__sum']

#             # closing_balance -= orders_total
#             orders_balance = orders_total - total_paid
#             closing_balance += orders_balance

#             if is_need_instances:
#                 serialized_order_debit = CustomerOrderSerializer(orders, many=True, context={'amount_type': 20, 'head': head})
#                 instances += serialized_order_debit.data

#                 serialized_order_credit = CustomerOrderSerializer(orders.filter(paid_amount__gt=0), many=True, context={'amount_type': 10, 'head': head})
#                 instances += serialized_order_credit.data

#                 # serialized_order_credit = CustomerOrderSerializer(orders, many=True, context={'amount_type': 10, 'head': head})
#                 # instances += serialized_order_credit.data

#     elif ac_head_name == "Sale Returns A/C":
#         credit_note_vouchers = CreditNoteVoucher.objects.none()

#         if CreditNoteVoucher.objects.filter(is_deleted=False).exists():
#             credit_note_vouchers = CreditNoteVoucher.objects.filter(is_deleted=False).order_by('voucher_date')
#             if not financial_year:
#                 first_date = credit_note_vouchers.first().voucher_date.date()

#             previous_credit_note_voucher = credit_note_vouchers.filter(voucher_date__date__range=[first_date, date_range])
#             if previous_credit_note_voucher.exists():
#                 total_voucher_amount = previous_credit_note_voucher.aggregate(amount=Sum('amount')).get('amount', 0)
#                 opening_balance += total_voucher_amount

#         closing_balance = opening_balance

#         if credit_note_vouchers.filter(voucher_date__date__range=[from_date, to_date]).exists():
#             total_voucher_amount = credit_note_vouchers.filter(voucher_date__date__range=[from_date, to_date]).aggregate(amount=Sum('amount')).get('amount', 0)
#             closing_balance += total_voucher_amount

#             if is_need_instances:
#                 credit_note_serialized = CreditNoteVoucherSerializer(credit_note_vouchers, many=True, context={"head": head, 'amount_type': 20, })
#                 instances += credit_note_serialized.data

#     elif ac_head_name == "Purchase Returns A/C":
#         debit_note_vouchers = DebitNoteVoucher.objects.none()

#         if DebitNoteVoucher.objects.filter(is_deleted=False).exists():
#             debit_note_vouchers = DebitNoteVoucher.objects.filter(is_deleted=False).order_by('voucher_date')
#             if not financial_year:
#                 first_date = debit_note_vouchers.first().voucher_date.date()

#             previous_debit_note_voucher = debit_note_vouchers.filter(voucher_date__date__range=[first_date, date_range])
#             if previous_debit_note_voucher.exists():
#                 total_voucher_amount = previous_debit_note_voucher.aggregate(amount=Sum('amount')).get('amount', 0)
#                 opening_balance -= total_voucher_amount

#         closing_balance = opening_balance

#         if debit_note_vouchers.filter(voucher_date__date__range=[from_date, to_date]).exists():
#             total_voucher_amount = debit_note_vouchers.filter(voucher_date__date__range=[from_date, to_date]).aggregate(amount=Sum('amount')).get('amount', 0)
#             closing_balance -= total_voucher_amount

#             if is_need_instances:
#                 debit_note_serialized = DebitNoteVoucherSerializer(debit_note_vouchers, many=True, context={"head": head, 'amount_type': 10, })
#                 instances += debit_note_serialized.data

#     if current_payment_vouchers.exists():
#         if is_need_instances:
#             payment_serialized = PaymentVoucherSerializer(current_payment_vouchers, many=True, context={'head': head})
#             instances += payment_serialized.data

#         current_p_total = current_payment_vouchers.aggregate(amount=Sum('amount')).get('amount', 0)
#         closing_balance += current_p_total

#     if current_receipt_vouchers.exists():
#         if is_need_instances:
#             payment_serialized = ReceiptVoucherSerializer(current_receipt_vouchers, many=True, context={'head': head})
#             instances += payment_serialized.data

#         current_p_total = current_receipt_vouchers.aggregate(amount=Sum('amount')).get('amount', 0)
#         closing_balance -= current_p_total

#     if current_journal_voucher_items.exists():
#         if is_need_instances:
#             journal_items_serialized = JournalVoucherItemSerializer(current_journal_voucher_items, many=True, context={})
#             instances += journal_items_serialized.data

#         if current_journal_voucher_items.filter(amount_type=20).exists():
#             current_j_debit_total = current_journal_voucher_items.filter(amount_type=20).aggregate(amount=Sum('amount')).get('amount', 0)
#             closing_balance += current_j_debit_total

#         if current_journal_voucher_items.filter(amount_type=10).exists():
#             current_j_credit_total = current_journal_voucher_items.filter(amount_type=10).aggregate(amount=Sum('amount')).get('amount', 0)
#             closing_balance -= current_j_credit_total

#     if is_need_instances:
#         data = {
#             'instances': instances,
#             'closing_balance': closing_balance,
#             'opening_balance': opening_balance,
#         }

#     elif is_need_closing:
#         data = {
#             'debit_total': debit_total,
#             'credit_total': credit_total,
#             'opening_balance': opening_balance,
#             'closing_balance': closing_balance,
#         }

#     return data
