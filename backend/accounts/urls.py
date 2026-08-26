from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    ChangePasswordView,
    CustomerSignupView,
    GeocodeLookupView,
    LoginView,
    LogoutView,
    SendSignupOtpView,
    SignupView,
    SupportTicketListCreateView,
    UpdateLocationView,
    UserProfileView,
    WorkerSignupView,
)

urlpatterns = [
    path('signup/send-otp/', SendSignupOtpView.as_view(), name='send_signup_otp'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('signup/worker/', WorkerSignupView.as_view(), name='worker_signup_nested'),
    path('signup/customer/', CustomerSignupView.as_view(), name='customer_signup_nested'),
    path('worker-signup/', WorkerSignupView.as_view(), name='worker_signup'),
    path('customer-signup/', CustomerSignupView.as_view(), name='customer_signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('location/', UpdateLocationView.as_view(), name='update_location'),
    path('geocode/', GeocodeLookupView.as_view(), name='geocode_lookup'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('support/tickets/', SupportTicketListCreateView.as_view(), name='support_tickets'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
