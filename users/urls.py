from django.urls import path
from .views import (
    SendOTPView,
    VerifyOTPView,
    SetPasswordView,
    CompleteProfileView,
    RequestPhoneChangeView,
    VerifyPhoneChangeView,
    UserReferralStatsView,
    ReferralTreeView,
)
app_name = 'users'
urlpatterns = [
    path("send-otp/", SendOTPView.as_view(), name="send-otp"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
    path("set-password/", SetPasswordView.as_view(), name="set-password"),

    path("profile/complete/", CompleteProfileView.as_view(),
         name="complete-profile"),

    path("profile/request-phone-change/",
         RequestPhoneChangeView.as_view(), name="request-phone-change"),
    path("profile/verify-phone-change/",
         VerifyPhoneChangeView.as_view(), name="verify-phone-change"),

    path("referrals/stats/", UserReferralStatsView.as_view(), name="referral-stats"),
    path("referrals/tree/", ReferralTreeView.as_view(), name="referral-tree"),
]
