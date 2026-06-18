from django.conf.urls import url, include
from sales import views
from django.urls import path, re_path, include
from sales.views import SaleAutocomplete,SaleReturnAutocomplete

app_name = 'sales'

urlpatterns = [
    re_path(r'^sale-autocomplete/$', SaleAutocomplete.as_view(),name='sale_autocomplete'),
    re_path(r'^sale-return-autocomplete/$', SaleReturnAutocomplete.as_view(),name='sale_return_autocomplete'),

    re_path(r'^edit/(?P<pk>.*)/$', views.edit, name='edit'),
    re_path(r'^sales/$', views.sales, name='sales'),
    re_path(r'^create/$', views.create, name='create'),
    re_path(r'^view/(?P<pk>.*)/$', views.sale, name='sale'),
    re_path(r'^delete/(?P<pk>.*)/$', views.delete, name='delete'),
    re_path(r'^delete-selected-sales/$', views.delete_selected_sales,name='delete_selected_sales'),

    re_path(r'^print-sale/(?P<pk>.*)/$', views.print_sale, name='print_sale'),
    re_path(r'^print/invoice/(?P<pk>.*)/$',views.print_invoice, name='print_invoice'),

    re_path(r'^create-sale-return/$', views.create_sale_return_new,name='create_sale_return'),
    re_path(r'^sale-returns/$', views.sale_returns, name='sale_returns'),
    re_path(r'^view-sale-return/(?P<pk>.*)/$',views.sale_return, name='sale_return'),
    re_path(r'^cancel-sale-return/(?P<pk>.*)/$',views.delete_sale_return, name='delete_sale_return'),
    re_path(r'^edit-sale-return/(?P<pk>.*)/$',views.edit_sale_return, name='edit_sale_return'),
    re_path(r'^print/sale/return/(?P<pk>.*)/$',views.print_sale_return, name='print_sale_return'),

    re_path(r'^customer-from-create/$', views.customer_from_create,name='customer_from_create'),

    re_path(r'^get-customer/$', views.get_customer, name='get_customer'),
    re_path(r'^get-product/$', views.get_product_items,name='get_product_items'),
    re_path(r'^get-variant/$', views.get_varient, name='get_varient'),
    re_path(r'^get-product-variant/$', views.get_product_variant_items,name='get_product_variant_items'),

    re_path(r'^get-sale-items/$', views.get_sale_items, name='get_sale_items'),
    re_path(r'^get-sale-returns/$', views.get_sale_returns,name='get_sale_returns'),
    re_path(r'^get-sale-return-data/$', views.get_sale_return_amount,name='get_sale_return_amount'),
    re_path(r'^get-return-customer/$', views.get_return_customer,name='get_return_customer'),
    re_path(r'^get-prifix-sale-id/$', views.get_prifix_sale_id,name='get_prifix_sale_id'),
    re_path(r'^get-prifix-sale-type/$', views.get_prifix_sale_type,name='get_prifix_sale_type'),

    re_path(r'^sale-export/$', views.sale_export, name='sale_export'),

]
