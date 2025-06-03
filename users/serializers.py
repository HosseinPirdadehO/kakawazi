import re
import hashlib
from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PhoneOTP, Referral

User = get_user_model()

class SendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField()

    def validate_phone_number(self, value):
        if not re.match(r'^09\d{9}$', value):
            raise serializers.ValidationError("شماره موبایل معتبر نیست.")
        return value

class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)
    referral_code = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        phone = attrs.get("phone_number")
        otp = attrs.get("otp")

        try:
            otp_record = PhoneOTP.objects.filter(phone_number=phone, purpose='registration', is_verified=False).latest("created_at")
        except PhoneOTP.DoesNotExist:
            raise serializers.ValidationError("کد تأیید پیدا نشد، لطفاً مجدداً درخواست دهید.")

        # اگر تعداد تلاش‌های ناموفق بیشتر از حد باشد
        if hasattr(otp_record, 'failed_attempts') and otp_record.failed_attempts >= 5:
            raise serializers.ValidationError("تعداد تلاش‌های ناموفق بیش از حد مجاز است. لطفاً مجدداً درخواست کد نمایید.")

        # بررسی منقضی شدن کد
        if otp_record.is_expired():
            raise serializers.ValidationError("کد منقضی شده است.")

        # مقایسه کد ارسالی (بدون هش) با کد ذخیره شده (در مدل شما بدون هش ذخیره شده است)
        if otp_record.code != otp:
            # اگر خواستی می‌تونی فیلد failed_attempts رو تو مدل اضافه کنی و اینجا افزایش بدی
            raise serializers.ValidationError("کد تأیید اشتباه است.")

        return attrs
    
    
class CompleteProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(required=True)
    national_code = serializers.CharField(required=True)
    email = serializers.EmailField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['full_name', 'national_code', 'email']

    def validate_national_code(self, value):
        if not re.match(r'^\d{10}$', value):
            raise serializers.ValidationError("کد ملی معتبر نیست.")
        return value

    def update(self, instance, validated_data):
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        return instance


class RequestPhoneChangeSerializer(serializers.Serializer):
    new_phone_number = serializers.CharField(max_length=15)

    def validate_new_phone_number(self, value):
        if not re.match(r'^\+?[1-9]\d{9,14}$', value):
            raise serializers.ValidationError("شماره تلفن نامعتبر است.")
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("این شماره تلفن قبلاً ثبت شده است.")
        return value


class VerifyPhoneChangeSerializer(serializers.Serializer):
    new_phone_number = serializers.CharField(max_length=15)
    code = serializers.CharField(max_length=6)

    def validate(self, data):
        phone = data.get("new_phone_number")
        code = data.get("code")

        if not re.match(r'^\+?[1-9]\d{9,14}$', phone):
            raise serializers.ValidationError({"new_phone_number": "شماره تلفن نامعتبر است."})

        try:
            otp_entry = PhoneOTP.objects.filter(phone_number=phone, purpose='change_phone', is_verified=False).latest('created_at')
        except PhoneOTP.DoesNotExist:
            raise serializers.ValidationError({"code": "کد ارسال نشده یا نامعتبر است."})

        if otp_entry.is_expired():
            raise serializers.ValidationError({"code": "کد تایید منقضی شده است."})

        hashed_input = hashlib.sha256(code.encode()).hexdigest()
        if otp_entry.code != hashed_input:
            raise serializers.ValidationError({"code": "کد تأیید اشتباه است."})

        return data


class ReferralInfoSerializer(serializers.ModelSerializer):
    invited_full_name = serializers.SerializerMethodField()
    invited_registered_at = serializers.DateTimeField(source='invited.date_joined')

    class Meta:
        model = Referral
        fields = ['invited_full_name', 'invited_registered_at']

    def get_invited_full_name(self, obj):
        return f"{obj.invited.first_name} {obj.invited.last_name}"


class UserReferralStatsSerializer(serializers.Serializer):
    total_referrals = serializers.IntegerField()
    referrals = ReferralInfoSerializer(many=True)