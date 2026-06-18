from django.urls import path, re_path
from django.conf.urls import url, include
from purchases import views
from django.views.generic import TemplateView
from purchases.views import PurchaseAutocomplete,PurchaseReturnAutocomplete

app_name = "purchases"

urlpatterns = [
    re_path(r'^purchase-autocomplete/$',
            PurchaseAutocomplete.as_view(), name='purchase_autocomplete'),
   re_path(r'^purchase-return-autocomplete/$',
            PurchaseReturnAutocomplete.as_view(), name='purchase_return_autocomplete'),

    re_path(r'^get-purchase-items/$', views.get_purchase_items,
            name='get_purchase_items'),

    re_path(r'^create-purchase/$', views.create_new_purchase,
            name='create_new_purchase'),
    re_path(r'^purchases/', views.purchases, name='purchases'),
    re_path(r'^single-purchase/(?P<pk>.*)/$', views.purchase, name='purchase'),
    re_path(r'^purchase/edit/(?P<pk>.*)/$',
            views.edit_purchase, name='edit_purchase'),
    re_path(r'^purchase/delete/(?P<pk>.*)/$',
            views.delete_purchase, name='delete_purchase'),

    re_path(r'^get-customer/$', views.get_customer, name='get_customer'),
    # re_path(r'^get-product-stock$', views.get_product_stock,
    #         name='get_product_stock'),

    re_path(r'^print-purchase/(?P<pk>.*)/$',
            views.print_purchase, name='print_purchase'),

    re_path(r'^create-purchase-return/',
            views.create_purchase_return_new, name='create_purchase_return'),
    re_path(r'^purchase-returns/$', views.purchase_returns,
            name='purchase_returns'),
    re_path(r'^view-purchase-return/(?P<pk>.*)/$',
            views.purchase_return, name='purchase_return'),
    re_path(r'^purchase-return/edit/(?P<pk>.*)/$',
            views.edit_purchase_return_new, name='edit_purchase_return'),
    re_path(r'^purchase-return/cancel/(?P<pk>.*)/$',
            views.delete_purchase_return, name='delete_purchase_return'),
    re_path(r'^delete-selected-purchase-returns/',
            views.delete_selected_purchase_return, name='delete_selected_purchase_return'),
    re_path(r'^print-purchase-return/(?P<pk>.*)/$',
            views.print_purchase_return, name='print_purchase_return'),
    re_path(r'^get-purchase-returns/$', views.get_purchase_returns,name='get_purchase_returns'),
    re_path(r'^get-purchase-return-data/$', views.get_purchase_return_amount,name='get_purchase_return_amount'),
    re_path(r'^get-purchase-return-supplier/$', views.get_purchase_return_supplier,name='get_purchase_return_supplier'),
    re_path(r'^get-prifix-purchase-id/$', views.get_prifix_purchase_id,name='get_prifix_purchase_id'),


    re_path(r'^create-purchase-order/$', views.create_purchase_order,name='create_purchase_order'),
    re_path(r'^purchase-orders/$', views.purchase_orders,name='purchase_orders'),
    re_path(r'^view-purchase-order/(?P<pk>.*)/$', views.purchase_order,name='purchase_order'),
    re_path(r'^delete-purchase-order/(?P<pk>.*)/$', views.delete_order_purchase,name='delete_order_purchase'),
    re_path(r'^edit-purchase-order/(?P<pk>.*)/$', views.edit_purchase_order,name='edit_purchase_order'),
    re_path(r'^save-purchase-order/(?P<pk>.*)/$', views.save_purchase, name='save_purchase'),
    re_path(r'^print-purchase-order/(?P<pk>.*)/$', views.print_purchase_order, name='print_purchase_order'),


    re_path(r'^purchase-export/$',
            views.purchase_export, name='purchase_export'),
]
