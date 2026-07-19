from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import SendSignupOtpView, SignupView, LoginView, UserProfileView, LogoutView

urlpatterns = [
    path('signup/send-otp/', SendSignupOtpView.as_view(), name='send_signup_otp'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
