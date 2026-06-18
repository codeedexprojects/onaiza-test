from customers.models import Customer
from vendors.models import Vendor
from suppliers.models import Supplier
from orders.models import Orders
from purchases.models import Purchase
from rest_framework import serializers
from datetime import datetime
from django.utils import formats
from sales.models import Sale
from django.urls import reverse
from finance.models import PaymentVoucher, ReceiptVoucher, JournalVoucher, JournalVoucherItem, CreditNoteVoucher, DebitNoteVoucher


def extract_subledger_name(head_name, voucher_type, sub_ledger):
    sub_ledger_name = ''

    if head_name in ['Purchases','Sundry Creditor (Supplier)']:
        if Supplier.objects.filter(pk=sub_ledger).exists():
            sub_ledger_name = Supplier.objects.get(pk=sub_ledger).name
    elif head_name in ['Sales A/C', 'Online Sales', 'Sundry Debtor (Customer']:
        if Customer.objects.filter(pk=sub_ledger).exists():
            sub_ledger_name = Customer.objects.get(pk=sub_ledger).name
    elif head_name == 'Sundry Creditor (Vendor)':
        if Vendor.objects.filter(pk=sub_ledger).exists():
            sub_ledger_name = Vendor.objects.get(pk=sub_ledger).name

    return sub_ledger_name


class PaymentVoucherSerializer(serializers.ModelSerializer):
    voucher_date = serializers.SerializerMethodField()
    reverse_url = serializers.SerializerMethodField()
    reference = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    amount_type = serializers.SerializerMethodField()
    transfer_type = serializers.SerializerMethodField()
    transfer_number = serializers.SerializerMethodField()
    transfer_date = serializers.SerializerMethodField()

    class Meta:
        model = PaymentVoucher
        fields = (
            'pk',
            'title',
            'voucher_number',
            'voucher_date',
            'amount',
            'amount_type',
            'account_head',
            'sub_ledger',
            'reverse_url',
            'reference',
            'transfer_type',
            'transfer_number',
            'transfer_date'
        )

    def get_voucher_date(self, instance):
        return instance.voucher_date

    def get_reference(self, instance):
        number = f'PV - {instance.account_head} - '
        if instance.is_system_generated:
            number += str(instance.voucher_number)
        else:
            # number += str(instance.manual_voucher_number)
            number += str(instance.voucher_number)

        if instance.account_head.name == 'Purchases':
            try:
                purchase_id = Supplier.objects.get(pk=instance.sub_ledger).purchase_id
            except:
                purchase_id = ''

            number = f'{instance.account_head} - {purchase_id}'

        return number

    def get_title(self, instance):
        title = None
        head = self.context.get('head')
        ac_head_name = instance.account_head.name

        if head:
            subledger_name = extract_subledger_name(ac_head_name, 'payment', instance.sub_ledger)
            if subledger_name:
                if head.name == 'Cash A/C' or head.bank_account:
                    title = f"Amount payed - {subledger_name}"

        if not title:
            title = instance.title

        return title

    def get_amount_type(self, instance):
        # 10 = credit, 20 = debit
        amount_type = self.context.get('amount_type')
        if not amount_type:
            amount_type = instance.amount_type

        return amount_type

    def get_transfer_type(self, instance):
        transfer_type = instance.get_transfer_type_display()

        return transfer_type

    def get_transfer_number(self, instance):
        transfer_number = None
        if instance.transfer_type == 15:
            transfer_number = instance.cheque_no
        elif instance.transfer_type == 20:
            transfer_number = instance.draft_no
        elif instance.transfer_type == 25:
            transfer_number = instance.transfer_number

        return transfer_number

    def get_transfer_date(self, instance):
        transfer_date = None
        if instance.transfer_type == 15:
            transfer_date = instance.cheque_date
        elif instance.transfer_type == 20:
            transfer_date = instance.draft_date
        elif instance.transfer_type == 25:
            transfer_date = instance.transfer_date

        return transfer_date

    def get_reverse_url(self, instance):
        head = self.context.get('head')
        url = reverse('finance:payment_voucher', kwargs={'pk': instance.pk})

        if instance.account_head.name == "Purchases" and instance.sub_ledger:
            if head.name == 'Cash A/C' or head.bank_account:
                url = reverse('purchases:purchase', kwargs={'pk': instance.sub_ledger})

        return url


