# -*- coding: utf-8 -*-
import hashlib
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from .sms_service import send_sms
import random
import string
import uuid
from datetime import timedelta
import logging


class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("Phone number is required")
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    user_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                 editable=False, unique=True, verbose_name="شناسه کاربر")
    phone_number = models.CharField(max_length=15, unique=True)
    is_phone_verified = models.BooleanField(default=False)

    referral_code = models.CharField(
        max_length=10, unique=True, blank=True, null=True, verbose_name="کد دعوت")

    national_code = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name="کد ملی",
        validators=[
            RegexValidator(regex=r'^\d{10}$',
                           message="کد ملی باید ۱۰ رقم باشد.")
        ]
    )
    VEHICLE_TYPE_CHOICES = [
        ('van', 'ون'),
        ('car', 'سواری سب'),
        ('minibus', 'مینی بوس'),
    ]
    ROLE_CHOICES = [
        ('school_manager', 'مدیر مدرسه'),
        ('taxi_driver', 'راننده تاکسی'),
        ('student', 'دانش‌آموز'),
    ]

    first_name = models.CharField(
        max_length=30, blank=True, verbose_name="نام")
    last_name = models.CharField(
        max_length=30, blank=True, verbose_name="نام خانوادگی")
    email = models.EmailField(blank=True, verbose_name="ایمیل")
    birth_date = models.DateField(
        null=True, blank=True, verbose_name="تاریخ تولد")
    city = models.CharField(max_length=100, blank=True,
                            null=True, verbose_name="شهر")
    state = models.CharField(max_length=100, blank=True,
                             null=True, verbose_name="استان")
    image = models.URLField(null=True, blank=True, verbose_name="عکس پروفایل")

    # iranian_plate_validator = RegexValidator(
    #     regex=r'^\d{2}[الف-ی]\d{3}\s?\d{2}$',
    #     message='شماره پلاک باید به فرمت صحیح پلاک خودروهای ایران باشد، مثلا ۲۲۲ی۲۲ ۲۲'
    # )
    plate_number = models.CharField(
        max_length=11,
        unique=True,
        null=True,
        blank=True,
        # validators=[iranian_plate_validator],
        verbose_name='شماره پلاک'
    )
    type_of_car = models.CharField(
        max_length=10,
        choices=VEHICLE_TYPE_CHOICES,
        null=True,
        blank=True,
        verbose_name='نوع ماشین'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        verbose_name='نقش / شغل',
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    last_login = models.DateTimeField(null=True, blank=True)

    STATUS_CHOICES = [
        ('active', 'فعال'),
        ('inactive', 'غیرفعال'),
        ('deleted', 'حذف‌شده'),
        ('pending', 'در انتظار تایید'),
    ]
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='active')

    objects = UserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"
        ordering = ['birth_date']

    def __str__(self):
        return self.get_full_name() or self.phone_number

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def clean(self):
        if self.city and self.state and self.city == self.state:
            raise ValidationError("شهر و استان نباید مشابه هم باشند.")

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        super().save(*args, **kwargs)

    def generate_referral_code(self, length=6):
        characters = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choices(characters, k=length))
            if not User.objects.filter(referral_code=code).exists():
                return code

    @property
    def id(self):
        return self.user_uuid


class PhoneOTP(models.Model):
    PURPOSE_CHOICES = (
        ('registration', 'ثبت‌نام'),
        ('login', 'ورود'),
        ('change_phone', 'تغییر شماره'),
    )

    phone_number = models.CharField(max_length=15)
    code = models.CharField(max_length=128)  # هش‌شده
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    purpose = models.CharField(
        max_length=20, choices=PURPOSE_CHOICES, default='registration')
    failed_attempts = models.IntegerField(default=0)

    class Meta:
        verbose_name = "کد تایید"
        verbose_name_plural = "کدهای تایید"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.phone_number} - {self.purpose}"

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=2)

    def increase_failed_attempts(self):
        self.failed_attempts += 1
        self.save(update_fields=['failed_attempts'])

    def verify_code(self, input_code):
        """
        بررسی کد ارسالی توسط کاربر با کد ذخیره‌شده (هش‌شده) و مدیریت تعداد تلاش‌ها
        """
        if self.is_expired():
            return False, "کد منقضی شده است."

        input_hash = hashlib.sha256(input_code.encode()).hexdigest()

        if input_hash != self.code:
            self.increase_failed_attempts()
            if self.failed_attempts >= 5:
                return False, "تعداد تلاش‌های ناموفق بیش از حد مجاز است."
            return False, "کد تأیید اشتباه است."

        return True, "تأیید موفق بود."

    @staticmethod
    def generate_code():
        return str(random.randint(1000, 9999))

    @classmethod
    def create_and_send_otp(cls, phone_number, purpose='registration'):
        """
        ایجاد و ارسال کد تایید (OTP) به شماره موبایل مشخص برای هدف تعیین‌شده.
        """
        try:
            cls.objects.filter(phone_number=phone_number,
                               is_verified=False, purpose=purpose).delete()

            raw_code = cls.generate_code()
            hashed_code = hashlib.sha256(raw_code.encode()).hexdigest()

            cls.objects.create(
                phone_number=phone_number,
                code=hashed_code,
                purpose=purpose
            )

            logging.info(
                f"در حال ارسال کد {raw_code} به شماره {phone_number} برای هدف '{purpose}'.")

            message = f"کد تایید شما: {raw_code}"
            success = send_sms(phone_number, message)

            if success:
                logging.info("پیامک با موفقیت ارسال شد.")
                return True
            else:
                logging.warning("ارسال پیامک با شکست مواجه شد.")
                return False

        except Exception as e:
            logging.error(f"خطا در ایجاد یا ارسال OTP: {str(e)}")
            return False


class Referral(models.Model):
    inviter = models.ForeignKey(User, related_name='sent_referrals',
                                on_delete=models.CASCADE, verbose_name="دعوت‌کننده")
    invited = models.OneToOneField(
        User, related_name='referral', on_delete=models.CASCADE, verbose_name="دعوت‌شده")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="تاریخ عضویت")
    # reward_given = models.BooleanField(default=False, verbose_name="پاداش داده شده؟")

    class Meta:
        verbose_name = "رفرال"
        verbose_name_plural = "رفرال‌ها"
        ordering = ['-created_at']

    def __str__(self):
        inviter_name = self.inviter.get_full_name() or self.inviter.phone_number
        invited_name = self.invited.get_full_name() or self.invited.phone_number
        return f"{inviter_name} → {invited_name}"
