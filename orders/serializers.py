from rest_framework import serializers
from django.urls import reverse
from orders.models import Orders


class OrdersSerializer(serializers.ModelSerializer):
    voucher_date = serializers.SerializerMethodField()
    voucher_number = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    amount_type = serializers.SerializerMethodField()
    account_head = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()
    reverse_url = serializers.SerializerMethodField()
    reference = serializers.SerializerMethodField()

    class Meta:
        model = Orders

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
        return ('Order From Customer %s' % instance.customer.name)

    def get_voucher_number(self, instance):
        return ('%s' % instance.order_id)

    def get_voucher_date(self, instance):
        return instance.date_added

    def get_amount_type(self, instance):
        amount_type = self.context.get('amount_type')
        return amount_type

    def get_amount(self, instance):
        return (round(instance.total, 2))

    def get_account_head(self, instance):
        head = self.context.get('head')
        return head

    def get_reference(self, instance):
        return f'{instance.order_id}'

    def get_reverse_url(self, instance):
        return reverse('orders:order', kwargs={'pk': instance.pk})

