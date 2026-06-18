from django.db.models import Sum, F
from django.template import Library
from django.template.defaultfilters import stringfilter

from delivery_agent.models import CollectPayment, CollectedPaymentRegister
from orders.models import Orders

register = Library()


@register.simple_tag
def get_order_total_of_agent(agent):
    orders = Orders.objects.filter(delivery_agent=agent)
    total_orders = orders.count()

    accepted_orders = orders.filter(delivery_agent_is_accept=True).count()
    completed_orders = orders.filter(order_status="30").count()
    rejected_orders = orders.filter(delivery_agent_is_accept=False,
                                    delivery_agent_declined_reason__isnull=False).count()

    return {"accepted_orders": accepted_orders, "completed_orders": completed_orders,
            "rejected_orders": rejected_orders, "total_orders": total_orders, }


@register.simple_tag
def get_amount_total_of_agent(agent):
    collected_amount = CollectPayment.objects.filter(delivery_agent=agent)

    total_amount_collected = collected_amount.aggregate(total=Sum(F('collected_amount')))['total']
    handovered_amount = \
        CollectedPaymentRegister.objects.filter(delivery_agent=agent).aggregate(total=Sum(F('collected_amount')))[
            'total']
    balance_amount = collected_amount.filter(is_transferred=False).aggregate(total=Sum(F('collected_amount')))['total']

    return {"total_collected_amount": total_amount_collected, "handovered_amount": handovered_amount,
        "balance_amount": balance_amount, }


@register.simple_tag
def get_collected_amount(order_pk):
    if  CollectPayment.objects.filter(order__pk=order_pk).exists():
        instance = CollectPayment.objects.get(order__pk=order_pk)
        return instance.collected_amount
    return ''


@register.simple_tag
def is_handovered(order_pk):
    if CollectPayment.objects.filter(order__pk=order_pk).exists():
        instance = CollectPayment.objects.get(order__pk=order_pk)
        return instance.is_transferred
    return ''