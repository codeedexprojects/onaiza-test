from products.models import Category,Brand
from vendors.models import Vendor


def update_vendor_credit_debit(pk, transaction_type, amount):
    if amount > 0:
        vendor = Vendor.objects.get(pk=pk)
        opening_type = vendor.opening_type
        current_balance = vendor.current_balance
        if opening_type == "credit":
            debit = 0
            credit = current_balance
        elif opening_type == "debit":
            debit = 0
            credit = current_balance

        vendor_objects = Vendor.objects.filter(pk=pk)

        if transaction_type == "credit":
            if debit > 0:
                debit_balance = debit - amount
                if debit_balance < 0:
                    abs_debit_balance = abs(debit_balance)
                    vendor_objects.update(current_balance=abs_debit_balance)
                else:
                    vendor_objects.update(current_balance=debit_balance)
            else:
                vendor_objects.update(current_balance=credit + amount)

        elif transaction_type == "debit":
            if credit > 0:
                credit_balance = credit - amount
                if credit_balance < 0:
                    abs_credit_balance = abs(credit_balance)
                    vendor_objects.update(current_balance=abs_credit_balance)
                else:
                    vendor_objects.update(current_balance=credit_balance)
            else:
                vendor_objects.update(current_balance=debit + amount)


def get_vendor_credit(pk):
    vendor = Vendor.objects.get(pk=pk)
    current_balance = vendor.current_balance
    return current_balance


def get_vendor_debit(pk):
    vendor = Vendor.objects.get(pk=pk)
    current_balance = vendor.current_balance
    return current_balance


def get_all_vendors():
    vendors = Vendor.objects.filter(is_deleted=False)
    return vendors


def get_vendor_categories(user):
    instances = Category.objects.filter(creator=user)
    return instances


def get_vendor_brands(user):
    instances = Brand.objects.filter(creator=user)
    return instances

def if_vendor_is_user(request):
    try:
        print(request.user.vendor)
        return True
    except:
        return False