class ReceiptVoucherSerializer(serializers.ModelSerializer):
    voucher_date = serializers.SerializerMethodField()
    reverse_url = serializers.SerializerMethodField()
    reference = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    amount_type = serializers.SerializerMethodField()
    transfer_type = serializers.SerializerMethodField()
    transfer_number = serializers.SerializerMethodField()
    transfer_date = serializers.SerializerMethodField()

    class Meta:
        model = ReceiptVoucher
        fields = (
            'pk',
            'title',
            'voucher_number',
            'voucher_date',
            'amount',
            'amount_type',
            'account_head',
            'sub_ledger',
            'reverse_url',
            'reference',
            'transfer_type',
            'transfer_number',
            'transfer_date'
        )

    def get_reference(self, instance):
        number = f'RV - {instance.account_head} - '

        if instance.is_system_generated:
            number += str(instance.voucher_number)
        else:
            # number += str(instance.manual_voucher_number)
            number += str(instance.voucher_number)

        return number

    def get_voucher_date(self, instance):
        return instance.voucher_date

    def get_title(self, instance):
        head = self.context.get('head')
        title = None

        if head:
            subledger_name = extract_subledger_name(instance.account_head.name, 'receipt', instance.sub_ledger)

            if subledger_name:
                if head.name == 'Cash A/C' or head.bank_account:
                    title = f"Amount received - {subledger_name}"

        if not title:
            title = instance.title

        return title

    def get_transfer_type(self, instance):
        transfer_type = instance.get_transfer_type_display()

        return transfer_type

    def get_transfer_number(self, instance):
        transfer_number = None
        if instance.transfer_type == 15:
            transfer_number = instance.cheque_no
        elif instance.transfer_type == 20:
            transfer_number = instance.draft_no
        elif instance.transfer_type == 25:
            transfer_number = instance.transfer_number

        return transfer_number

    def get_transfer_date(self, instance):
        transfer_date = None
        if instance.transfer_type == 15:
            transfer_date = instance.cheque_date
        elif instance.transfer_type == 20:
            transfer_date = instance.draft_date
        elif instance.transfer_type == 25:
            transfer_date = instance.transfer_date

        return transfer_date

    def get_amount_type(self, instance):
        # 10 = credit, 20 = debit
        amount_type = self.context.get('amount_type')
        if not amount_type:
            amount_type = instance.amount_type
        return amount_type

    def get_reverse_url(self, instance):
        head = self.context.get('head')
        url = reverse('finance:receipt_voucher', kwargs={'pk': instance.pk})

        if instance.account_head.name == "Sales A/C" and instance.sub_ledger:
            if head.name == 'Cash A/C' or head.bank_account:
                url = reverse('sales:sale', kwargs={'pk': instance.sub_ledger})

        return url


class JournalVoucherItemSerializer(serializers.ModelSerializer):
    reverse_url = serializers.SerializerMethodField()
    pk = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    voucher_number = serializers.SerializerMethodField()
    voucher_date = serializers.SerializerMethodField()
    reference = serializers.SerializerMethodField()

    class Meta:
        model = JournalVoucherItem
        fields = ('pk', 'title', 'voucher_number', 'voucher_date', 'amount', 'amount_type', 'account_head', 'sub_ledger', 'reverse_url', 'reference')

    def get_pk(self, instance):
        return instance.journal.pk

    def get_title(self, instance):
        return instance.journal.title

    def get_voucher_number(self, instance):
        return instance.journal.voucher_number

    def get_reference(self, instance):
        return f'JV - {instance.account_head} - {instance.journal.voucher_number}'

    def get_voucher_date(self, instance):
        return instance.journal.voucher_date

    def get_reverse_url(self, instance):
        return reverse('finance:journal_voucher', kwargs={'pk': instance.journal.pk})


class CreditNoteVoucherSerializer(serializers.ModelSerializer):
    reverse_url = serializers.SerializerMethodField()
    voucher_date = serializers.SerializerMethodField()
    reference = serializers.SerializerMethodField()
    amount_type = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()

    class Meta:
        model = CreditNoteVoucher
        fields = ('pk', 'title', 'voucher_number', 'voucher_date', 'amount', 'amount_type', 'sub_ledger', 'reverse_url', 'reference')

    def get_reference(self, instance):
        number = f'Cr-Note - {instance.voucher_number}'

        return number

    def get_voucher_date(self, instance):
        return instance.voucher_date

    def get_title(self, instance):
        title = f"Amount Payed on sale return to ({instance.customer})"

        if not title:
            title = instance.title

        return title

    def get_amount(self, instance):
        amount = instance.amount

        return amount

    def get_amount_type(self, instance):
        amount_type = self.context.get('amount_type')
        if not amount_type:
            amount_type = instance.amount_type
        return amount_type

    def get_reverse_url(self, instance):
        # return reverse('sales:sale_return', kwargs={'pk': instance.sub_ledger})
        return reverse('finance:credit_note_voucher', kwargs={'pk': instance.pk})


class DebitNoteVoucherSerializer(serializers.ModelSerializer):
    reverse_url = serializers.SerializerMethodField()
    voucher_date = serializers.SerializerMethodField()
    reference = serializers.SerializerMethodField()
    amount_type = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()

    class Meta:
        model = DebitNoteVoucher
        fields = ('pk', 'title', 'voucher_number', 'voucher_date', 'amount', 'amount_type', 'sub_ledger', 'reverse_url', 'reference')

    def get_reference(self, instance):
        number = f'Dr-Note - {instance.voucher_number}'

        return number

    def get_voucher_date(self, instance):
        return instance.voucher_date

    def get_title(self, instance):
        amount_type = self.context.get('amount_type')

        if amount_type == 10:
            title = f"Amount Received on purchase return from ({instance.vendor})"
        elif amount_type == 20:
            title = f"{instance.sub_ledger_name}"

        if not title:
            title = instance.title

        return title

    def get_amount(self, instance):
        amount = instance.amount

        return amount

    def get_amount_type(self, instance):
        amount_type = self.context.get('amount_type')
        if not amount_type:
            amount_type = instance.amount_type
        return amount_type

    def get_reverse_url(self, instance):
        # return reverse('purchases:purchase_return', kwargs={'pk': instance.sub_ledger})
        return reverse('finance:debit_note_voucher', kwargs={'pk': instance.pk})



