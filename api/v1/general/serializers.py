import datetime
import decimal

from rest_framework import pagination

from offers.models import Offers
from orders.models import OrderItem
from products.models import Category, ProductVariant, SubCategory, ProductImages
from rest_framework import serializers
from users.models import Wishlistitem, CartItem
from vendors.models import Vendor
from general.models import Batch
from web.models import ProductReview, SpotlightBanner
from customers.models import Customer

from purchases.models import Purchase

from sales.models import Sale

from products.models import Product

from products.templatetags.stock import get_total_stock


class BestOfferSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    product_name_malayalam = serializers.SerializerMethodField()
    mrp = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    is_cart = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    category_malayalam = serializers.SerializerMethodField()
    subcategory = serializers.SerializerMethodField()
    subcategory_malayalam = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    retail_price = serializers.SerializerMethodField()
    is_book_now_button = serializers.SerializerMethodField()

    class Meta:
        model = Offers
        fields = '__all__'

    def get_product_name(self, instances):
        if instances.product_variant:
            return instances.product_variant.get_fullname()
        return instances.title

    def get_product_name_malayalam(self, instances):
        if instances.product_variant:
            return instances.product_variant.get_malayalam_name()
        return instances.title

    def get_mrp(self, instances):
        if instances.product_variant:
            orginal_price = instances.product_variant.mrp
            offer_percent = instances.offer_percentage
            offer = orginal_price - (orginal_price * decimal.Decimal(float(offer_percent))) / 100
            return offer
        return 0

    def get_image(self, instances):
        request = self.context.get("request")
        if instances.image:
            image_url = instances.image.url
            return request.build_absolute_uri(image_url)
        elif instances.product_variant:
            if instances.product_variant.image:
                image_url = instances.product_variant.image.url
                return request.build_absolute_uri(image_url)
        return ""

    def get_is_cart(self, instances):
        request = self.context.get("request")
        if CartItem.objects.filter(product_variant=instances.product_variant, customer__user=request.user).exists():
            return True
        return False

    def get_category(self, instances):
        if instances.category:
            return instances.category.name
        elif instances.product_variant:
            return instances.product_variant.product.category.name
        return ''

    def get_category_malayalam(self, instances):
        if instances.category:
            return instances.category.malayalam_name
        elif instances.product_variant:
            return instances.product_variant.product.category.malayalam_name
        return ''

    def get_subcategory(self, instances):
        if instances.subcategory:
            return instances.subcategory.name
        elif instances.product_variant:
            return instances.product_variant.product.subcategory.name
        return ''

    def get_subcategory_malayalam(self, instances):
        if instances.subcategory:
            return instances.subcategory.malayalam_name
        elif instances.product_variant:
            return instances.product_variant.product.subcategory.malayalam_name
        return ''

    def get_rating(self, instances):
        if instances.product_variant:
            rating = '{0:.1f}'.format(instances.product_variant.current_rating)
            return str(rating)
        return 0

    def get_retail_price(self, instance):
        """
        if location exists the batch retail price is taken, if not exists the retail price is picked on product variant model
        :param instance:
        """
        request = self.context.get('request')

        if instance.product_variant:
            if 'pincode' in request.session:
                pincode_in_session = request.session.get('pincode', '')
                batch_instance = Batch.objects.filter(product_variant=instance.product_variant, warehouse__location__pincode=pincode_in_session).first()

                return batch_instance.retail_price
            else:
                return instance.product_variant.retail_price

    def get_is_book_now_button(self, instance):
        request = self.context.get("request")
        pincode = request.session.get('pincode', '')

        if pincode:
            # if a batch with zero stock exits it returns True
            if instance.product_variant:
                if Batch.objects.filter(product_variant=instance.product_variant, stock__gt=0, warehouse__location__pincode=pincode).exists():
                    return False
                else:
                    return True
            return None # offer is for product/category
        else:
            return None


class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = ['name', 'pk', 'malayalam_name']


