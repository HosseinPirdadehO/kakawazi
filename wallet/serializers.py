from users.models import User
from .models import WalletTransaction
from rest_framework import serializers


class WalletDashboardSerializer(serializers.Serializer):
    balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_rewards = serializers.DecimalField(max_digits=18, decimal_places=0)
    total_deposits = serializers.DecimalField(max_digits=18, decimal_places=0)
    total_withdrawals = serializers.DecimalField(
        max_digits=18, decimal_places=0)
    total_invites = serializers.IntegerField()
    transactions_count = serializers.IntegerField()
    updated_at = serializers.DateTimeField()


class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = [
            'id',
            'amount',
            'types',
            'status',
            'description',
            'created_at',
            'updated_at'
        ]


class InvitedUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    joined_at = serializers.DateTimeField(source='date_joined')

    class Meta:
        model = User
        fields = [
            'id',
            'phone_number',
            'first_name',
            'last_name',
            'full_name',
            'joined_at',
            'is_phone_verified',
            'status',
            'referral_code',
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()
