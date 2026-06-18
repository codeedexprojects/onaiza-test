from django.conf.urls import url, include
from reports import views
from django.urls import path, re_path, include

app_name = 'reports'

urlpatterns = [
    re_path(r'^sales-report/$', views.sales_report, name='sales_report'),
    re_path(r'^print-sales-report/$', views.print_sales_report, name='print_sales_report'),

    re_path(r'^purchase-report/$', views.purchase_report, name='purchase_report'),
    re_path(r'^print-purchase-report/$', views.print_purchase_report, name='print_purchase_report'),

    re_path(r'^batch-stock-report/$', views.batch_stock_report, name='batch_stock_report'),

    re_path(r'^daily-report/$', views.daily_report, name='daily_report'),

    re_path(r'^ledger-book/$', views.ledger_report, name='ledger_report'),
    re_path(r'^trial-balance/$', views.trial_balance, name='trial_balance'),
    # re_path(r'^profit_and_loss/$', views.profit_and_loss, name='profit_and_loss'),

    re_path(r'^gst-r1-report/$', views.gstr1_report, name='gstr1_report'),
    re_path(r'^gst-r2-report/$', views.gstr2_report, name='gstr2_report'),
    re_path(r'^gst-r3-report/$', views.gstr3_report, name='gstr3_report'),

]