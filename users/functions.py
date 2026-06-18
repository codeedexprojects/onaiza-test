from staffs.models import Staff
from customers.models import Customer
from warehouses.models import Warehouse


def get_user(user):
    print("======>>><><>>", user)
    user = Customer.objects.get(user=user)
    return user


def get_warehouse(request):
    warehouse = None
    if Staff.objects.filter(user=request.user, warehouse__isnull=False).exists():
        warehouse = Staff.objects.get(user=request.user, warehouse__isnull=False).warehouse
    else:
        if request.method == 'GET':
            try:
                if request.GET.get("warehouse"):
                    if Warehouse.objects.filter(pk=request.GET.get("warehouse")).exists():
                        warehouse = Warehouse.objects.get(pk=request.GET.get("warehouse"))
            except:
                pass

    return warehouse
