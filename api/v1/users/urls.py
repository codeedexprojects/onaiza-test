from django.conf.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^send-otp/$', views.send_otp, name='send_otp'),
    re_path(r'^verify-otp/$', views.verify_otp, name='verify_otp'),
    re_path(r'^create-customer/$', views.create_customer, name='create_customer'),

    re_path(r'^add-or-remove-from-wishlist/(?P<pk>.*)/$', views.add_or_remove_from_wishlist,name='add_or_remove_from_wishlist'),
    re_path(r'^view-wishlist/$', views.view_wishlist, name='view_wishlist'),

    re_path(r'^add-address/$', views.add_address, name='add_address'),
    re_path(r'^view-address/$', views.view_address, name='view_address'),
    re_path(r'^set-default-address/(?P<pk>.*)/$', views.set_default_address, name='set_default_address'),
    re_path(r'^get-default-address/$', views.get_default_address, name='get_default_address'),
    re_path(r'^(?P<view_type>.*)-address/(?P<pk>.*)/$', views.update_address, name='update_address'),

    re_path(r'^cart/$', views.cart, name='cart'),
    re_path(r'^add-to-cart/$', views.add_to_cart, name='add_to_cart'),
    re_path(r'^cart-increment/(?P<pk>.*)/$', views.cart_increment, name='cart_increment'),
    re_path(r'^cart-decrement/(?P<pk>.*)/$', views.cart_decrement, name='cart_decrement'),
    re_path(r'^cart-remove/(?P<pk>.*)/$', views.cart_remove, name='cart_remove'),
    re_path(r'^cart-remove-all/$', views.cart_remove_all, name='cart_remove_all'),

    re_path(r'^apply-coupon/(?P<pk>.*)/$', views.apply_coupon, name='apply_coupon'),
    re_path(r'^apply-wallet-amount/$', views.apply_wallet_amount, name='apply_wallet_amount'),

    re_path(r'^checkout/$', views.checkout, name='checkout'),
    re_path(r'^payment/$', views.payment, name='payment'),

    re_path(r'^orders/$', views.orders, name='orders'),
    re_path(r'^order-cancel/(?P<pk>.*)/$', views.order_cancel, name='order_cancel'),

    re_path(r'^book-now/(?P<pk>.*)/$', views.book_now, name='book_now'),
    re_path(r'^bookings/$', views.bookings, name='bookings'),

    # ticketes
    re_path(r'^new-issue/$', views.new_issue, name='new_issue'),
    re_path(r'^active-issue/$', views.active_issue, name='active_issue'),
    re_path(r'^resolved-issue/$', views.resolved_issue, name='resolved_issue'),

    re_path(r'^ratings/$', views.ratings, name='ratings'),
    re_path(r'^post-ratings/$', views.post_ratings, name='post_ratings'),

    re_path(r'^view-profile/$', views.view_profile, name='view_profile'),
    re_path(r'^update-profile/$', views.update_profile, name='update_profile'),

    re_path(r'^get-time-slots/$', views.get_time_slots, name='get_time_slots'),

    re_path(r'^product-return/$', views.product_return, name='product_return'),
]
