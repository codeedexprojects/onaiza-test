from products.models import Category, Brand, SubCategory, HsnCodes
from vendors.models import Vendor


class VendorFunctionsManager:

    def get_vendor(self,user):
        return Vendor.objects.get(user=user)

    def non_approved_categories(self, user):
        return Category.objects.filter(is_deleted=False, vendor_created=True, is_admin_approved=None, creator=user)

    def approved_categories(self, user):
        return Category.objects.filter(is_deleted=False, vendor_created=True, is_admin_approved=True, creator=user)

    def cancelled_categories(self, user):
        return Category.objects.filter(is_deleted=False, vendor_created=True, is_admin_approved=False, creator=user)

    def non_approved_brands(self, user):
        return Brand.objects.filter(is_deleted=False, vendor_created=True, is_admin_approved=None, creator=user)

    def approved_brands(self, user):
        return Brand.objects.filter(is_deleted=False, vendor_created=True, is_admin_approved=True, creator=user)

    def cancelled_brands(self, user):
        return Brand.objects.filter(is_deleted=False, vendor_created=True, is_admin_approved=False, creator=user)

    def get_approved_subcategories(self, user):
        return SubCategory.objects.filter(is_deleted=False, vendor_created=True, is_admin_approved=True, creator=user)

    def get_non_approved_subcategories(self, user):
        return SubCategory.objects.filter(is_deleted=False, vendor_created=True, is_admin_approved=None, creator=user)

    def get_cancelled_subcategories(self, user):
        return SubCategory.objects.filter(is_deleted=False, vendor_created=True, is_admin_approved=False, creator=user)

    def get_hsn_codes(self, user):
        return HsnCodes.objects.filter(creator=user,is_deleted=False)

    def get_queried_instances(self, request):
        query = request.GET.get('query')
        condition = request.GET.get('condition')
        instances = None

        if 'brands' in query and 'non-approved' in condition:
            instances = self.non_approved_brands(request.user)

        elif 'brands' in query and 'approved' in condition:
            instances = self.approved_brands(request.user)

        if 'category' in query and 'non-approved' in condition:
            instances = self.non_approved_categories(request.user)

        elif 'category' in query and 'approved' in condition:
            instances = self.approved_categories(request.user)

        elif 'category' in query and 'cancelled' in condition:
            instances = self.cancelled_categories(request.user)

        if 'sub-category' in query and 'non-approved' in condition:
            instances = self.get_non_approved_subcategories(request.user)

        elif 'sub-category' in query and 'approved' in condition:
            instances = self.get_approved_subcategories(request.user)

        return instances

    def decline_category(self, instance):
        instance.is_admin_approved = False
        instance.save()
        return True

    def approve_brand(self, instance):
        instance.is_admin_approved = True
        instance.save()
        return True

    def approve(self, instance):
        instance.is_admin_approved = True
        instance.save()
        return True
