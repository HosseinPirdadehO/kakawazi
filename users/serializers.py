import re
import hashlib
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PhoneOTP, Referral

User = get_user_model()


def validate_iran_phone_number(value):
    if not re.match(r'^09\d{9}$', value):
        raise serializers.ValidationError("شماره موبایل معتبر نیست.")
    return value


class SendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        validators=[validate_iran_phone_number])


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        validators=[validate_iran_phone_number])
    code = serializers.CharField(max_length=4)
    referral_code = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        phone = attrs.get("phone_number")
        code = attrs.get("code")

        try:
            otp = PhoneOTP.objects.filter(
                phone_number=phone,
                purpose='registration',
                is_verified=False
            ).latest("created_at")
        except PhoneOTP.DoesNotExist:
            raise serializers.ValidationError(
                "کد تأیید پیدا نشد. لطفاً مجدداً درخواست دهید.")

        if otp.is_expired():
            raise serializers.ValidationError("کد منقضی شده است.")

        if otp.code != code:
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
    new_phone_number = serializers.CharField(
        validators=[validate_iran_phone_number])

    def validate_new_phone_number(self, value):
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError(
                "این شماره تلفن قبلاً ثبت شده است.")
        return value


class VerifyPhoneChangeSerializer(serializers.Serializer):
    new_phone_number = serializers.CharField(
        validators=[validate_iran_phone_number])
    code = serializers.CharField(max_length=6)

    def validate(self, data):
        phone = data.get("new_phone_number")
        code = data.get("code")

        try:
            otp_entry = PhoneOTP.objects.filter(
                phone_number=phone, purpose='change_phone', is_verified=False
            ).latest('created_at')
        except PhoneOTP.DoesNotExist:
            raise serializers.ValidationError(
                {"code": "کد ارسال نشده یا نامعتبر است."})

        if otp_entry.is_expired():
            raise serializers.ValidationError(
                {"code": "کد تأیید منقضی شده است."})

        hashed_code = hashlib.sha256(code.encode()).hexdigest()
        if otp_entry.code != hashed_code:
            raise serializers.ValidationError({"code": "کد تأیید اشتباه است."})

        return data


class SetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, min_length=6)

    def validate_password(self, value):
        if ' ' in value:
            raise serializers.ValidationError(
                "رمز عبور نباید شامل فاصله باشد.")
        return value


class ReferralInfoSerializer(serializers.ModelSerializer):
    invited_full_name = serializers.SerializerMethodField()
    invited_registered_at = serializers.DateTimeField(
        source='invited.date_joined')

    class Meta:
        model = Referral
        fields = ['invited_full_name', 'invited_registered_at']

    def get_invited_full_name(self, obj):
        return f"{obj.invited.first_name or ''} {obj.invited.last_name or ''}".strip()


class UserReferralStatsSerializer(serializers.Serializer):
    total_referrals = serializers.IntegerField()
    referrals = ReferralInfoSerializer(many=True)


class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_uuid', 'first_name',
                  'last_name', 'phone_number', 'role']
