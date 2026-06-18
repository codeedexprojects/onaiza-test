from django.urls import path, re_path
from suppliers.views import SupplierAutocomplete
from suppliers import views

app_name = "suppliers"


urlpatterns = [

    path('supplier-autocomplete/', SupplierAutocomplete.as_view(),
         name='supplier_autocomplete'),
    path('get-suppliers/', views.get_suppliers, name='get_suppliers'),
    path('get-supplier-data/', views.get_supplier_data, name='get_supplier_data'),
    path('get-balance/',views.get_balance, name='get_balance'),

    path('supplier/create/', views.create_supplier, name='create_supplier'),
    path('supplier/from-create/', views.supplier_from_create,
         name='supplier_from_create'),

    path('suppliers/', views.suppliers, name='suppliers'),
    re_path(r'^supplier/edit/(?P<pk>.*)/$',
            views.edit_supplier, name='edit_supplier'),
    re_path(r'^supplier/view/(?P<pk>.*)/$', views.supplier, name='supplier'),
    re_path(r'^supplier/delete/(?P<pk>.*)/$',
            views.delete_supplier, name='delete_supplier'),
    path('supplier/delete-selected/', views.delete_selected_suppliers,
         name='delete_selected_suppliers'),
]
