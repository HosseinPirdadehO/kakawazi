from rest_framework import generics, permissions
from django.db.models import Sum
from rest_framework.pagination import PageNumberPagination

from .models import Wallet, WalletTransaction
from users.models import User
from .serializers import WalletTransactionSerializer
from users.serializers import InvitedUserSerializer

from .mixins import StandardResponseMixin


class WalletDashboardView(StandardResponseMixin, generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        transactions = WalletTransaction.objects.filter(user=request.user)

        total_rewards = transactions.filter(
            types='reward', status='success'
        ).aggregate(total=Sum('amount'))['total'] or 0

        total_withdrawals = transactions.filter(
            types='withdrawal', status='success'
        ).aggregate(total=Sum('amount'))['total'] or 0

        total_deposits = transactions.filter(
            types='deposit', status='success'
        ).aggregate(total=Sum('amount'))['total'] or 0

        total_invites = request.user.sent_referrals.count()

        data = {
            "balance": wallet.balance,
            "total_rewards": total_rewards,
            "total_deposits": total_deposits,
            "total_withdrawals": total_withdrawals,
            "total_invites": total_invites,
            "transactions_count": transactions.count(),
            "updated_at": wallet.updated_at,

            "labels": {
                "balance": "موجودی کیف پول",
                "total_rewards": "مجموع پاداش‌ها",
                "total_deposits": "مجموع واریزها",
                "total_withdrawals": "مجموع برداشت‌ها",
                "total_invites": "تعداد دعوت‌شده‌ها",
                "transactions_count": "تعداد تراکنش‌ها",
                "updated_at": "آخرین بروزرسانی"
            }
        }

        return self.success_response(data, message="داشبورد کیف پول")


class WalletTransactionListView(StandardResponseMixin, generics.ListAPIView):
    serializer_class = WalletTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WalletTransaction.objects.filter(user=self.request.user).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        serializer = self.get_serializer(
            page, many=True) if page else self.get_serializer(queryset, many=True)
        data = serializer.data

        if page is not None:
            return self.get_paginated_response({
                "transactions": data
            })

        return self.success_response({"transactions": data}, message="لیست تراکنش‌ها")


class CombinedInviteListAndSummaryView(StandardResponseMixin, generics.ListAPIView):
    serializer_class = InvitedUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.sent_referrals.all()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        total_invites = queryset.count()

        total_reward = WalletTransaction.objects.filter(
            user=request.user,
            types='reward',
            status='success'
        ).aggregate(total=Sum('amount'))['total'] or 0

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(
            page, many=True) if page else self.get_serializer(queryset, many=True)

        result = {
            "total_invites": total_invites,
            "total_reward": total_reward,
            "invites": serializer.data
        }

        if page is not None:
            return self.get_paginated_response(result)

        return self.success_response(result, message="لیست دعوت‌شدگان و خلاصه جوایز")
