from django.urls import path, re_path
from django.conf.urls import url, include
from orders import views


app_name = "orders"

urlpatterns = [
    re_path(r'^create-time-slot/$', views.create_time_slot, name='create_time_slot'),
    re_path(r'^time-slots/$', views.time_slots, name='time_slots'),
    re_path(r'^time-slot/(?P<pk>.*)/$', views.time_slot, name='time_slot'),
    re_path(r'^edit-time-slot/(?P<pk>.*)/$', views.edit_time_slot, name='edit_time_slot'),
    re_path(r'^delete-time-slot/(?P<pk>.*)/$', views.delete_time_slot, name='delete_time_slot'),

    re_path(r'^(?P<order_type>.*)-orders/$', views.orders, name='orders'),
    re_path(r'^order/(?P<pk>.*)/$', views.order, name='order'),
    re_path(r'^assign-agent/$', views.assign_agent, name='assign_agent'),

    re_path(r'^bookings/$', views.bookings, name='bookings'),
    re_path(r'^booking/(?P<pk>.*)/$', views.booking, name='booking'),
    re_path(r'^accept_booking/(?P<pk>.*)/(?P<address_pk>.*)/$', views.accept_booking, name='accept_booking'),
    re_path(r'^accepted-bookings/$', views.accepted_bookings, name='accepted_bookings'),

    re_path(r'^returns/$', views.returns, name='returns'),
    re_path(r'^product-return/(?P<pk>.*)/$', views.product_return, name='product_return'),
    re_path(r'^accept-or-reject-return/$', views.accept_or_reject_return, name='accept_or_reject_return'),
    re_path(r'^assign-agent-for-return/$', views.assign_agent_for_return, name='assign_agent_for_return'),
    re_path(r'^product-recieved/$', views.product_recieved, name='product_recieved'),
    re_path(r'^print-sale-order/(?P<pk>.*)/$', views.print_sale_order, name='print_sale_order'),
    re_path(r'^print-staff-view-order-(?P<view_type>.*)/(?P<pk>.*)/$', views.print_staff_view_order, name='print_staff_view_order'),
    re_path(r'^change-order-status/(?P<pk>.*)/$', views.change_order_status, name='change_order_status'),

    re_path(r'^print-sale-order-A4/(?P<pk>.*)/$', views.print_sale_order_a4, name='print_sale_order_a4'),


]
