from .models import Supplier


def get_all_suppliers():
    suppliers = Supplier.objects.filter(is_deleted=False)
    return suppliers