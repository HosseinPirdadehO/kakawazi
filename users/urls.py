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
    LogoutView, TestTokenView, ReferralListView, UserListView, FullUserProfileView
)

urlpatterns = [
    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('login-password/', LoginWithPasswordView.as_view(), name='login-password'),
    path('Complete-profile/', CompleteProfileView.as_view(), name='user-profile'),
    path('set-password/', SetPasswordView.as_view(), name='set-password'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('referrals/', ReferralListView.as_view(), name='referral-list'),
    path('test-token/', TestTokenView.as_view(), name='test-token'),


    path('list-users/', UserListView.as_view(), name='user-list'),
    path('user/me/', FullUserProfileView.as_view(), name='user-profile'),

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


# 'june27q'
