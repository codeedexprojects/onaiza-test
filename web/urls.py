from django.urls import re_path,path
from . import views
from web.views import PincodeAutoComplete


app_name = 'web'


urlpatterns = [
    re_path('pincode-autocomplete/', PincodeAutoComplete.as_view(),name='pincode_autocomplete'),

    re_path(r'^$', views.index, name='index'),
    re_path(r'^signup/$', views.signup, name='signup'),
    re_path(r'^login/$', views.userlogin, name='userlogin'),
    re_path(r'^verify-otp/$', views.verify_otp, name='verify_otp'),

    re_path(r'^add-to-wishlish/$', views.add_to_wishlist, name='add_to_wishlist'),
    re_path(r'^view-wishlish/$', views.view_wishlist, name='view_wishlist'),

    re_path(r'^product/(?P<pk>.*)/$', views.product, name='product'),
    re_path(r'^category/(?P<pk>.*)/$', views.product_by_category, name='category'),
    re_path(r'^sub-category/(?P<pk>.*)/$', views.product_by_subcategory, name='subcategory'),
    re_path(r'^product-variant-switch/$', views.product_variant_switch, name='product_variant_switch'),

    re_path(r'^search/$', views.search, name='search'),

    # re_path(r'^cart/$', views.cart, name='cart'),
    re_path(r'^add-to-cart/$', views.add_to_cart, name='add_to_cart'),
    re_path(r'^increment-cart/$', views.increment_cart, name='increment_cart'),
    re_path(r'^decrement-cart/$', views.decrement_cart, name='decrement_cart'),
    re_path(r'^remove-cart/$', views.remove_cart, name='remove_cart'),

    re_path(r'^apply-coupon/$', views.apply_coupon, name='apply_coupon'),
    re_path(r'^apply-wallet-amount/$', views.apply_wallet_amount, name='apply_wallet_amount'),

    re_path(r'^place-order/$', views.place_order, name='place_order'),
    re_path(r'^order-confirmed/$', views.order_confirmed, name='order_confirmed'),
    re_path(r'^view-orders/$', views.view_orders, name='view_orders'),
    re_path(r'^order-cancel/$', views.order_cancel, name='order_cancel'),

    re_path(r'^profile/$', views.view_profile, name='view_profile'),

    re_path(r'^delete-address/(?P<pk>.*)/$', views.delete_address, name='delete_address'),
    re_path(r'^edit-address/(?P<pk>.*)/$', views.edit_address, name='edit_address'),
    re_path(r'^get-address-form/(?P<pk>.*)/$', views.get_address_edit_form, name='get_address_edit_form'),
    re_path(r'^set-default-address/$', views.set_default_address, name='set_default_address'),

    re_path(r'^shops/$', views.shops, name='shops'),
    re_path(r'^shop/(?P<pk>.*)/$', views.shop, name='shop'),

    re_path(r'^payment/$', views.payment, name='payment'),
    re_path(r'^proceed-to-payment/$', views.proceed_to_payment, name='proceed_to_payment'),

    re_path(r'^book-product/$', views.book_product, name='book_product'),
    re_path(r'^view-booked-product/$', views.view_booked_product, name='view_booked_product'),

    re_path(r'^new-issue/$', views.new_issue, name='new_issue'),

    re_path(r'^get-pincode-by-name/$',views.get_pincode_by_name, name='get_pincode_by_name'),
    re_path(r'^get-time-slots/$', views.get_time_slots, name='get_time_slots'),

    re_path(r'^post-rating/$', views.post_rating, name='post_rating'),
    re_path(r'^set-pincode/$', views.set_pincode, name='set_pincode'),

    re_path(r'^clear-sessions/$', views.clear_sessions, name='clear_sessions'),
    re_path(r'^logout-customer/$', views.logout_customer, name='logout_customer'),

    re_path(r'^get-product-details-from-order-item/$', views.get_product_details_from_order_item, name='get_product_details_from_order_item'),

    re_path(r'^product-return/$', views.product_return, name='product_return'),
    re_path(r'^cancel-order/$', views.cancel_order, name='cancel_order'),

    re_path(r'^about-us/', views.about_us, name='about_us'),
    re_path(r'^delivery-information/', views.delivery_info, name='delivery_info'),
    re_path(r'^privacy-policy/', views.privacy_policy, name='privacy_policy'),
    re_path(r'^tac/', views.terms_and_contition, name='terms_and_contition'),

    # SpotlightBanner
    path('create-spotlight-banner/', views.create_spotlight_banner, name='create_spotlight_banner'),
    path('spotlight-banners/', views.spotlight_banners, name='spotlight_banners'),
    re_path(r'^edit-spotlight-banner/(?P<pk>.*)/$',views.edit_spotlight_banner, name='edit_spotlight_banner'),
    re_path(r'^view-spotlight-banner/(?P<pk>.*)/$', views.spotlight_banner, name='spotlight_banner'),
    re_path(r'^delete-spotlight-banner/(?P<pk>.*)/$',views.delete_spotlight_banner, name='delete_spotlight_banner'),

]