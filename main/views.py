from django.shortcuts import render, get_object_or_404
from django.http.response import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
import json
from django.views.decorators.http import require_GET
from django.core import serializers
from django.contrib.auth.models import Group
from django.db.models import Sum, Q, F
import datetime
import re
from django.http import JsonResponse
from customers.models import Customer
from finance.models import AccountHead
from main.decorators import role_required
from django.utils.translation import activate
from django.utils import translation
from orders.models import Orders, OrderItem
# from finance.functions import get_ledger_data
from sales.models import Sale, SaleItem


@login_required
@role_required(['superadmin', 'warehouse_manager', 'normal_staff', 'billing_staff', 'vendor_user'])
def app(request):
    return HttpResponseRedirect(reverse('dashboard'))


@login_required
@role_required(['superadmin', 'warehouse_manager', 'normal_staff', 'billing_staff','vendor_user'])
def dashboard(request):
    today = datetime.datetime.now()
    no_of_oders = 0
    no_of_sales = 0
    no_of_pending_orders = 0
    no_of_shipped_orders = 0
    no_of_delivered_orders = 0
    no_of_cancelled_orders = 0

    sale_total = 0
    order_subtotal = 0

    orders = Orders.objects.filter(is_deleted=False).order_by('-date_added')
    invoices = Sale.objects.filter(is_deleted=False).order_by('-date_added')[:5]
    customers = Customer.objects.filter(is_deleted=False).order_by('-date_added')[:5]

    pending_orders = orders.filter(order_status="10")[:10]
    shipped_orders = orders.filter(order_status="20")[:10]
    delivered_orders = orders.filter(order_status="30")[:10]
    cancelled_orders = orders.filter(order_status="40")[:10]

    no_of_oders = orders.count()
    no_of_pending_orders = pending_orders.count()
    no_of_shipped_orders = shipped_orders.count()
    no_of_delivered_orders = delivered_orders.count()
    no_of_cancelled_orders = cancelled_orders.count()
    order_subtotal = orders.aggregate(total_amt=Sum('total_amt')).get("total_amt", 0)

    orders = orders[:5]

    if Sale.objects.filter(is_deleted=False, date_added__date=today.date()).exists():
        sales = Sale.objects.filter(is_deleted=False, date_added__date=today.date())
        no_of_sales = sales.count()

        if sales.filter(paid__lt=F('total')).exists():
            credit_sale_total = sales.filter(paid__lt=F('total')).annotate(balance=F('total')-F('paid')).aggregate(new_balance=Sum('balance')).get('new_balance', 0)
            credit_sale_count = sales.filter(paid__lt=F('total')).count()

        sale_items = SaleItem.objects.filter(sale__in=sales)
        sale_total = sales.aggregate(total=Sum('total')).get("total", 0)

    context = {
        "title": "Dashboard",

        "order_subtotal": order_subtotal, # order_subtotal,
        "sale_subtotal": sale_total,

        "no_of_sales":no_of_sales,
        "no_of_oders":no_of_oders,
        "no_of_pending_orders":no_of_pending_orders,
        "no_of_shipped_orders":no_of_shipped_orders,
        "no_of_delivered_orders":no_of_delivered_orders,
        "no_of_cancelled_orders":no_of_cancelled_orders,

        "orders":orders,
        "invoices":invoices,
        "customers":customers,
        "pending_orders":pending_orders,
        "shipped_orders":shipped_orders,
        "delivered_orders":delivered_orders,
        "cancelled_orders":cancelled_orders,

    }
    return render(request, "base.html", context)


@login_required
def check_password_policy(request):
    username = request.GET.get('username')
    password1 = request.GET.get('password1')
    s = password1
    regex = re.compile('[@_!#$%^&*()<>?/\|}{~:]')
    regex1 = re.compile('[A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z]')
    regex2 = re.compile('[123456789]')

    l = len(password1)
    if s.find(username) == -1 and l > 8 and (regex.search(password1) != None) and (regex1.search(password1) != None) and (regex2.search(password1) != None):
        response_data = {
            "status": "true",
        }
    else:
        response_data = {
            "status": "false",
        }
    return JsonResponse(response_data)


def switch_language(request):
    lang = request.GET.get('language') # accepting value choosen by client
    next = request.GET.get('next')
    language = translation.get_language() # this will return current active language

    if lang == "en":
        activate('en')
    elif lang == "ml":
        activate('ml')

    # return HttpResponseRedirect(next)
    return HttpResponseRedirect(reverse('web:index'))


