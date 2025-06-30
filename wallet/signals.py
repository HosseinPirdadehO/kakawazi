from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Wallet, WalletTransaction

from users.models import User


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_wallet(sender, instance, created, **kwargs):
    if created:
        wallet, was_created = Wallet.objects.get_or_create(user=instance)
        if was_created:
            print(f" کیف پول جدید برای {instance} ساخته شد.")
        else:
            print(f" {instance} از قبل کیف پول داشت.")


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def reward_inviter_on_signup(sender, instance, created, **kwargs):
    if not created:
        return

    inviter = instance.referral
    if inviter:
        try:
            inviter_wallet, _ = Wallet.objects.get_or_create(user=inviter)

            with transaction.atomic():
                inviter_wallet.deposit(
                    50000,
                    description=f"پاداش دعوت از {instance.phone_number}"
                )
        except Exception as e:
            print(f" خطا در پرداخت پاداش دعوت: {e}")
