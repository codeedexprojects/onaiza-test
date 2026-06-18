from django.conf.urls import url, include
from django.urls import path
from rest_framework_simplejwt.views import (TokenRefreshView,)
from . import views


urlpatterns = [
    path('token/', views.UserTokenObtainPairView.as_view(),
         name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
