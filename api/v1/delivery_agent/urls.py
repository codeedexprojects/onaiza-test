from django.conf.urls import url, re_path

from . import views

urlpatterns = [
    url(r'^login-agent/$', views.login_agent, name='login_agent'),
    url(r'^get-orders/$', views.get_orders, name='get_orders'),
    url(r'^accept-or-reject-order/(?P<pk>.*)/$', views.accept_or_reject_order, name='accept_or_reject_order'),
    url(r'^payment-collection/$', views.payment_collection, name='payment_collection'),
    url(r'^collected-payments/$', views.collected_payments, name='collected_payments'),
    url(r'^payment-transfer/$', views.payment_transfer, name='payment_transfer'),

    url(r'^save_location/$', views.save_location, name='save_location'),
    url(r'^get_location/$', views.get_location, name='get_location'),

    url(r'^get-returns/$', views.get_returns,),
    url(r'^accept-return-by-agent/(?P<pk>.*)/$', views.accept_return_by_agent),

    url(r'^order/(?P<pk>.*)/$', views.order, name='order'),

    url(r'^update-duty-status/$', views.update_duty_status, name='update_duty_status'),
    url(r'^get-duty-status/$', views.get_duty_status, name='get_duty_status'),

    url(r'^update-pickup-status/(?P<pk>.*)/$', views.update_pickup_status, name='update_pickup_status'),
    url(r'^update-delivery-status/(?P<pk>.*)/$', views.update_delivery_status, name='update_delivery_status'),

    url(r'^dashboard/$', views.dashboard, name='dashboard'),
    url(r'^notifications/$', views.notifications, name='notifications'),
    url(r'^mark-as-read/(?P<pk>.*)/$', views.mark_as_read, name='mark_as_read'),
    url(r'^view-profile/$', views.view_profile, name='view_profile'),
    url(r'^update-profile/$', views.update_profile, name='update_profile'),


]