from django.urls import path, re_path
from warehouses import views
from warehouses.views import WarehouseAutocomplete, ToWarehouseAutocomplete, LocationAutocomplete, WarehouseLocationAutocomplete

app_name = "warehouses"


urlpatterns = [
    path('warehouse-autocomplete/', WarehouseAutocomplete.as_view(),name='warehouse_autocomplete'),
    path('towarehouse-autocomplete/', ToWarehouseAutocomplete.as_view(),name='towarehouse_autocomplete'),
    path('location-autocomplete/', LocationAutocomplete.as_view(),name='location_autocomplete'),
    path('warehouse-location-autocomplete/', WarehouseLocationAutocomplete.as_view(),name='warehouse_location_autocomplete'),

    path('create-warehouse/', views.create_warehouse,name='create_warehouse'),
    path('warehouses/', views.warehouses, name='warehouses'),
    re_path(r'^edit-warehouse/(?P<pk>.*)/$',views.edit_warehouse, name='edit_warehouse'),
    re_path(r'^view-warehouse/(?P<pk>.*)/$',views.warehouse, name='warehouse'),
    re_path(r'^delete-warehouse/(?P<pk>.*)/$',views.delete_warehouse, name='delete_warehouse'),
    path('delete-selected-warehouses/', views.delete_selected_warehouses,name='delete_selected-warehouses'),

    path('create-location/', views.create_location,name='create_location'),
    path('locations/', views.locations, name='locations'),
    re_path(r'^edit-location/(?P<pk>.*)/$',views.edit_location, name='edit_location'),
    re_path(r'^view-location/(?P<pk>.*)/$',views.location, name='location'),
    re_path(r'^delete-location/(?P<pk>.*)/$',views.delete_location, name='delete_location'),
    path('delete-selected-locations/', views.delete_selected_locations,name='delete_selected-locations'),

    path('get-warehouse-variant/', views.get_warehouse_variant,name='get_warehouse_variant'),
    re_path(r'^our-orders/$',views.our_orders, name='our_orders'),
]
