from django.shortcuts import get_object_or_404

from products.models import Product


class ProductUtils:

    def check_status(self, instance):
        if instance.is_active:
            return True
        else:
            return False

    def disable(self,instance):
        instance.is_active = False
        instance.save()
        return "disabled"

    def enable(self,instance):
        instance.is_active = True
        instance.save()
        return "enabled"


    def enable_or_disable_product_status(self,pk):
        instance = get_object_or_404(
            Product.objects.filter(pk=pk, is_deleted=False))

        is_active = self.check_status(instance)
        response_data = {}

        if is_active:
            self.disable(instance)
            response_data['message'] = f"Product {instance.name} is enabled"

        else:
            self.enable(instance)
            response_data['message'] = f"Product {instance.name} is disabled"

        print(response_data,"<<<++++")

        return response_data


