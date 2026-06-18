from django.conf.urls import  url,include
from main import views

app_name = "main"

urlpatterns = [
    url(r'^$', views.dashboard, name='dashboard'),
    url(r'^switch-language/$', views.switch_language, name='switch_language'),
    url(r'^check-password-policy/$', views.check_password_policy, name='check_password_policy'),
]