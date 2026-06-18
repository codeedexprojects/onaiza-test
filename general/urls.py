from django.conf.urls import url, include
from django.contrib import admin
from general import views
from django.urls import path, re_path
from dal import autocomplete

app_name = "general"

urlpatterns = [
    # path('batch-autocomplete/', BatchAutocomplete.as_view(), name='batch_autocomplete'),
    re_path(r'^get-batch-data/$', views.get_batch_data, name='get_batch_data'),

    re_path(r'^create-damaged-product/$', views.create_damaged_product,name='create_damaged_product'),
    re_path(r'^damaged-products/', views.damaged_products,name='damaged_products'),
    re_path(r'^view-damaged_product/(?P<pk>.*)/$',views.damaged_product, name='damaged_product'),
    re_path(r'^edit-damaged_product/(?P<pk>.*)/$',views.edit_damaged_product, name='edit_damaged_product'),
    re_path(r'^delete-damaged_product/(?P<pk>.*)/$',views.delete_damaged_product, name='delete_damaged_product'),

    re_path(r'^create-stock-transfer/$', views.create_stock_transfer,name='create_stock_transfer'),
    re_path(r'^stock-transfers/$', views.stock_transfers, name='stock_transfers'),
    re_path(r'^edit-stock-transfer/(?P<pk>.*)/$',views.edit_stock_transfer, name='edit_stock_transfer'),
    re_path(r'^view-stock-transfer/(?P<pk>.*)/$',views.stock_transfer, name='stock_transfer'),
    re_path(r'^delete-stock-transfer/(?P<pk>.*)/$',views.delete_stock_transfer, name='delete_stock_transfer'),

    re_path(r'^stock-updates/$', views.stock_updates, name='stock_updates'),
    re_path(r'^view-stock-update/(?P<pk>.*)/$', views.update_stock, name='update_stock'),
    re_path(r'^edit-stock-update/(?P<pk>.*)/$', views.edit_update_stock, name='edit_update_stock'),
    re_path(r'^delete-stock-update/(?P<pk>.*)/$', views.delete_stock_update, name='delete_stock_update'),
    re_path(r'^create-stock-outward/$', views.create_outward_stock, name='create_outward_stock'),
    re_path(r'^create-stock-inward/$', views.create_inward_stock, name='create_inward_stock'),

    path('create-invoice_design/', views.create_invoice_design, name='create_invoice_design'),
    path('invoice_designs/', views.invoice_designs, name='invoice_designs'),
    re_path(r'^edit-invoice_design/(?P<pk>.*)/$', views.edit_invoice_design, name='edit_invoice_design'),
    re_path(r'^view-invoice_design/(?P<pk>.*)/$', views.invoice_design, name='invoice_design'),
    re_path(r'^delete-invoice_design/(?P<pk>.*)/$',views.delete_invoice_design, name='delete_invoice_design'),
    path('delete-selected-invoice_designs/', views.delete_selected_invoice_designs,name='delete_selected_invoice_designs'),

]