class CategorySerializer(serializers.ModelSerializer):
    sub_category = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['name', 'is_featured', 'pk', 'sub_category', 'malayalam_name']

    def get_sub_category(self, instances):
        sub_category = SubCategory.objects.filter(category=instances)
        serialized = SubCategorySerializer(sub_category, many=True)
        return serialized.data


class BestSellersSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    malayalam_title = serializers.SerializerMethodField()
    is_wishlist = serializers.SerializerMethodField()
    is_cart = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    category_malayalam_name = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    retail_price = serializers.SerializerMethodField()
    is_book_now_button = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = ['id', 'title', 'image', 'mrp', 'current_rating', 'is_wishlist', 'is_cart', 'category',
                  'category_malayalam_name', 'malayalam_title', 'rating', 'retail_price', 'is_book_now_button']

    def get_is_wishlist(self, instances):
        request = self.context.get("request")
        if Wishlistitem.objects.filter(product_variant=instances, customer__user=request.user).exists():
            return True
        return False

    def get_title(self, instances):
        return str(instances)

    def get_malayalam_title(self, instances):
        return str(instances.get_malayalam_name())

    def get_is_cart(self, instances):
        request = self.context.get("request")
        if CartItem.objects.filter(product_variant=instances, customer__user=request.user).exists():
            return True
        return False

    def get_category(self, instances):
        if instances.product.category:
            return instances.product.category.name

    def get_category_malayalam_name(self, instances):
        if instances.product.category:
            return instances.product.category.malayalam_name

    def get_rating(self, instances):
        return round(instances.current_rating, 1)

    def get_retail_price(self, instance):
        """
        if location exists the batch retail price is taken, if not exists the retail price is picked on product variant model
        :param instance:
        """
        request = self.context.get('request')

        if 'pincode' in request.session:
            pincode_in_session = request.session.get('pincode', '')
            batch_instance = Batch.objects.filter(product_variant=instance, warehouse__location__pincode=pincode_in_session).first()

            if batch_instance:
                return round(batch_instance.retail_price, 2)
            else:
                return "Not added"

        else:
            if instance.retail_price:
                return round(instance.retail_price, 1)
            else:
                return "Not added"

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


class ShopSerializer(serializers.ModelSerializer):
    delivery_time = serializers.SerializerMethodField()
    delivery_fee = serializers.SerializerMethodField()
    location_name = serializers.SerializerMethodField()
    location_name_malayalam = serializers.SerializerMethodField()
    malayalam_name = serializers.SerializerMethodField()

    class Meta:
        model = Vendor
        fields = ['name', 'id', 'email', 'image', 'location', 'state', 'country', 'place', 'address', 'delivery_time',
                  'delivery_fee', 'location_name', 'malayalam_name', 'location_name_malayalam']

    def get_delivery_time(self, instances):
        return "25 m"

    def get_delivery_fee(self, instances):
        return "Free Shipping"

    def get_location_name(self, instances):
        return instances.location.name

    def get_location_name_malayalam(self, instances):
        return instances.location.malayalam_name

    def get_malayalam_name(self, instances):
        return instances.malayalam_name


class ProductSubVariantsSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        # exclude = ['auto_id', 'date_added', 'date_updated','mrp','creator','updater','is_deleted']
        fields = ['id', 'product_name', 'title']

    def get_product_name(self, instances):
        return str(instances.get_fullname())


class VairantImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImages
        fields = ['image', 'pk']


