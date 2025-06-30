from django.contrib import admin
from django.db.models import Sum, Count
from .models import Wallet, WalletTransaction


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'updated_at', 'created_at')
    search_fields = ('user__phone_number',
                     'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at', 'balance', 'user')
    ordering = ('-updated_at',)

    def changelist_view(self, request, extra_context=None):
        total_balance = Wallet.objects.aggregate(
            total=Sum('balance'))['total'] or 0
        total_transactions = WalletTransaction.objects.aggregate(count=Count('id'))[
            'count'] or 0

        extra_context = extra_context or {}
        extra_context['total_balance'] = total_balance
        extra_context['total_transactions'] = total_transactions

        return super().changelist_view(request, extra_context=extra_context)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'types', 'status', 'created_at')
    list_filter = ('types', 'status', 'created_at')
    search_fields = ('user__phone_number',
                     'user__first_name', 'user__last_name')
    readonly_fields = ('user', 'amount', 'types', 'status',
                       'description', 'created_at', 'updated_at')
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False
