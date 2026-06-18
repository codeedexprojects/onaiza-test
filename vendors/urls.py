from django.urls import path, re_path
from vendors.views import VendorAutocomplete
from vendors import views

app_name = "vendors"


urlpatterns = [

    re_path(r'^vendor-autocomplete/$', VendorAutocomplete.as_view(), name='vendor_autocomplete'),
    re_path(r'^get-vendors/$', views.get_vendors, name='get_vendors'),
    re_path(r'^get-vendor-data/$', views.get_vendor_data, name='get_vendor_data'),
    re_path(r'^get-balance/$',views.get_balance, name='get_balance'),

    re_path(r'^vendor/pop-up-create/$', views.add_new_vendor, name='add_new_vendor'),

    re_path(r'^create/$', views.create_vendor, name='create_vendor'),
    re_path(r'^$', views.vendors, name='vendors'),
    re_path(r'^edit/(?P<pk>.*)/$', views.edit_vendor, name='edit_vendor'),
    re_path(r'^view/(?P<pk>.*)/$', views.vendor, name='vendor'),
    re_path(r'^delete/(?P<pk>.*)/$', views.delete_vendor, name='delete_vendor'),
    re_path(r'^delete-selected/$', views.delete_selected_vendors, name='delete_selected_vendors'),

    re_path(r'^vendor-activites/$', views.vendor_activities, name='vendor_activities'),

    re_path(r'^create-category/$', views.vendor_create_category, name='vendor_create_category'),
    re_path(r'^create-brand/$', views.vendor_create_brand, name='vendor_create_brand'),
    re_path(r'^create-sub_category/$', views.vendor_create_sub_category, name='vendor_create_sub_category'),
    re_path(r'^create-product/$', views.vendor_create_product, name='vendor_create_product'),

    re_path(r'^brands/$', views.vendor_brands, name='vendor_brands'),
    re_path(r'^categories/$', views.vendor_categories, name='vendor_categories'),
    re_path(r'^sub-categories/$', views.vendor_sub_categories, name='vendor_sub_categories'),
    re_path(r'^products/$', views.vendor_products, name='vendor_products'),

    re_path(r'^product/approve/(?P<pk>.*)/$', views.approve_vendor_product, name='approve_vendor_product'),
    re_path(r'^product/decline/(?P<pk>.*)/$', views.decline_vendor_product, name='decline_vendor_product'),
    re_path(r'^approve-(?P<item_type>.*)/(?P<pk>.*)/$', views.approve_vendor_item, name='approve_vendor_item'),
    re_path(r'^decline-(?P<item_type>.*)/(?P<pk>.*)/$', views.decline_vendor_item, name='decline_vendor_item'),

    re_path(r'^create-hsn-code/$', views.vendor_create_hsn_code, name='vendor_create_hsn_code'),
    re_path(r'^view-hsn-code/$', views.vendor_view_hsn_code, name='vendor_view_hsn_code'),

    re_path(r'^received-orders/(?P<status>.*)/$', views.received_orders, name='received_orders'),
    re_path(r'^received-order/(?P<pk>.*)/$', views.received_order, name='received_order'),
    re_path(r'^update-status-(?P<status>.*)/(?P<pk>.*)/$', views.update_order_status, name='update_order_status'),
    
    re_path(r'^bookings/$', views.bookings, name='bookings'),
    re_path(r'^booking/(?P<pk>.*)/$', views.booking, name='booking'),
    re_path(r'^accept_booking/(?P<pk>.*)/(?P<address_pk>.*)/$', views.accept_booking, name='accept_booking'),
    re_path(r'^accepted-bookings/$', views.accepted_bookings, name='accepted_bookings'),
]
