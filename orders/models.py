from django.db import models

from main.models import BaseModel
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MinValueValidator
from customers.models import Customer
from products.models import *
from general.models import UserBaseModel
from general.models import Batch
from warehouses.models import Warehouse, Location


DAY_CHOICES = (
    (1, 'Monday'),
    (2, 'Tuesday'),
    (3, 'Wednesday'),
    (4, 'Thursday'),
    (5, 'Friday'),
    (6, 'Saturday'),
    (7, 'Sunday'),
)


ORDER_CHOICES = (
    ("10", 'Pending'),
    ("20", 'Shipped'),
    ("30", 'Delivered'),
    ("40", 'Cancelled'),
)

VENDOR_CHOICES = (
    (10, 'Pending'),
    (20, 'Accepted'),
    (30, 'Packed'),
    (40, 'Declined'),
)

PAYMENT_CHOICES = (
    ("10", 'Pending'),
    ("20", 'Recieved'),
    ("30", 'Failed'),

)

BOOKING_STATUS_CHOICES = (
    ('pending', 'pending'),
    ('confirmed', 'Confirmed'),
)

DELIVERY_AGENT_DECLINED_CHOICES = (
    ('too_long', 'Too Long'),
    ('time_waste', 'Time Waste'),
    ('large_order_list', 'Large Order List'),
)

PICKUP_CHOICES = (
    ('reached', 'Reached Pickup Location'),
    ('picked_up', 'Picked Up'),
)

class TimeSlot(BaseModel):
    day = models.IntegerField(choices=DAY_CHOICES, default=1)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        verbose_name = 'time slot'
        verbose_name_plural = 'time slots'

    def __str__(self):
        start_time = self.start_time.strftime("%I:%M %p")
        end_time = self.end_time.strftime("%I:%M %p")
        return f"{start_time} - {end_time}"

class Orders(BaseModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, )
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, null=True, blank=True)
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, null=True, blank=True)
    prefix = models.ForeignKey('finance.InvoicePrefix', on_delete=models.CASCADE, null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True)

    billing_name = models.CharField(max_length=50, null=False)
    billing_phone = models.CharField(max_length=10, null=False)
    billing_address = models.TextField(max_length=128, null=True, blank=True)
    billing_landmark = models.CharField(max_length=128, null=False)
    billing_street = models.CharField(max_length=128, null=False)
    billing_state = models.CharField(max_length=128, null=False)
    billing_city = models.CharField(max_length=128, null=False)

    order_status = models.CharField(choices=ORDER_CHOICES,max_length=5, null=False, default=10)
    payment_method = models.CharField(max_length=128, null=False)
    payment_status = models.CharField(choices=PAYMENT_CHOICES,max_length=5, null=False)

    delivery_agent = models.ForeignKey('delivery_agent.DeliveryAgents', on_delete=models.CASCADE, null=True, blank=True)
    assigned_time = models.DateTimeField(null=True, blank=True)
    delivery_agent_is_accept = models.BooleanField(null=True,blank=True)
    delivery_agent_declined_reason = models.CharField(choices=DELIVERY_AGENT_DECLINED_CHOICES,max_length=100, null=True,blank=True)
    delivery_agent_declined_reason_text = models.TextField(null=True, blank=True)
    pickup_status = models.CharField(max_length=256, choices=PICKUP_CHOICES,null=True,blank=True)

    total_amt = models.FloatField()
    card_name = models.CharField(max_length=128, null=True, blank=True)
    card_number = models.CharField(max_length=128, null=True, blank=True)
    transaction_id = models.CharField(max_length=128, null=True, blank=True)
    payment_order_id = models.CharField(max_length=128, null=True, blank=True)
    delivery_note = models.TextField(null=True,blank=True)

    order_no = models.IntegerField()
    order_id = models.TextField(null=True,blank=True)

    class Meta:
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
        ordering = ('-date_added',)

    def __str__(self):
        return str(self.customer)

    def get_order_items(self):
        return OrderItem.objects.filter(order=self)

    def get_full_address(self):
        return f"{self.billing_address} , {self.billing_street}, {self.billing_city}, {self.billing_landmark}, {self.billing_state}"

    def get_full_timesot(self):
        return f"{self.delivery_date} - {self.time_slot}"


class OrderItem(UserBaseModel):
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, )
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, )
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, null=True, blank=True)

    qty = models.DecimalField(default=0.0, decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    price = models.DecimalField(default=0.0, decimal_places=2, max_digits=15,validators=[MinValueValidator(Decimal('0.00'))])
    status = models.PositiveIntegerField(default=10, choices=VENDOR_CHOICES,null=True,blank=True)

    class Meta:
        ordering = ('qty',)
        verbose_name = 'order item'
        verbose_name_plural = 'order items'
        
    def total(self):
        total = (self.qty * self.price)
        
        return(total)

    def __str__(self):
        return f"{self.product_variant} - {self.order.customer}"


class Booking(UserBaseModel):
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, )
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, )
    message = models.TextField()
    status = models.CharField(max_length=10,choices=BOOKING_STATUS_CHOICES)
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        verbose_name = 'booking'
        verbose_name_plural = 'bookings'
        ordering = ('-date_added', 'status')

    def __str__(self):
        return str(self.customer.name)