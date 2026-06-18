from customers.models import Customer

# customer, sales, orders, products
from django.db.models import Q
from django.db.models.functions import Lower

from products.models import ProductVariant


class InstancesManager:
    def __init__(self, request):
        self.request = request

    def get_instances_depend_on_params(self):
        """
        get instances and filter based on request params
        :return:
        """
        instances = Customer.objects.filter(is_deleted=False)

        request = self.request.GET
        view = request.get('view')
        balance_type = request.get('balance_type')
        sort_by = request.get('sort_by')
        order_by = request.get('order_by')

        if view:
            if 'view_all' in view:
                instances = Customer.objects.filter(is_deleted=False)

            if 'online' in view:
                instances = instances.filter(user__isnull=False)

            if 'offline' in view:
                print("Offline")
                instances = instances.filter(user__isnull=True)

        if balance_type:
            if 'credit' in balance_type:
                instances = instances.filter(opening_type='debit')

            if 'debit' in balance_type:
                instances = instances.filter(opening_type='credit')

        if sort_by:
            pass

        if order_by:
            if 'asc' in order_by:
                instances = instances.order_by('auto_id')

            if 'desc' in order_by:
                instances = instances.order_by('-auto_id')

        return instances

    def get_product_variant_instances_depend_on_params(self,product_instance):
        product_variant_instances = ProductVariant.objects.filter(product=product_instance, is_admin_approved=True)
        return product_variant_instances
