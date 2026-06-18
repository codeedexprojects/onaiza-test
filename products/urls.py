from django.urls import path, re_path
from django.conf.urls import url, include
from django.contrib import admin
from django.urls import reverse
from products import views
from products.views import CategoryAutocomplete, SubcategoryAutocomplete, UnitMeasurementAutocomplete, ProductVariantAutocomplete, BrandAutocomplete, ProductAutocomplete, UnitAutocomplete, HSNcodeAutocomplete

app_name = "products"


urlpatterns = [
    re_path(r'^product-autocomplete/$', ProductAutocomplete.as_view(),name='product_autocomplete'),
    re_path(r'^product-variant-autocomplete/$', ProductVariantAutocomplete.as_view(),name='product_variant_autocomplete'),
    re_path(r'^subcategory-autocomplete/$', SubcategoryAutocomplete.as_view(create_field='name'), name='subcategory_autocomplete'),
    re_path(r'^category-autocomplete/$', CategoryAutocomplete.as_view(create_field='name'),name='category_autocomplete'),
    re_path(r'^unit-measurement-autocomplete/$', UnitMeasurementAutocomplete.as_view(),name='unit_measurement_autocomplete'),
    re_path(r'^unit-autocomplete/$', UnitAutocomplete.as_view(),name='unit_autocomplete'),
    re_path(r'^brand-autocomplete/$', BrandAutocomplete.as_view(create_field='name'),name='brand_autocomplete'),
    re_path(r'^hsn-code-autocomplete/$', HSNcodeAutocomplete.as_view(),name='hsn_code_autocomplete'),

    re_path(r'^create/$', views.create, name='create'),
    re_path(r'^all/$', views.products, name='products'),
    re_path(r'^product/(?P<pk>.*)/$', views.product, name='product'),
    re_path(r'^edit/(?P<pk>.*)/$', views.edit, name='edit'),
    re_path(r'^delete/(?P<pk>.*)/$', views.delete, name='delete'),
    re_path(r'^delete-selected-products/$', views.delete_selected_products,name='delete_selected_products'),

    re_path(r'^create-variant/(?P<pk>.*)/$', views.create_variant, name='create_variant'),
    re_path(r'^view-variant/(?P<pk>.*)/$', views.view_variant, name='view_variant'),
    re_path(r'^edit-variant/(?P<pk>.*)/$', views.edit_variant, name='edit_variant'),
    re_path(r'^delete-variant/(?P<pk>.*)/$', views.delete_variant, name='delete_variant'),

    re_path(r'^barcode/create/$', views.create_barcode, name='create_barcode'),
    re_path(r'^barcodes/print/$', views.print_barcodes, name='print_barcodes'),

    re_path(r'^get-product-details/$', views.get_category_details,name='get_category_details'),
    re_path(r'^get-product-hsn-detailes/$', views.get_product_hsn_detailes,name='get_product_hsn_detailes'),

    re_path(r'^create-category/$', views.create_category, name='create_category'),
    re_path(r'^categories/$', views.categories, name='categories'),
    re_path(r'^edit-category/(?P<pk>.*)/$',views.edit_category, name='edit_category'),
    re_path(r'^view-category/(?P<pk>.*)/$', views.category, name='category'),
    re_path(r'^delete-category/(?P<pk>.*)/$',views.delete_category, name='delete_category'),
    re_path(r'^delete-selected-categories/$', views.delete_selected_categories,name='delete_selected_categories'),

    re_path(r'^create-subcategory/$', views.create_subcategory,name='create_subcategory'),
    re_path(r'^get-subcategory/$', views.get_subcategory, name='get_subcategory'),
    re_path(r'^subcategories/$', views.subcategories, name='subcategories'),
    re_path(r'^edit-subcategory/(?P<pk>.*)/$',views.edit_subcategory, name='edit_subcategory'),
    re_path(r'^subcategory/(?P<pk>.*)/$',views.subcategory, name='subcategory'),
    re_path(r'^delete-sub-category/(?P<pk>.*)/$',views.delete_sub_category, name='delete_sub_category'),
    re_path(r'^delete-selected-subcategories/$', views.delete_selected_subcategories,name='delete_selected_subcategories'),

    re_path(r'^create-brand/$', views.create_brand, name='create_brand'),
    re_path(r'^brands/$', views.brands, name='brands'),
    re_path(r'^edit-brand/(?P<pk>.*)/$', views.edit_brand, name='edit_brand'),
    re_path(r'^view-brand/(?P<pk>.*)/$', views.brand, name='brand'),
    re_path(r'^delete-brand/(?P<pk>.*)/$',views.delete_brand, name='delete_brand'),
    re_path(r'^delete-selected-brands/$', views.delete_selected_brands,name='delete_selected_brands'),

    re_path(r'^create-unit-measurement/$', views.create_unit_measurement,name='create_unit_measurement'),
    re_path(r'^unit-measurements/$', views.unit_measurements, name='unit_measurements'),
    re_path(r'^edit-unit-measurement/(?P<pk>.*)/$',views.edit_unit_measurement, name='edit_unit_measurement'),
    re_path(r'^view-unit-measurement/(?P<pk>.*)/$',views.unit_measurement, name='unit_measurement'),
    re_path(r'^delete-unit-measurement/(?P<pk>.*)/$',views.delete_unit_measurement, name='delete_unit_measurement'),
    re_path(r'^delete-unit-measurement/$', views.delete_selected_unit_measurement,name='delete_selected_unit_measurement'),

    re_path(r'^create-unit/$', views.create_unit,name='create_unit'),
    re_path(r'^units/$', views.units, name='units'),
    re_path(r'^edit-unit/(?P<pk>.*)/$',views.edit_unit, name='edit_unit'),
    re_path(r'^view-unit/(?P<pk>.*)/$',views.unit, name='unit'),
    re_path(r'^delete-unit/(?P<pk>.*)/$',views.delete_unit, name='delete_unit'),
    re_path(r'^delete-unit/$', views.delete_selected_unit,name='delete_selected_unit_measurement'),

    re_path(r'^create-hsn-code/$', views.hsn_codes_create, name='create_hsn_codes'),
    re_path(r'^hsn-codes/$', views.hsn_codes, name='hsn_codes_all'),
    re_path(r'^edit-hsn-code/(?P<pk>.*)/$',views.edit_hsn_code, name='edit_hsn_code'),
    re_path(r'^view-hsn-code/(?P<pk>.*)/$', views.hsn_code, name='hsn_code'),
    re_path(r'^delete-hsn-code/(?P<pk>.*)/$',views.delete_hsn_code, name='delete_hsn_code'),
    re_path(r'^delete-selected-hsn-codes/$', views.delete_selected_hsn_codes,name='delete_selected_hsn_codes'),

    re_path(r'^export-products/$', views.export_products, name='export_products'),
    re_path(r'^export-filtered-products/$', views.export_filtered_products,name='export_filtered_products'),
    re_path(r'^export-variant/(?P<pk>.*)/$', views.export_variants, name='export_variants'),
    re_path(r'^export-variant-to-pdf/(?P<pk>.*)/$', views.export_variants_to_pdf, name='export_variants_to_pdf'),

    re_path(r'^update-varying-product-price/$', views.update_varying_product_price, name='update_varying_product_price'),
    re_path(r'^enable-or-disable-product/(?P<pk>.*)/$', views.enable_or_disable_product, name='enable_or_disable_product'),

    re_path(r'^update-variant-stock/(?P<pk>.*)/$', views.update_variant_stock, name='update_variant_stock'),
]
