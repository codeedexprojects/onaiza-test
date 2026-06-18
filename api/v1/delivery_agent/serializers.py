from delivery_agent.models import *
from orders.models import *
from rest_framework import serializers
from users.models import Notification
from web.models import ProductReturn

from delivery_agent.functions import get_total_distance

from delivery_agent.functions import serializer_return


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = '__all__'

    def get_product_name(self, instances):
        return {"name": f"{instances.product_variant.product.name} x {instances.qty}",
                "variant": instances.product_variant.title}


class OrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    order_items = serializers.SerializerMethodField()
    destination = serializers.SerializerMethodField()
    agent_status = serializers.SerializerMethodField()
    order_status_value = serializers.SerializerMethodField()
    delivery_date = serializers.SerializerMethodField()
    date_added = serializers.SerializerMethodField()
    time_slot = serializers.SerializerMethodField()

    class Meta:
        model = Orders
        fields = ['customer_name', 'total_amt', 'order_id', 'order_items', 'destination', 'pk', 'order_status', 'agent_status',
                  'pickup_status', 'order_status_value', 'billing_phone', 'payment_method', 'delivery_date', "date_added", 'time_slot']

    def get_customer_name(self, instances):
        return instances.customer.name

    def get_order_items(self, instance):
        order_item_instances = OrderItem.objects.filter(order=instance)
        request = self.context.get("request")
        serialized = OrderItemSerializer(order_item_instances, context={"request": request}, many=True)
        return serialized.data

    def get_destination(self, instance):
        data = {
            "customer_name": instance.billing_name,
            "customer_address": instance.get_full_address(),
            "warehouse_distance": "18km"
        }
        if instance.warehouse:
            data["warehouse"] = instance.warehouse.name
            data["warehouse_location"] = instance.warehouse.district

        return data

    def get_time_slot(self, instance):
        if instance.time_slot:
            start_time = instance.time_slot.start_time.strftime("%I:%M %p")
            end_time = instance.time_slot.end_time.strftime("%I:%M %p")

            return f"Between {start_time} & {end_time} on {instance.time_slot.get_day_display()}"

        return "Sooner (time not specified)"

    def get_delivery_date(self, instance):
        return instance.delivery_date

    def get_date_added(self, instance):
        return instance.assigned_time

    def get_agent_status(self, instance):
        return instance.delivery_agent_is_accept

    def get_order_status_value(self, instance):
        return instance.get_order_status_display()


class PaymentCollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectPayment
        exclude = ['creator', 'updater', 'auto_id', 'delivery_agent']


class DeliveryAgentLocationSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryAgentTravel
        fields = '__all__'


class ProductReturnSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    customer_address = serializers.SerializerMethodField()

    class Meta:
        model = ProductReturn
        fields = ['order_item', 'order', 'product', 'customer_address', 'pk']

    def get_product(self, instance):
        request = self.context.get("request")
        return {"product_name": instance.order_item.product_variant.get_fullname(),
                "image": request.build_absolute_uri(instance.order_item.product_variant.image.url)}

    def get_customer_address(self, instance):
        return instance.order_item.order.get_full_address()


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['subject', 'message', 'customer', 'who', 'pk']


class DeliveryAgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryAgents
        fields = ['name', 'email', 'phone1', 'email','image', 'id_proof', 'phone2']



class DeliveryAgentExportSerializer(serializers.ModelSerializer):

    total_distance_covered = serializers.SerializerMethodField()
    date_of_join = serializers.SerializerMethodField()

    class Meta:
        model = DeliveryAgents
        fields = ['name', 'email', 'phone1', 'email','total_distance_covered','date_of_join']

    def get_total_distance_covered(self,instance):
        total_distance = get_total_distance(instance)
        return serializer_return(total_distance, total_distance)

    def get_date_of_join(self,instance):
        return serializer_return('date_added', instance.date_added)