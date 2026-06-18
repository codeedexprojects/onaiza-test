import datetime
from api.v1.general.functions import is_pincode_exists, get_pincode
from customers.models import Customer, Ticket, CustomerAddress
from django.db.models import Sum, F
from general.models import Batch
from offers.models import VoucherCode
from orders.models import TimeSlot, Orders, OrderItem, Booking
from rest_framework import serializers
from users.models import Wishlistitem, CartItem
from web.functions import get_orginal_price, get_mrp
from web.models import ProductReview
from api.v1.users.functions import get_privliged_points, is_eligible_for_return
from delivery_agent.models import DeliveryRating


class PhoneNumberSerializer(serializers.Serializer):
    phone = serializers.CharField()


class CustomerRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'image']


class WishlistSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    malayalam_name = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    mrp = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    is_wishlist = serializers.SerializerMethodField()
    is_cart = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    malayalam_category = serializers.SerializerMethodField()
    is_book_now_button = serializers.SerializerMethodField()

    class Meta:
        model = Wishlistitem
        fields = ['product_variant', 'name', 'image', 'is_wishlist', 'is_cart', 'mrp', 'price', 'category',
                  'malayalam_category', 'malayalam_name', 'is_book_now_button']

    def get_name(self, instances):
        return instances.product_variant.get_fullname()

    def get_malayalam_name(self, instances):
        return instances.product_variant.get_malayalam_name()

    def get_image(self, instances):
        request = self.context.get('request')
        if instances.product_variant.image:
            image_url = instances.product_variant.image.url
            return request.build_absolute_uri(image_url)

    def get_mrp(self, instances):
        if instances.product_variant.mrp:
            return instances.product_variant.mrp

    def get_price(self, instances):
        if instances.product_variant.retail_price:
            return instances.product_variant.retail_price

    def get_is_cart(self, instances):
        request = self.context.get("request")
        if CartItem.objects.filter(product_variant=instances.product_variant, customer__user=request.user).exists():
            return True
        return False

    def get_is_wishlist(self, instances):
        request = self.context.get("request")
        if Wishlistitem.objects.filter(product_variant=instances.product_variant, customer__user=request.user).exists():
            return True
        return False

    def get_category(self, instances):
        if instances.product_variant.product.category:
            return instances.product_variant.product.category.name

    def get_malayalam_category(self, instances):
        if instances.product_variant.product.category:
            return instances.product_variant.product.category.malayalam_name

    def get_is_book_now_button(self, instances):
        request = self.context.get("request")
        pincode = request.session.get('pincode', '')

        if pincode:
            # if a batch with zero stock exits it returns True
            if Batch.objects.filter(product_variant=instances, stock__gt=0, warehouse__location__pincode=pincode).exists():
                return False
            else:
                return True
        else:
            return None


class CustomerAddressSerializer(serializers.ModelSerializer):
    pincode_data = serializers.SerializerMethodField()
    address_type_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomerAddress
        # exclude = ['customer']
        fields = ['name', 'id', 'house_name', 'phone', 'email', 'pincode', 'pincode_data', 'street', 'city', 'landmark',
                  'state', 'address_type', 'address_type_name', 'is_default']

    def get_address_type_name(self, instance):
        if instance.address_type == 10:
            return "Home"
        elif instance.address_type == 20:
            return "Office"

    def get_pincode_data(self, instance):
        return {'id': str(instance.pincode.id), 'pincode': instance.pincode.pincode, 'name': instance.pincode.name}


class CartItemSerializer(serializers.ModelSerializer):
    date_added = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    malayalam_name = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    mrp = serializers.SerializerMethodField()
    retail_price = serializers.SerializerMethodField()
    sub_category = serializers.SerializerMethodField()
    malayalam_sub_category = serializers.SerializerMethodField()
    uom = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        exclude = ['customer']

    def get_date_added(self, instances):
        return str(instances.date_added)

    def get_name(self, instances):
        return instances.product_variant.get_fullname()

    def get_malayalam_name(self, instances):
        return instances.product_variant.get_malayalam_name()

    def get_image(self, instances):
        request = self.context.get('request')
        if instances.product_variant.image:
            image_url = instances.product_variant.image.url
            return request.build_absolute_uri(image_url)

    def get_mrp(self, instances):
        request = self.context.get('request')
        return get_orginal_price(instances.product_variant, request)

    def get_sub_category(self, instances):
        if instances.product_variant.product.subcategory:
            return instances.product_variant.product.subcategory.name

    def get_malayalam_sub_category(self, instances):
        if instances.product_variant.product.subcategory:
            return instances.product_variant.product.subcategory.malayalam_name

    def get_uom(self, instance):
        if instance.product_variant.product.unit_of_measurement:
            return instance.product_variant.product.unit_of_measurement.unit_of_measurement

    def get_retail_price(self, instance):
        request = self.context.get('request')
        # get mrp defined in web.functions
        return get_mrp(instance.product_variant, request)


