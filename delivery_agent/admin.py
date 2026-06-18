from django.contrib import admin
from delivery_agent.models import *

admin.site.register(DeliveryAgents)
admin.site.register(CollectPayment)
admin.site.register(DeliveryRating)
admin.site.register(DeliveryAgentTravel)

admin.site.register(CollectedPaymentRegister)