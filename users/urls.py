from django.urls import path
from .views import (
    SendOTPView,
    VerifyOTPView,
    CompleteProfileView,
    RequestPhoneChangeView,
    VerifyPhoneChangeView,
    UserReferralStatsView,
)
from rest_framework_simplejwt.views import TokenRefreshView

app_name = 'users'  

urlpatterns = [
    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('complete-profile/', CompleteProfileView.as_view(), name='complete-profile'),
    path('request-phone-change/', RequestPhoneChangeView.as_view(), name='request-phone-change'),
    path('verify-phone-change/', VerifyPhoneChangeView.as_view(), name='verify-phone-change'),
    path('referrals/', UserReferralStatsView.as_view(), name='user-referrals'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  
]