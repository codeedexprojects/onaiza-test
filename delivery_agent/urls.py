from django.contrib import admin
from django.urls import path, re_path, include
from .import views
from delivery_agent.views import DeliveryAgentAutocomplete
app_name = 'delivery_agent'

urlpatterns = [
    path('delivery-agent-autocomplete/', DeliveryAgentAutocomplete.as_view(),
         name='delivery_agent_autocomplete'),
    re_path(r'^create-delivery-agent/$',views.create_delivery_agent, name='create_delivery_agent'),
    re_path(r'^delivery-agent/(?P<pk>.*)/$', views.delivery_agent, name='delivery_agent'),
    re_path(r'^delivery-agents/$', views.delivery_agents, name='delivery_agents'),
    re_path(r'^delete-delivery-agent/(?P<pk>.*)/$', views.delete_delivery_agent, name='delete_delivery_agent'),
    re_path(r'^edit-delivery-agent/(?P<pk>.*)/$', views.edit_delivery_agent, name='edit_delivery_agent'),

    re_path(r'^get-delivery-agents/$', views.get_delivery_agents, name='get_delivery_agents'),
    re_path(r'^delivery-agent-export/$', views.delivery_agent_export, name='delivery_agent_export'),

    re_path(r'^view-detailed-report/(?P<pk>.*)/$', views.view_detail_report, name='view_detail_report'),
    re_path(r'^view-hand-over-details/$', views.hand_over_details, name='hand_over_details'),

    re_path(r'^approve-hand-over/(?P<pk>.*)$', views.approve_hand_over, name='approve_hand_over'),
    re_path(r'^decline-hand-over/(?P<pk>.*)$', views.decline_hand_over, name='decline_hand_over'),

]