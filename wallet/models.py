from django.db import models, transaction
from django.conf import settings


class Wallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet',
        verbose_name='کاربر'
    )
    balance = models.DecimalField(
        max_digits=12, decimal_places=0, default=0, verbose_name='موجودی (ریال)')
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name='تاریخ بروزرسانی')
    created_at = models.DateTimeField(
        auto_now_add=True, null=True, verbose_name='تاریخ ایجاد')

    def deposit(self, amount, description=None, transaction_type='deposit'):
        with transaction.atomic():
            self.balance += amount
            self.save()
            WalletTransaction.objects.create(
                user=self.user,
                types=transaction_type,
                amount=amount,
                status='success',
                description=description
            )

    def withdraw(self, amount, description=None):
        if amount > self.balance:
            raise ValueError("موجودی کافی نیست")
        with transaction.atomic():
            self.balance -= amount
            self.save()
            WalletTransaction.objects.create(
                user=self.user,
                types='withdrawal',
                amount=amount,
                status='success',
                description=description
            )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'کیف پول'
        verbose_name_plural = 'کیف پول‌ها'

    def __str__(self):
        return f"کیف پول {self.user} - موجودی: {self.balance} ریال"


class WalletTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('deposit', 'واریز'),
        ('withdrawal', 'برداشت'),
        ('refund', 'بازگشت وجه'),
        ('reward', 'پاداش'),
        ('manual', 'تراکنش دستی'),
    )

    STATUS_CHOICES = (
        ('pending', 'در انتظار'),
        ('success', 'موفق'),
        ('failed', 'ناموفق'),
        ('canceled', 'لغو شده'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet_transactions',
        verbose_name='کاربر'
    )
    amount = models.DecimalField(
        max_digits=18, decimal_places=0, verbose_name='مبلغ')
    types = models.CharField(
        max_length=20, choices=TRANSACTION_TYPES, verbose_name='نوع تراکنش')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='وضعیت')
    description = models.TextField(
        blank=True, null=True, verbose_name='توضیحات')
    created_at = models.DateTimeField(
        auto_now_add=True, null=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'تراکنش کیف پول'
        verbose_name_plural = 'تراکنش‌های کیف پول'

    def __str__(self):
        return f"{self.user} - {self.get_types_display()} - {self.amount} ریال"
