from datetime import datetime

from delivery_agent.models import DeliveryAgents, CollectPayment, DeliveryAgentTravel, CollectedPaymentRegister
from orders.models import Orders


class DeliveryAgentUtils:
    def __init__(self, agent_pk=None):
        self.agent_pk = agent_pk

    def delivery_agent(self):
        return DeliveryAgents.objects.get(pk=self.agent_pk)

    def get_all_agents(self):
        return DeliveryAgents.objects.filter(is_deleted=False)

    def get_all_orders(self):
        agent = self.delivery_agent()
        orders = Orders.objects.filter(delivery_agent=agent)
        return orders

    def get_all_order_including_distance(self):
        agent = self.delivery_agent()
        orders = DeliveryAgentTravel.objects.filter(delivery_agent=agent)
        return orders

    def approve_hand_over(self, pk):
        instance = CollectedPaymentRegister.objects.get(pk=pk)
        instance.is_approved = True
        instance.is_declined= False
        instance.save()

    def decline_decline_hand_over(self, pk, reason):
        instance = CollectedPaymentRegister.objects.get(pk=pk)
        instance.is_approved = False
        instance.is_declined = True
        if reason:
            instance.declined_reason = reason
        instance.save()

    def handover_details(self, start_date=None, end_date=None, delivery_agent=None):
        instances = CollectedPaymentRegister.objects.filter(is_deleted=False)

        if delivery_agent:
            instances = instances.filter(delivery_agent__pk=delivery_agent)

        if start_date and end_date:
            from_date = datetime.strptime(start_date, '%d/%m/%Y').date()
            to_date = datetime.strptime(end_date, '%d/%m/%Y').date()
            instances = instances.filter(date_added__range=[from_date, to_date])

        return instances
