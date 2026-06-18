from rest_framework import serializers
from datetime import datetime
from django.utils import formats
from django.urls import reverse
from sales.models import Sale, SaleItem, SaleReturnItem


class SaleSerializer(serializers.ModelSerializer):
    voucher_date = serializers.SerializerMethodField()
    voucher_number = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    amount_type = serializers.SerializerMethodField()
    account_head = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()
    reverse_url = serializers.SerializerMethodField()
    reference = serializers.SerializerMethodField()

    class Meta:
        model = Sale

        fields = (
            'voucher_date',
            'voucher_number',
            'title',
            'amount_type',
            'account_head',
            'amount',
            'reverse_url',
            'reference'
        )

    def get_title(self, instance):

        return ('Sale to Customer %s' % instance.customer.name)

    def get_voucher_number(self, instance):

        return ('%s' % instance.sale_id)

    def get_voucher_date(self, instance):

        return instance.sale_date

    def get_amount_type(self, instance):
        amount_type = self.context.get('amount_type')

        return amount_type

    def get_amount(self, instance):

        return (round(instance.total, 2))

    def get_account_head(self, instance):
        head = self.context.get('head')

        return head

    def get_reference(self, instance):
        return f'{instance.sale_id}'

    def get_reverse_url(self, instance):
        return reverse('sales:sale', kwargs={'pk': instance.pk})


class CustomerSaleSerializer(serializers.ModelSerializer):
    voucher_date = serializers.SerializerMethodField()
    voucher_number = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    amount_type = serializers.SerializerMethodField()
    account_head = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()
    reverse_url = serializers.SerializerMethodField()
    reference = serializers.SerializerMethodField()

    class Meta:
        model = Sale

        fields = (
            'voucher_date',
            'voucher_number',
            'title',
            'amount_type',
            'account_head',
            'amount',
            'reverse_url',
            'reference'
        )

    def get_title(self, instance):
        amount_type = self.context.get('amount_type')

        if amount_type == 20:

            return ('Sale to Customer %s' % instance.customer.name)
        else:

            return ('Sale payment from %s' % instance.customer.name)

    def get_voucher_number(self, instance):

        return ('%s' % instance.sale_id)

    def get_voucher_date(self, instance):

        return instance.sale_date

    def get_amount_type(self, instance):
        amount_type = self.context.get('amount_type')

        return amount_type

    def get_amount(self, instance):
        amount_type = self.context.get('amount_type')

        if amount_type == 20:

            return (round(instance.total, 2))
        else:

            return (round(instance.paid, 2))

    def get_account_head(self, instance):
        head = self.context.get('head')

        return head

    def get_reference(self, instance):
        return f'{instance.sale_id}'

    def get_reverse_url(self, instance):
        return reverse('sales:sale', kwargs={'pk': instance.pk})


class SaleItemStockSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    stock_type = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()
    reverse_url = serializers.SerializerMethodField()
    reference = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    class Meta:
        model = SaleItem

        fields = (
            'title',
            'stock_type',
            'quantity',
            'reference',
            'reverse_url',
            'date'
        )

    def get_title(self, instance):

        return ('Sale to customer %s' % instance.sale.customer.name)

    def get_date(self, instance):

        return instance.sale.date_added

    def get_stock_type(self, instance):

        return "OUT"

    def get_quantity(self, instance):

        return (instance.quantity)

    def get_reference(self, instance):

        return f'{instance.sale.sale_id}'

    def get_reverse_url(self, instance):

        return reverse('sales:sale', kwargs={'pk': instance.sale.pk})




class SaleReturnItemStockSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    stock_type = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()
    reverse_url = serializers.SerializerMethodField()
    reference = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    class Meta:
        model = SaleReturnItem

        fields = (
            'title',
            'stock_type',
            'quantity',
            'reference',
            'reverse_url',
            'date'
        )

    def get_title(self, instance):

        return ('Sale Return from customer %s' % instance.sale_item.sale.customer.name)

    def get_date(self, instance):

        return instance.sale_item.sale.date_added

    def get_stock_type(self, instance):

        return "IN"

    def get_quantity(self, instance):

        return (instance.qty)

    def get_reference(self, instance):

        return f'SL RN- {instance.sale_item.sale.sale_id}'

    def get_reverse_url(self, instance):

        return reverse('sales:sale_return', kwargs={'pk': instance.sale_return.pk})
