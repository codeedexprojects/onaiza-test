from django.urls import path, re_path
from users import views

app_name = "users"


urlpatterns = [
    path('login/', views.login_enter, name='login'),
    path('register/', views.registration, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('verify-success/', views.verify_success, name='verify_success'),
    # re_path(r'^verify/(?P<pk>.*)/$', views.verify, name='verify'),

    re_path(r'^change-password/(?P<pk>.*)/$', views.change_password, name='change_password'),
    re_path(r'^notifications/$', views.notifications, name='notifications'),
    re_path(r'^notification-mark-and-go/(?P<pk>.*)/$', views.notification_redirect_view, name='notification_redirect_view'),
    re_path(r'^read-selected-notification/$', views.read_selected_notification, name='read_selected_notification'),
    re_path(r'^read-notification/(?P<pk>.*)/$', views.read_notification, name='read_notification'),

]
