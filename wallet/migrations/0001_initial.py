# Generated by Django 4.2.9 on 2025-06-30 13:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='WalletTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=0, max_digits=18, verbose_name='مبلغ')),
                ('types', models.CharField(choices=[('deposit', 'واریز'), ('withdrawal', 'برداشت'), ('refund', 'بازگشت وجه'), ('reward', 'پاداش'), ('manual', 'تراکنش دستی')], max_length=20, verbose_name='نوع تراکنش')),
                ('status', models.CharField(choices=[('pending', 'در انتظار'), ('success', 'موفق'), ('failed', 'ناموفق'), ('canceled', 'لغو شده')], default='pending', max_length=20, verbose_name='وضعیت')),
                ('description', models.TextField(blank=True, null=True, verbose_name='توضیحات')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wallet_transactions', to=settings.AUTH_USER_MODEL, verbose_name='کاربر')),
            ],
            options={
                'verbose_name': 'تراکنش کیف پول',
                'verbose_name_plural': 'تراکنش\u200cهای کیف پول',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Wallet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('balance', models.DecimalField(decimal_places=0, default=0, max_digits=12, verbose_name='موجودی (ریال)')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='تاریخ ایجاد')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='wallet', to=settings.AUTH_USER_MODEL, verbose_name='کاربر')),
            ],
            options={
                'verbose_name': 'کیف پول',
                'verbose_name_plural': 'کیف پول\u200cها',
                'ordering': ['-created_at'],
            },
        ),
    ]
