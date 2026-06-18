from dal import autocomplete
from django.db.models import Q

from products.models import Brand, Category, SubCategory


class VendorBrandAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        user = self.request.user
        items = Brand.objects.filter(is_deleted=False, is_admin_approved=True, creator=user)

        if self.q:
            items = items.filter(Q(auto_id__istartswith=self.q) | Q(name__istartswith=self.q))

        return items


class VendorCategoryAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        user = self.request.user
        items = Category.objects.filter(is_deleted=False, is_admin_approved=True, creator=user)

        if self.q:
            items = items.filter(Q(auto_id__istartswith=self.q) | Q(name__istartswith=self.q))

        return items


class VendorSubcategoryAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        user = self.request.user
        items = SubCategory.objects.filter(is_deleted=False, is_admin_approved=True, creator=user)
        category = self.forwarded.get('category', None)

        if category:
            items = items.filter(category=category)
        if self.q:
            items = items.filter(Q(auto_id__istartswith=self.q) | Q(name__istartswith=self.q))
        return items
