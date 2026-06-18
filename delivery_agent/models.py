from customers.models import Customer
from django.db import models
from django.utils.translation import ugettext_lazy as _
from general.models import UserBaseModel
from main.models import BaseModel
from orders.models import Orders
from versatileimagefield.fields import VersatileImageField
from warehouses.models import Warehouse
from django.db.models import JSONField

RATING_CHOICES = ((1, 1), (2, 2), (3, 3), (4, 4), (5, 5),)


class DeliveryAgents(BaseModel):
    user = models.OneToOneField("auth.User", on_delete=models.CASCADE, blank=True, null=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, null=True, blank=True)

    name = models.CharField(max_length=128)
    phone1 = models.CharField(max_length=128)
    phone2 = models.CharField(max_length=128, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    password = models.CharField(max_length=256)

    active_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(null=True, blank=True)

    image = VersatileImageField(upload_to="customers/images/", null=True, blank=True)
    id_proof = VersatileImageField(upload_to="delivery_agents/proofs/", null=True, blank=True)

    class Meta:
        db_table = 'delvery_agent_delivery_agent'
        verbose_name = _('delivery agent')
        verbose_name_plural = _('delivery agents')
        ordering = ('-date_added', 'name')

    def __str__(self):
        return str(self.name)


class CollectPayment(BaseModel):
    delivery_agent = models.ForeignKey(DeliveryAgents, on_delete=models.CASCADE)
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)

    name = models.CharField(max_length=128)
    collected_amount = models.DecimalField(decimal_places=2, max_digits=15)
    is_transferred = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('collected payment')
        verbose_name_plural = _('collected payments')

    def __str__(self):
        return str(self.name)


class DeliveryRating(UserBaseModel):
    delivery_agent = models.ForeignKey(DeliveryAgents, on_delete=models.CASCADE)
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)

    class Meta:
        verbose_name = _('rating')
        verbose_name_plural = _('rating')

    def __str__(self):
        return str(self.customer.name)


class DeliveryAgentTravel(UserBaseModel):
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    delivery_agent = models.ForeignKey(DeliveryAgents, on_delete=models.CASCADE)

    # cordinates of order accept location
    origin_latitude = models.TextField(blank=True, null=True)
    origin_longitude = models.TextField(blank=True, null=True)

    # probably cordinates of warehouse
    pickup_latitude = models.TextField(blank=True, null=True)
    pickup_longitude = models.TextField(blank=True, null=True)

    # cordinates of delivered location
    delivery_latitude = models.TextField(blank=True, null=True)
    delivery_longitude = models.TextField(blank=True, null=True)

    pickup_distance = models.DecimalField(decimal_places=2, default=0, max_digits=15)  # in meter
    delivery_distance = models.DecimalField(decimal_places=2, default=0, max_digits=15)  # in meter

    pickup_distance_text = models.CharField(max_length=125, null=True)
    delivery_distance_text = models.CharField(max_length=125, null=True)

    class Meta:
        db_table = 'delvery_agent_travel'
        verbose_name = _('delivery agent location')
        verbose_name_plural = _('delivery agent locations')

    def __str__(self):
        return f"{self.delivery_agent.name}"

    def total_delivery_distance(self):
        return self.pickup_distance + self.delivery_distance


class CollectedPaymentRegister(BaseModel):
    PAYMENT_CHOICES = (("cash", "Cash"), ("upi", "UPI"),)
    collected_payments = JSONField(default=list)
    delivery_agent = models.ForeignKey(DeliveryAgents, on_delete=models.CASCADE)
    collected_amount = models.DecimalField(decimal_places=2, max_digits=15)
    is_approved = models.BooleanField(default=False)
    is_declined = models.BooleanField(default=False)
    declined_reason = models.TextField(null=True,blank=True)
    payment_medium = models.CharField(max_length=15, choices=PAYMENT_CHOICES)
    image = VersatileImageField(upload_to="delivery_agents/collected-payments/", null=True, blank=True)

    class Meta:
        verbose_name = _('collected payment register')
        verbose_name_plural = _('collected payments register')

    def __str__(self):
        return f"{self.delivery_agent.name} - {self.collected_amount}"
