from django.conf.urls import url, re_path

from . import views

urlpatterns = [
    url(r'^get-pincodes/$', views.get_pincodes, name='get_pincodes'),
    url(r'^set-location/$', views.set_location, name='set_location'),
]