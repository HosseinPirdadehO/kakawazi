from django.urls import path
from .views import WalletDashboardView, WalletTransactionListView,  CombinedInviteListAndSummaryView

urlpatterns = [
    path('wallet-dashboard/', WalletDashboardView.as_view(),
         name='wallet-dashboard'),
    path('wallet-transactions/', WalletTransactionListView.as_view(),
         name='wallet-transactions'),
    path('invites/', CombinedInviteListAndSummaryView.as_view(),
         name='combined-invites'),
]