class VoucherSerializer(serializers.ModelSerializer):
    is_applied = serializers.SerializerMethodField()

    class Meta:
        model = VoucherCode
        fields = ['id', 'title', 'description', 'voucher_code', 'percentage', 'is_applied']

    def get_is_applied(self, instances):
        request = self.context.get('request')
        coupon_id = request.session.get('coupon_id', '')
        if coupon_id:
            if str(instances.pk) == coupon_id:
                return True
        else:
            return False


class CustomerSerializer(serializers.ModelSerializer):
    privilege_points = serializers.SerializerMethodField()
    default_address = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ['phone', 'name', 'email', 'privilege_points', 'default_address', 'image']

    def get_privilege_points(self, instance):
        request = self.context.get('request')
        points = get_privliged_points(request)

        return points

    def get_default_address(self, instances):
        request = self.context.get("request")
        addresses = CustomerAddress.objects.filter(is_default=True, is_deleted=False, customer__user=request.user)
        if addresses.exists():
            serialized = CustomerAddressSerializer(addresses.first())
            return serialized.data


class CustomerProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['phone', 'name', 'email']


class TimeSlotSerializer(serializers.ModelSerializer):
    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()

    class Meta:
        model = TimeSlot
        fields = ['day', 'start_time', 'end_time', 'id']

    def get_start_time(self, instances):
        return instances.start_time.strftime('%I:%M %p')

    def get_end_time(self, instances):
        return instances.end_time.strftime('%I:%M %p')


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Orders
        fields = ['payment_method', 'card_name', 'card_number', 'time_slot', 'delivery_date', 'delivery_note']
        optional_fields = ['']


class OrderItemSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    order_status = serializers.SerializerMethodField()
    is_cancelled = serializers.SerializerMethodField()
    is_returnable = serializers.SerializerMethodField()
    product_image = serializers.SerializerMethodField()
    product_name = serializers.SerializerMethodField()
    product_name_malayalam = serializers.SerializerMethodField()
    order_id = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = '__all__'

    def get_user(self, instances):
        return instances.order.customer.name

    def get_is_returnable(self, instances):
        return is_eligible_for_return(instances.product_variant_id, instances.order_id)

    def get_is_cancelled(self, instances):
        if instances.order.order_status == '40':
            return True
        return False

    def get_order_status(self, instances):
        order_status_data = {"name": instances.order.billing_name,
            "address": f"{instances.order.billing_address}, {instances.order.billing_landmark}, {instances.order.billing_city}, {instances.order.billing_state}",
            "phone": instances.order.billing_phone, "status": instances.order.order_status

        }
        return order_status_data

    def get_product_image(self, instances):
        request = self.context.get('request')
        if instances.product_variant.image:
            image_url = instances.product_variant.image.url
            return request.build_absolute_uri(image_url)

    def get_product_name(self, instances):
        if instances.product_variant.get_fullname():
            return instances.product_variant.get_fullname()

    def get_product_name_malayalam(self, instances):
        if instances.product_variant.get_malayalam_name():
            return instances.product_variant.get_malayalam_name()

    def get_order_id(self, instances):
        if instances.order:
            return instances.order.order_id


