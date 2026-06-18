from vendors.models import VendorCommission
from products.models import Product, ProductVariant
from sales.models import Sale
from general.models import Batch
import datetime


def update_batch_stock(pk, quantity, status):

    if Batch.objects.filter(pk=pk).exists():
        batch = Batch.objects.get(pk=pk)
        stock = batch.stock

        if status == "increase":
            balance_stock = stock + quantity
        elif status == "decrease":
            balance_stock = stock - quantity

        batch.stock = balance_stock
        batch.save()

        if batch.product_variant:
            print(batch.product_variant.total_stock)


def get_sale_invoice_id(request):
    sale_no = 1

    if Sale.objects.all().exists():
        latest_sale_no = Sale.objects.all().latest('auto_id').sale_no
    else:
        latest_sale_no = 0
    sale_no = int(float(latest_sale_no)) + 1

    # sale_id = app_settings.sale_prefix + str(sale_no)
    return sale_no

def get_week(date):
    import datetime
    date = datetime.date.today()
    start_week = date - datetime.timedelta(date.weekday())
    end_week = start_week + datetime.timedelta(7)
    print(start_week,end_week)
    return[start_week,end_week]


def create_or_update_commission(sale_date,vendor,sub_total):
    # today = datetime.date.today()
    today = sale_date.date()
    print(today,"TESTINGGGGGG",sale_date.date(),type(sale_date))
    commission_amount = 0
    if vendor:
        commission_type = vendor.commission_type
        commission_percentage = vendor.commission_percentage
        commission_amount = commission_percentage/100*sub_total
        if commission_type == "product_based":
            commission_amount = commission_percentage/100*sub_total
        elif commission_type == "monthly":
            if VendorCommission.objects.filter(is_paid=False,vendor=vendor,date__month=today.month,date__year=today.year).exists():
                monthly_commission = VendorCommission.objects.get(is_paid=False,vendor=vendor,date__month=today.month,date__year=today.year)
                print("iffff",commission_type,commission_percentage)
                new_commission_amount = monthly_commission.commission_amount + commission_amount
                monthly_commission.commission_amount = new_commission_amount
                monthly_commission.save()
            else:
                print(type(today.month),today.year,"elseeee",commission_type,commission_percentage)
                VendorCommission.objects.create(
                    date=today,
                    vendor=vendor,
                    commission_amount=commission_amount,
                    is_paid=False,
                    )
        elif commission_type == "weekly":

            start_week = get_week(today)[0]
            end_week = get_week(today)[1]
            if VendorCommission.objects.filter(is_paid=False,vendor=vendor,date__lte=end_week,date__gte=start_week).exists():
                weekly_commission = VendorCommission.objects.filter(is_paid=False,vendor=vendor,date__lte=end_week,date__gte=start_week).first()
                new_commission_amount = weekly_commission.commission_amount + commission_amount
                weekly_commission.commission_amount = new_commission_amount
                weekly_commission.save()
            else:
                VendorCommission.objects.create(
                    date=today,
                    vendor=vendor,
                    commission_amount=commission_amount,
                    is_paid=False,
                    )
        elif commission_type == "daily":
            if VendorCommission.objects.filter(is_paid=False,vendor=vendor,date=today).exists():
                daily_commission = VendorCommission.objects.get(is_paid=False,vendor=vendor,date=today)
                new_commission_amount = daily_commission.commission_amount + commission_amount
                daily_commission.commission_amount = new_commission_amount
                daily_commission.save()
            else:
                VendorCommission.objects.create(
                    date=today,
                    vendor=vendor,
                    commission_amount=commission_amount,
                    is_paid=False,
                    )
    return commission_amount

def return_commission(sale_date,vendor,old_commission_amount):
    # today = datetime.date.today()
    today = sale_date.date()
    print(today,"TESTINGGGGGG",sale_date.date(),type(sale_date))
    commission_amount = 0
    if vendor:
        commission_type = vendor.commission_type
        commission_percentage = vendor.commission_percentage
        commission_amount = old_commission_amount
        if commission_type == "product_based":
            pass
        elif commission_type == "monthly":
            if VendorCommission.objects.filter(is_paid=False,vendor=vendor,date__month=today.month,date__year=today.year).exists():
                monthly_commission = VendorCommission.objects.get(is_paid=False,vendor=vendor,date__month=today.month,date__year=today.year)
                print("iffff",commission_type,commission_percentage)
                new_commission_amount = monthly_commission.commission_amount - commission_amount
                monthly_commission.commission_amount = new_commission_amount
                monthly_commission.save()

        elif commission_type == "weekly":

            start_week = get_week(today)[0]
            end_week = get_week(today)[1]
            if VendorCommission.objects.filter(is_paid=False,vendor=vendor,date__lte=end_week,date__gte=start_week).exists():
                weekly_commission = VendorCommission.objects.filter(is_paid=False,vendor=vendor,date__lte=end_week,date__gte=start_week).first()
                new_commission_amount = weekly_commission.commission_amount - commission_amount
                weekly_commission.commission_amount = new_commission_amount
                weekly_commission.save()

        elif commission_type == "daily":
            if VendorCommission.objects.filter(is_paid=False,vendor=vendor,date=today).exists():
                daily_commission = VendorCommission.objects.get(is_paid=False,vendor=vendor,date=today)
                new_commission_amount = daily_commission.commission_amount - commission_amount
                daily_commission.commission_amount = new_commission_amount
                daily_commission.save()
