from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)
from django.urls import path
from .views import (
    SendOTPView,
    VerifyOTPView,
    LoginWithPasswordView,
    CompleteProfileView,
    SetPasswordView,
    LogoutView, TestTokenView, ReferralListView, UserProfileView
)

urlpatterns = [
    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('login-password/', LoginWithPasswordView.as_view(), name='login-password'),
    path('complete-profile/', CompleteProfileView.as_view(),
         name='complete-profile'),
    path('set-password/', SetPasswordView.as_view(), name='set-password'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('referrals/', ReferralListView.as_view(), name='referral-list'),
    path('test-token/', TestTokenView.as_view(), name='test-token'),

    path('profile/', UserProfileView.as_view(), name='user-profile'),


    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/blacklist/', TokenBlacklistView.as_view(),
         name='token_blacklist'),
]
#
# git add .
# git commit -m 'june4'
# git branch -M main
# git push -u origin main
