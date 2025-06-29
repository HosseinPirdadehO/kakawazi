from .models import User
from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from users.models import Referral, PhoneOTP

User = get_user_model()

# --------------------------------------------
#  نمایش لیست تمام کاربران ثبت‌نام‌شده
# --------------------------------------------


class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'phone_number', 'first_name',
                  'last_name', 'referral_code',]


# ------------------------------
# احراز هویت با شماره موبایل و رمز
# ------------------------------


class LoginPasswordSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        phone_number = attrs.get("phone_number")
        password = attrs.get("password")

        if not (phone_number and password):
            raise serializers.ValidationError(
                "شماره موبایل و رمز عبور الزامی هستند.")

        user = authenticate(username=phone_number, password=password)
        if not user:
            raise serializers.ValidationError(
                "نام کاربری یا رمز عبور نادرست است.")

        attrs['user'] = user
        return attrs


# ------------------------------
# ارسال شماره موبایل
# ------------------------------

class PhoneNumberSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)


# ------------------------------
# تایید کد OTP
# ------------------------------

class OTPVerifySerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=4)
    purpose = serializers.CharField(required=False, allow_blank=True)
    referral_code = serializers.CharField(required=False, allow_blank=True)


# ------------------------------
# تعیین رمز عبور جدید
# ------------------------------


class SetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(
        write_only=True,
        min_length=4,
        max_length=128,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        min_length=4,
        max_length=128,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')

        if not password or not password_confirm:
            raise serializers.ValidationError(
                "رمز عبور و تکرار آن الزامی است.")

        if password != password_confirm:
            raise serializers.ValidationError("رمزهای عبور مطابقت ندارند.")

        return attrs

# ------------------------------
# تکمیل پروفایل
# ------------------------------


class ProfileCompleteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=False, min_length=4)
    password_confirm = serializers.CharField(
        write_only=True, required=False, min_length=4)

    class Meta:
        model = User
        fields = [
            "first_name", "last_name", "email", "birth_date",
            "city", "state", "national_code", "plate_number",
            "type_of_car", "system_role", "job_role",
            "password", "password_confirm", 'referral_code',
            'school',
        ]

    def validate(self, attrs):
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        if password or password_confirm:
            if password != password_confirm:
                raise serializers.ValidationError("رمزهای عبور مطابقت ندارند.")
        return attrs

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        validated_data.pop('password_confirm', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance

# ------------------------------
# لیست کاربران دعوت‌شده توسط رفرال
# ------------------------------


class InvitedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone_number',
                  'first_name', 'last_name', 'date_joined']


# ------------------------------
# مشاهده یا ویرایش پروفایل کاربر
# ------------------------------
class TokenResponseSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()
    profile_complete = serializers.BooleanField()

# ------------------------------

# ------------------------------


class FullUserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    referral_code = serializers.CharField(read_only=True)
    referrals_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "phone_number",
            "is_phone_verified",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "birth_date",
            "city",
            "state",
            "school",
            "image",
            "national_code",
            "plate_number",
            "type_of_car",
            "job_role",
            "system_role",
            "status",
            "referral_code",
            "referrals_count",
            "date_joined",
            "created_at",
            "last_login",
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_referrals_count(self, obj):
        return obj.referrals.count()
