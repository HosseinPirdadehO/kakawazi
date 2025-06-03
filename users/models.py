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
    user_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True, verbose_name="شناسه کاربر")
    phone_number = models.CharField(max_length=15, unique=True)
    is_phone_verified = models.BooleanField(default=False)

    referral_code = models.CharField(max_length=10, unique=True, blank=True, null=True, verbose_name="کد دعوت")

    national_code = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name="کد ملی",
        validators=[
            RegexValidator(regex=r'^\d{10}$', message="کد ملی باید ۱۰ رقم باشد.")
        ]
    )

    first_name = models.CharField(max_length=30, blank=True, verbose_name="نام")
    last_name = models.CharField(max_length=30, blank=True, verbose_name="نام خانوادگی")
    email = models.EmailField(blank=True, verbose_name="ایمیل")
    birth_date = models.DateField(null=True, blank=True, verbose_name="تاریخ تولد")
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name="شهر")
    state = models.CharField(max_length=100, blank=True, null=True, verbose_name="استان")
    image = models.URLField(null=True, blank=True, verbose_name="عکس پروفایل")

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
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

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


class PhoneOTP(models.Model):
    phone_number = models.CharField(max_length=15)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    purpose = models.CharField(max_length=20, default='registration')  # یا هر مقدار پیش‌فرض مناسب

    class Meta:
        verbose_name = "کد تایید"
        verbose_name_plural = "کدهای تایید"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.phone_number} - {self.code}"

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=2)

    @staticmethod
    def generate_code():
        return str(random.randint(100000, 999999))  
    
    @classmethod
    def create_and_send_otp(cls, phone_number, purpose='registration'):
        cls.objects.filter(phone_number=phone_number, is_verified=False, purpose=purpose).delete()
        code = cls.generate_code()
        cls.objects.create(phone_number=phone_number, code=code, purpose=purpose)

        print(f"📲 در حال ارسال کد {code} به شماره {phone_number} با هدف {purpose} ...")

        success = send_sms(phone_number, f"کد تایید شما: {code}")
        if success:
            print("✅ پیامک با موفقیت ارسال شد.")
        else:
            print("❌ خطا در ارسال پیامک.")


class Referral(models.Model):
    inviter = models.ForeignKey(User, related_name='sent_referrals', on_delete=models.CASCADE, verbose_name="دعوت‌کننده")
    invited = models.OneToOneField(User, related_name='referral', on_delete=models.CASCADE, verbose_name="دعوت‌شده")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ عضویت")
    # reward_given = models.BooleanField(default=False, verbose_name="پاداش داده شده؟")

    class Meta:
        verbose_name = "رفرال"
        verbose_name_plural = "رفرال‌ها"
        ordering = ['-created_at']

    def __str__(self):
        inviter_name = self.inviter.get_full_name() or self.inviter.phone_number
        invited_name = self.invited.get_full_name() or self.invited.phone_number
        return f"{inviter_name} → {invited_name}"