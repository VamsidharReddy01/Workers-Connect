from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    ChangePasswordView,
    LoginView,
    LogoutView,
    SendSignupOtpView,
    SignupView,
    SupportTicketListCreateView,
    UserProfileView,
)

urlpatterns = [
    path('signup/send-otp/', SendSignupOtpView.as_view(), name='send_signup_otp'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('support/tickets/', SupportTicketListCreateView.as_view(), name='support_tickets'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
