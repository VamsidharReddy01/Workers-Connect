from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import signup, login

urlpatterns = [
    path('signup/', signup, name='signup'),
    path('login/', login, name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]