class BookingSerializer(serializers.ModelSerializer):
    product_image = serializers.SerializerMethodField()
    product_name = serializers.SerializerMethodField()
    product_name_malayalam = serializers.SerializerMethodField()
    product_category_malayalam = serializers.SerializerMethodField()
    product_category = serializers.SerializerMethodField()
    product_subcategory_malayalam = serializers.SerializerMethodField()
    product_subcategory = serializers.SerializerMethodField()
    product_mrp = serializers.SerializerMethodField()
    product_rating = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = '__all__'

    def get_product_image(self, instances):
        request = self.context.get('request')
        if instances.product_variant.image:
            image_url = instances.product_variant.image.url
            return request.build_absolute_uri(image_url)

    def get_product_name(self, instances):
        if instances.product_variant.get_fullname():
            return instances.product_variant.get_fullname()

    def get_product_name_malayalam(self, instances):
        if instances.product_variant.get_malayalam_name():
            return instances.product_variant.get_malayalam_name()

    def get_product_subcategory(self, instances):
        if instances.product_variant.product.subcategory:
            return instances.product_variant.product.subcategory.name

    def get_product_subcategory_malayalam(self, instances):
        if instances.product_variant.product.subcategory:
            return instances.product_variant.product.subcategory.malayalam_name

    def get_product_category(self, instances):
        if instances.product_variant.product.category:
            return instances.product_variant.product.category.name

    def get_product_category_malayalam(self, instances):
        if instances.product_variant.product.category:
            return instances.product_variant.product.category.malayalam_name

    def get_product_rating(self, instances):
        return instances.product_variant.current_rating

    def get_product_mrp(self, instances):
        request = self.context.get('request')
        if is_pincode_exists(request):
            pincode = get_pincode(request)
            if Batch.objects.filter(product_variant=instances.product_variant,
                                    warehouse__location__pincode=pincode).exists():
                batch_instance = Batch.objects.filter(product_variant=instances.product_variant,
                                                      warehouse__location__pincode=pincode).order_by(
                    '-date_added').first()
                return batch_instance.mrp


class TicketPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['description', 'attachment', 'subject']


class TicketsViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        exclude = ['auto_id', 'is_deleted', 'creator', 'updater']


class OrderItemRatingSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    delivered_time = serializers.SerializerMethodField()
    product_image = serializers.SerializerMethodField()
    product_name = serializers.SerializerMethodField()
    product_rating = serializers.SerializerMethodField()
    delivery_rating = serializers.SerializerMethodField()
    product_pk = serializers.SerializerMethodField()
    product_price = serializers.SerializerMethodField()
    product_category = serializers.SerializerMethodField()
    order_pk = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['user', 'description', 'delivered_time', 'product_image', 'product_name', 'product_rating',
                  'delivery_rating', 'product_pk', 'product_price', 'product_category', 'order_pk']

    def get_user(self, instances):
        return instances.order.customer.name

    def get_description(self, instances):
        return f"Your order for-{instances.product_variant.get_fullname()} successfully delivered"

    def get_delivered_time(self, instances):
        return instances.order.date_updated

    def get_product_image(self, instances):
        request = self.context.get('request')
        if instances.product_variant.image:
            image_url = instances.product_variant.image.url
            return request.build_absolute_uri(image_url)

    def get_product_name(self, instances):
        if instances.product_variant.get_fullname():
            return instances.product_variant.get_fullname()

    def get_product_rating(self, instances):
        request = self.context.get('request')
        if ProductReview.objects.filter(product_variant=instances.product_variant, creator=request.user, is_deleted=False):
            instance = ProductReview.objects.filter(product_variant=instances.product_variant, creator=request.user, is_deleted=False).first()
            return instance.rating

    def get_delivery_rating(self, instances):
        request = self.context.get('request')
        if DeliveryRating.objects.filter(order=instances.order, customer__user=request.user, is_deleted=False):
            instance = DeliveryRating.objects.filter(order=instances.order, customer__user=request.user, is_deleted=False).first()
            return instance.rating

    def get_product_pk(self, instances):
        if instances.product_variant.pk:
            return instances.product_variant.pk

    def get_product_price(self, instances):
        request = self.context.get("request")
        pincode = request.session.get('pincode', '')

        if pincode:
            # if a batch with zero stock exits it returns True
            if Batch.objects.filter(is_deleted=False, product_variant=instances.product_variant,
                                    warehouse__location__pincode=pincode).exists():
                batch_instances = Batch.objects.filter(is_deleted=False, product_variant=instances.product_variant,
                                                       warehouse__location__pincode=pincode).order_by(
                    '-date_added').first()
                return batch_instances.mrp

        return instances.product_variant.mrp

    def get_product_category(self, instances):
        if instances.product_variant.product.category:
            return instances.product_variant.product.category.name

    def get_order_pk(self, instances):
        if instances.order:
            return instances.order.pk


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductReview
        exclude = ['auto_id', 'creator', 'updater', 'product_variant']


class DeliveryRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryRating
        fields = ['rating', ]


class CustomerExportSerializer(serializers.ModelSerializer):
    total_orders = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ['phone', 'name', 'email', 'district', 'state', 'country', 'total_orders','current_privilege_points']

    def get_total_orders(self, instance):
        total_orders = Orders.objects.filter(customer=instance).count()
        return total_orders
