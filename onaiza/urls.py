from django.contrib import admin
from django.urls import path, re_path, include
from django.views.static import serve
from django.conf import settings
from main import views as general_views
from django.conf import settings
from django.conf.urls import url
from django.conf.urls.i18n import i18n_patterns


admin.autodiscover()
admin.site.enable_nav_sidebar = False

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    re_path(r'^switch-language/$', general_views.switch_language, name='switch_language'),

    re_path('api/v1/auth/',include(('api.v1.authentication.urls', 'authentication'), namespace='api_v1_authentication')),
    re_path('api/v1/users/',include(('api.v1.users.urls', 'users'), namespace='api_v1_users')),
    re_path('api/v1/location/',include(('api.v1.location.urls', 'location'), namespace='api_v1_location')),
    re_path('api/v1/general/',include(('api.v1.general.urls', 'general'), namespace='api_v1_general')),
    re_path('api/v1/delivery/',include(('api.v1.delivery_agent.urls', 'delivery_agent'), namespace='api_v1_delivery_agent')),
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),

    path('', include('web.urls')),
    path('pwa', include('pwa.urls')),

    path('app/', general_views.app, name='app'),
    path('app/dashboard/', general_views.dashboard, name='dashboard'),
    path('app/accounts/', include('registration.backends.default.urls')),
    path('app/products/', include('products.urls')),
    path('app/general/', include('general.urls')),
    path('app/suppliers/', include('suppliers.urls')),
    path('app/vendors/', include('vendors.urls')),
    path('app/customers/', include(('customers.urls','customers'), namespace='customers')),
    path('app/staffs/', include(('staffs.urls','staffs'), namespace='staffs')),

    path('app/warehouses/', include(('warehouses.urls','warehouses'), namespace='warehouses')),

    path('app/finance/', include('finance.urls')),
    path('app/purchases/', include('purchases.urls')),
    path('app/sales/', include('sales.urls')),
    path('app/offers/', include('offers.urls')),
    path('app/orders/', include('orders.urls')),
    path('app/delivery/', include('delivery_agent.urls')),
    path('app/reports/', include('reports.urls')),

    path('app/main/', include('main.urls')),
    path('app/users/', include('users.urls', namespace="users")),

    url(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),
    url(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_FILE_ROOT}),
)
