from django.conf.urls import url, re_path

from . import views

urlpatterns = [

    # home screen urls
    url(r'^offer-sliders/$', views.offer_sliders, name='offer_sliders'),
    url(r'^get-latest-category-offer/$', views.get_latest_category_offer, name='get_latest_category_offer'),
    url(r'^categories/$', views.categories, name='categories'),
    url(r'^best-sellers/$', views.best_sellers, name='best_sellers'),
    url(r'^nearest-shops/$', views.nearest_shops, name='nearest_shops'),
    url(r'^best-offers/$', views.best_offers, name='best_offers'),

    url(r'^search/$', views.search, name='search'),

    url(r'^shops/$', views.shops, name='shops'),
    url(r'^shop/(?P<pk>.*)/$', views.shop, name='shop'),

    url(r'^product/(?P<pk>.*)/$', views.product, name='product'),
    url(r'^product-reviews/(?P<pk>.*)/$', views.product_reviews, name='product_reviews'),

    re_path(r'^app-update/$', views.app_update, name='app_update'),

    url(r'banners/$', views.banners, name='banners'),

]