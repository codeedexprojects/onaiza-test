from rest_framework import serializers
from datetime import datetime
from django.utils import formats
from django.urls import reverse
from purchases.models import Purchase, PurchaseReturn, PurchaseItem, PurchaseReturnItem


class PurchaseSerializer(serializers.ModelSerializer):
    voucher_date = serializers.SerializerMethodField()
    voucher_number = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    amount_type = serializers.SerializerMethodField()
    account_head = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()
    reverse_url = serializers.SerializerMethodField()
    reference = serializers.SerializerMethodField()

    class Meta:
        model = Purchase

        fields = (
            'voucher_date',
            'voucher_number',
            'title',
            'amount_type',
            'account_head',
            'amount',
            'reference',
            'reverse_url'
        )

    def get_title(self, instance):

        return ('Purchase from Vendor %s' % instance.supplier.name)

    def get_voucher_number(self, instance):

        return ('%s' % instance.purchase_id)

    def get_voucher_date(self, instance):

        return instance.date

    def get_amount_type(self, instance):

        return 20

    def get_amount(self, instance):

        return (round(instance.subtotal, 2))

    def get_account_head(self, instance):
        head = self.context.get('head')

        return head

    def get_reference(self, instance):
        return f'{instance.purchase_id}'

    def get_reverse_url(self, instance):
        return reverse('purchases:purchase', kwargs={'pk': instance.pk})


class VendorPurchaseSerializer(serializers.ModelSerializer):
    voucher_date = serializers.SerializerMethodField()
    voucher_number = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    amount_type = serializers.SerializerMethodField()
    account_head = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()
    reverse_url = serializers.SerializerMethodField()
    reference = serializers.SerializerMethodField()

    class Meta:
        model = Purchase

        fields = (
            'voucher_date',
            'voucher_number',
            'title',
            'amount_type',
            'account_head',
            'amount',
            'reference',
            'reverse_url'
        )

    def get_title(self, instance):
        amount_type = self.context.get('amount_type')

        if amount_type == 10:

            return ('Purchase from supplier %s' % instance.supplier.name)
        else:

            return ('Purchase payment to %s' % instance.supplier.name)

    def get_voucher_number(self, instance):

        return ('%s' % instance.purchase_id)

    def get_voucher_date(self, instance):

        return instance.date

    def get_amount_type(self, instance):
        amount_type = self.context.get('amount_type')

        return amount_type

    def get_amount(self, instance):
        amount_type = self.context.get('amount_type')

        if amount_type == 10:

            return (round(instance.subtotal, 2))
        else:

            return (round(instance.paid, 2))

    def get_account_head(self, instance):
        head = self.context.get('head')

        return head

    def get_reference(self, instance):
        return f'{instance.purchase_id}'

    def get_reverse_url(self, instance):
        return reverse('purchases:purchase', kwargs={'pk': instance.pk})


class PurchaseItemStockSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    stock_type = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()
    reverse_url = serializers.SerializerMethodField()
    reference = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseItem

        fields = (
            'title',
            'stock_type',
            'quantity',
            'reference',
            'reverse_url',
            'date'
        )

    def get_title(self, instance):

        return ('Purchase from supplier %s' % instance.purchase.supplier.name)

    def get_date(self, instance):

        return instance.purchase.date

    def get_stock_type(self, instance):

        return "IN"

    def get_quantity(self, instance):

        return (instance.quantity)

    def get_reference(self, instance):

        return f'{instance.purchase.purchase_id}'

    def get_reverse_url(self, instance):

        return reverse('purchases:purchase', kwargs={'pk': instance.purchase.pk})


class PurchaseReturnItemStockSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    stock_type = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()
    reverse_url = serializers.SerializerMethodField()
    reference = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseReturnItem

        fields = (
            'title',
            'stock_type',
            'quantity',
            'reference',
            'reverse_url',
            'date'
        )

    def get_title(self, instance):

        return ('Purchase Return from supplier %s' % instance.purchase_return.supplier.name)

    def get_date(self, instance):

        return instance.purchase_return.date_added

    def get_stock_type(self, instance):

        return "OUT"

    def get_quantity(self, instance):

        return (instance.quantity)

    def get_reference(self, instance):

        return f'PR RN- {instance.purchase_return.auto_id}'

    def get_reverse_url(self, instance):

        return reverse('purchases:purchase_return', kwargs={'pk': instance.purchase_return.pk})