class ProductVariantSerializer(serializers.ModelSerializer):
    is_wishlist = serializers.SerializerMethodField()
    is_cart = serializers.SerializerMethodField()
    unit = serializers.SerializerMethodField()
    unit_of_measurement = serializers.SerializerMethodField()
    product_name = serializers.SerializerMethodField()
    product_name_malayalam = serializers.SerializerMethodField()
    cart_data = serializers.SerializerMethodField()
    off = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    malayalam_description = serializers.SerializerMethodField()
    meta_description = serializers.SerializerMethodField()
    is_book_now_button = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    category_malayalam = serializers.SerializerMethodField()
    price_data = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()
    product_review = serializers.SerializerMethodField()
    variant_images = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        exclude = ['auto_id', 'date_added', 'date_updated', 'creator', 'updater', 'deleted_reason', 'mrp']

    def get_is_wishlist(self, instances):
        request = self.context.get("request")
        if Wishlistitem.objects.filter(product_variant=instances, customer__user=request.user).exists():
            return True
        return False

    def get_is_cart(self, instances):
        request = self.context.get("request")
        if CartItem.objects.filter(product_variant=instances, customer__user=request.user).exists():
            return True
        return False

    def get_unit(self, instances):
        if instances.unit.unit:
            return instances.unit.unit

    def get_description(self, instance):
        return instance.product.description

    def get_malayalam_description(self, instance):
        return instance.product.malayalam_description

    def get_meta_description(self, instance):
        return instance.product.meta_description

    def get_unit_of_measurement(self, instance):
        if instance.product.unit_of_measurement:
            return instance.product.unit_of_measurement.unit_of_measurement

    def get_product_name(self, instances):
        return str(instances.get_fullname())

    def get_product_name_malayalam(self, instances):
        return str(instances.get_malayalam_name())

    def get_cart_data(self, instances):
        request = self.context.get("request")
        if CartItem.objects.filter(product_variant=instances, customer__user=request.user).exists():
            cart_instance = CartItem.objects.get(product_variant=instances, customer__user=request.user)

            return {"id": cart_instance.pk, "qty": cart_instance.qty, }
        return ""

    def get_category(self, instances):
        return instances.product.category.name

    def get_category_malayalam(self, instances):
        return instances.product.category.malayalam_name

    def get_off(self, instances):
        return 0

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

    def get_price_data(self, instances):
        request = self.context.get("request")
        pincode = request.session.get('pincode', '')
        today = datetime.datetime.now()

        if pincode:
            # if a batch with zero stock exits it returns True
            if Batch.objects.filter(is_deleted=False, product_variant=instances,
                                    warehouse__location__pincode=pincode).exists():
                batch_instances = Batch.objects.filter(is_deleted=False, product_variant=instances,
                                                       warehouse__location__pincode=pincode).order_by(
                    '-date_added').first()
                off = ((batch_instances.mrp - batch_instances.retail_price) / batch_instances.mrp) * 100
                return {'mrp': batch_instances.mrp, 'price': batch_instances.retail_price, 'off': round(off, 1)}

        off = ((instances.mrp - instances.retail_price) / instances.mrp) * 100
        return {'mrp': instances.mrp, 'price': instances.retail_price, 'off': round(off, 1)}

    def get_variants(self, instances):
        request = self.context.get("request")
        variant_instances = ProductVariant.objects.filter(product=instances.product, is_admin_approved=True).exclude(pk=instances.pk)
        serialized = ProductSubVariantsSerializer(variant_instances, context={"request": request}, many=True)
        return serialized.data

    def get_product_review(self, instances):
        product_review_instances_count = ProductReview.objects.filter(product_variant=instances,
                                                                      is_deleted=False).count()
        reviews = {"total_customer_rating": str(product_review_instances_count),
                   "product_rating": str(round(instances.current_rating, 1))}
        return reviews

    def get_variant_images(self, instance):
        request = self.context.get("request")
        instances = ProductImages.objects.filter(product_variant=instance)

        serialized = VairantImageSerializer(instances, context={"request": request}, many=True)

        return serialized.data


class OfferSlidersSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    subcategory = serializers.SerializerMethodField()
    product_variant_name = serializers.SerializerMethodField()
    product_variant_name_malayalam = serializers.SerializerMethodField()

    class Meta:
        model = Offers
        fields = '__all__'

    def get_category(self, instances):
        if instances.category:
            return {'name': instances.category.name, 'id': instances.category.pk,
                    'malayalam_name': instances.category.malayalam_name, }

    def get_subcategory(self, instances):
        if instances.subcategory:
            return {'name': instances.subcategory.name, 'id': instances.subcategory.id,
                    'malayalam_name': instances.subcategory.malayalam_name, }

    def get_product_variant_name(self, instances):
        if instances.product_variant:
            return instances.product_variant.get_fullname()

    def get_product_variant_name_malayalam(self, instances):
        if instances.product_variant:
            return instances.product_variant.get_malayalam_name()


class ProductReviewSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProductReview
        fields = ['rating', 'review', 'name', 'image']

    def get_name(self, instances):
        if instances.creator:
            customer_instance = Customer.objects.get(user=instances.creator)
            return customer_instance.name

    def get_image(self, instances):
        customer_instance = Customer.objects.get(user=instances.creator)
        request = self.context.get('request')
        if customer_instance.image:
            image_url = customer_instance.image.url
            return request.build_absolute_uri(image_url)


class PurchaseExportSerializer(serializers.ModelSerializer):
    supplier_name = serializers.SerializerMethodField()
    warehouse_name = serializers.SerializerMethodField()

    class Meta:
        model = Purchase
        fields = ['date', 'purchase_no', 'purchase_id', 'warehouse_name', 'supplier_name', 'product_total', 'discount',
                  'round_off', 'paid', 'payment_method']

    def get_supplier_name(self, instance):
        if instance.supplier:
            return instance.supplier.name
        else:
            return "-"

    def get_warehouse_name(self, instance):
        if instance.warehouse:
            return instance.warehouse.name
        else:
            return "-"


class SaleExportSerializer(serializers.ModelSerializer):
    warehouse_name = serializers.SerializerMethodField()

    class Meta:
        model = Sale
        exclude = ['id', 'is_deleted', 'date_added', 'date_updated', 'deleted_reason', 'is_updated', 'add_gst',
                   'customer', 'creator', 'updater', 'auto_id', 'receipt_voucher', 'warehouse', 'sale_prifix']

    def get_warehouse_name(self, instance):
        if instance.warehouse:
            return instance.warehouse.name
        else:
            return "-"


class VariantExportSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    unit_name = serializers.SerializerMethodField()
    warehouse_name = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        exclude = ['id', 'product', 'warehouse', 'unit', 'unit_of_measurement', 'is_deleted', 'auto_id',
                   'deleted_reason', 'is_default', 'creator', 'updater', 'gst_included', 'image', 'date_added',
                   'date_updated']

    def get_product_name(self, instance):
        if instance.product:
            return instance.product.name
        else:
            return "-"

    def get_unit_name(self, instance):
        if instance.unit:
            return instance.unit.unit
        else:
            return "-"

    def get_warehouse_name(self, instance):
        if instance.warehouse:
            return instance.warehouse.name
        else:
            return "-"


class ProductExportSerializer(serializers.ModelSerializer):
    brand_name = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    subcategory_name = serializers.SerializerMethodField()
    hsn_code = serializers.SerializerMethodField()
    vendor_name = serializers.SerializerMethodField()
    total_stock = serializers.SerializerMethodField()
    unit_of_measurement_name = serializers.SerializerMethodField()

    class Meta:
        model = Product
        exclude = ['id', 'is_deleted', 'date_added', 'date_updated', 'deleted_reason', 'creator', 'updater', 'auto_id',
                   'malayalam_name', 'image', 'brand', 'category', 'subcategory', 'hsn', 'vendor']

    def get_brand_name(self, instance):
        if instance.brand:
            return instance.brand.name
        else:
            return "-"

    def get_category_name(self, instance):
        if instance.category:
            return instance.category.name
        else:
            return "-"

    def get_unit_of_measurement_name(self, instance):
        if instance.unit_of_measurement:
            return instance.unit_of_measurement.unit_of_measurement
        else:
            return "-"

    def get_subcategory_name(self, instance):
        if instance.subcategory:
            return instance.subcategory.name
        else:
            return "-"

    def get_hsn_code(self, instance):
        if instance.hsn:
            return instance.hsn.hsn_number
        else:
            return "-"

    def get_vendor_name(self, instance):
        if instance.vendor:
            return instance.vendor.name
        else:
            return "-"

    def get_total_stock(self,instance):
        total_stock = get_total_stock(instance)
        return total_stock


class BannerSerializer(serializers.ModelSerializer):

    class Meta:
        model = SpotlightBanner
        fields = "__all__"