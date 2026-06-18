from django.db.models import Sum, F

from delivery_agent.models import CollectPayment, CollectedPaymentRegister
from main.functions import get_auto_id


class DeliveryAgentUtils:
    def __init__(self, delivery_agent):
        self.delivery_agent = delivery_agent

    def get_total_unpaid_amount(self):
        total_amount_to_be_paid = \
            CollectPayment.objects.filter(delivery_agent=self.delivery_agent, is_transferred=False).aggregate(
                total=Sum(F('collected_amount')))['total']
        print("aount to be collected", total_amount_to_be_paid)
        return total_amount_to_be_paid

    def total_amount_to_transfer(self):
        return self.get_total_unpaid_amount()

    def get_array_of_payemnt_id(self):
        payment_array = []
        instance = CollectPayment.objects.filter(delivery_agent=self.delivery_agent, is_transferred=False)
        for i in instance:
            payment_array.append(i.pk)

        return payment_array

    def transfer_amount(self, payment_medium, user, image=None):
        collected_payments = self.get_array_of_payemnt_id()
        collected_amount = self.total_amount_to_transfer()

        print(payment_medium,'===========')
        if collected_amount:
            total_amount_to_be_paid = CollectPayment.objects.filter(delivery_agent=self.delivery_agent,
                                                                    is_transferred=False).update(is_transferred=True)
            if image:
                CollectedPaymentRegister.objects.create(collected_payments=collected_payments,
                                                        delivery_agent=self.delivery_agent,
                                                        collected_amount=collected_amount, payment_medium=payment_medium,
                                                        image=image, auto_id=get_auto_id(CollectedPaymentRegister),
                                                        creator=user, updater=user)
            else:
                CollectedPaymentRegister.objects.create(collected_payments=collected_payments,
                                                        delivery_agent=self.delivery_agent,
                                                        collected_amount=collected_amount, payment_medium=payment_medium,
                                                        auto_id=get_auto_id(CollectedPaymentRegister), creator=user,
                                                        updater=user)

            return {"status": True, "amount": collected_amount}
        else:
            return {"status": False, "message": "No amounts to transfer"}

