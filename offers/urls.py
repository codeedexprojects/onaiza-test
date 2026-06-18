from django.urls import path, re_path
from django.conf.urls import url, include
from django.contrib import admin
from django.urls import reverse
from offers import views

app_name = "offers"

urlpatterns = [

    path('create-offer/', views.create_offer, name='create_offer'),
    path('offers/', views.offers, name='offers'),
    re_path(r'^edit-offer/(?P<pk>.*)/$', views.edit_offer, name='edit_offer'),
    re_path(r'^view-offer/(?P<pk>.*)/$', views.offer, name='offer'),
    re_path(r'^delete-offer/(?P<pk>.*)/$',
            views.delete_offer, name='delete_offer'),
    path('delete-selected-offers/', views.delete_selected_offers,
         name='delete_selected_offers'),

    path('create-dealofday/', views.create_dealofday, name='create_dealofday'),
    path('dealofdays/', views.dealofdays, name='dealofdays'),
    re_path(r'^edit-dealofday/(?P<pk>.*)/$',
            views.edit_dealofday, name='edit_dealofday'),
    re_path(r'^view-dealofday/(?P<pk>.*)/$',
            views.dealofday, name='dealofday'),
    re_path(r'^delete-dealofday/(?P<pk>.*)/$',
            views.delete_dealofday, name='delete_dealofday'),
    path('delete-selected-dealofdays/', views.delete_selected_dealofdays,
         name='delete_selected_dealofdays'),

    path('create-voucher/', views.create_voucher, name='create_voucher'),
    path('vouchers/', views.vouchers, name='vouchers'),
    re_path(r'^edit-voucher/(?P<pk>.*)/$', views.edit_voucher, name='edit_voucher'),
    re_path(r'^view-voucher/(?P<pk>.*)/$', views.voucher, name='voucher'),
    re_path(r'^delete-voucher/(?P<pk>.*)/$',
            views.delete_voucher, name='delete_voucher'),
]
