# -*- coding: utf-8 -*-
from django.conf import settings
import hashlib
import hashlib
from django.contrib.auth import get_user_model
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .mixins import StandardResponseMixin
from users.models import Referral
from .models import PhoneOTP
from .sms_service import send_sms
from .serializers import (
    PhoneNumberSerializer,
    OTPVerifySerializer,
    ProfileCompleteSerializer,
    LoginPasswordSerializer,
    SetPasswordSerializer,
    InvitedUserSerializer,
    UserProfileSerializer
)
from .mixins import StandardResponseMixin
User = get_user_model()


# --------------------------------------------
# نمایش لیست کاربران
# --------------------------------------------
class UserListView(StandardResponseMixin, generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return self.success_response(message="لیست کاربران دریافت شد.", data=serializer.data)
        except Exception as e:
            return self.error_response(message=f"خطا در دریافت لیست کاربران: {str(e)}")

# -----------------------------------------------
#  ارسال کد تایید (OTP) به شماره موبایل کاربر
# -----------------------------------------------


class SendOTPView(StandardResponseMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone_number = request.data.get('phone_number')
        purpose = request.data.get('purpose', 'registration')

        if not phone_number:
            return self.error_response(message="شماره موبایل ارسال نشده است.", status_code=status.HTTP_400_BAD_REQUEST)

        if purpose == "change_phone":
            if not request.user or not request.user.is_authenticated:
                return self.error_response(message="برای تغییر شماره، ابتدا وارد شوید.", status_code=status.HTTP_403_FORBIDDEN)

            if User.objects.filter(phone_number=phone_number).exclude(id=request.user.id).exists():
                return self.error_response(message="این شماره قبلاً ثبت شده است.", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            PhoneOTP.objects.filter(
                phone_number=phone_number, is_verified=False, purpose=purpose).delete()

            raw_code = PhoneOTP.generate_code()
            hashed_code = hashlib.sha256(raw_code.encode()).hexdigest()

            PhoneOTP.objects.create(
                phone_number=phone_number, code=hashed_code, purpose=purpose)

            success = send_sms(phone_number, raw_code)
            if success:
                return self.success_response(message="کد تایید ارسال شد.")
            else:
                return self.error_response(message="ارسال پیامک با خطا مواجه شد.", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return self.error_response(message=f"خطا در ارسال کد تایید: {str(e)}")


# ------------------------------------------------------
#  تایید کد OTP و ورود یا ثبت‌نام کاربر جدید (JWT)
# ------------------------------------------------------

class VerifyOTPView(generics.GenericAPIView):
    serializer_class = OTPVerifySerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data['phone_number']
        otp = serializer.validated_data['otp']
        referral_code = serializer.validated_data.get('referral_code')
        purpose = serializer.validated_data.get('purpose', 'registration')

        otp_queryset = PhoneOTP.objects.filter(
            phone_number=phone,
            is_verified=False
        )
        if purpose:
            otp_queryset = otp_queryset.filter(purpose=purpose)

        try:
            otp_obj = otp_queryset.latest('created_at')
        except PhoneOTP.DoesNotExist:
            return Response({"detail": "کد تایید معتبر نیست."}, status=status.HTTP_400_BAD_REQUEST)

        valid, msg = otp_obj.verify_code(otp)
        if not valid:
            return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)

        otp_obj.is_verified = True
        otp_obj.save()

        # تغییر شماره موبایل
        if purpose == "change_phone":
            if not request.user.is_authenticated:
                return Response({"detail": "برای تغییر شماره، ابتدا وارد شوید."}, status=status.HTTP_403_FORBIDDEN)

            if User.objects.filter(phone_number=phone).exclude(id=request.user.id).exists():
                return Response({"detail": "این شماره قبلاً توسط کاربر دیگری استفاده شده است."}, status=status.HTTP_400_BAD_REQUEST)

            request.user.phone_number = phone
            request.user.save()
            return Response({"detail": "شماره تلفن با موفقیت تغییر یافت."}, status=status.HTTP_200_OK)

        # ثبت‌نام یا ورود
        user, created = User.objects.get_or_create(phone_number=phone)

        if created:
            user.is_phone_verified = True
            user.is_active = True

            # تعیین نقش برای شماره خاص
            special_phones = getattr(settings, 'SPECIAL_ADMIN_PHONES', [])
            if phone in special_phones:
                user.system_role = User.SystemRole.ADMIN
                user.is_staff = True
                user.is_superuser = True
            else:
                user.system_role = User.SystemRole.USER

            if referral_code:
                inviter = User.objects.filter(
                    referral_code=referral_code).first()
                if inviter:
                    Referral.objects.create(inviter=inviter, invited=user)

            user.save()

        profile_complete = all([user.first_name, user.last_name])

        refresh = RefreshToken.for_user(user)

        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "profile_complete": profile_complete,
            "system_role": user.system_role,
            "redirect_to": "/admin/" if user.system_role == User.SystemRole.ADMIN else "/dashboard/"
        })

# --------------------------------------------
#  ورود با رمز عبور (در صورت تنظیم قبلی)
# --------------------------------------------


class LoginWithPasswordView(StandardResponseMixin, generics.GenericAPIView):
    serializer_class = LoginPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(message="اطلاعات ورود نامعتبر است.", data=serializer.errors)

        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return self.success_response(message="ورود با رمز عبور موفقیت‌آمیز بود.", data={
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        })

# ------------------------------------------------------
#  تکمیل یا بروزرسانی اطلاعات پروفایل کاربر جاری
# ------------------------------------------------------


class CompleteProfileView(StandardResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProfileCompleteSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return self.success_response(message="اطلاعات پروفایل با موفقیت دریافت شد.", data=serializer.data)
        except Exception as e:
            return self.error_response(message=f"خطا در دریافت اطلاعات پروفایل: {str(e)}")

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return self.success_response(message="پروفایل با موفقیت به‌روزرسانی شد.", data=serializer.data)
        except Exception as e:
            return self.error_response(message=f"خطا در به‌روزرسانی پروفایل: {str(e)}")

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        try:
            self.get_object().delete()
            return self.success_response(message="پروفایل کاربری با موفقیت حذف شد.")
        except Exception as e:
            return self.error_response(message=f"خطا در حذف پروفایل: {str(e)}")

# -------------------------------------
#  تنظیم یا تغییر رمز عبور کاربر
# -------------------------------------


class SetPasswordView(StandardResponseMixin, generics.GenericAPIView):
    serializer_class = SetPasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(message="داده‌های ارسالی نامعتبر است.", data=serializer.errors)

        try:
            request.user.set_password(serializer.validated_data['password'])
            request.user.save()
            return self.success_response(message="رمز عبور با موفقیت تغییر کرد.")
        except Exception as e:
            return self.error_response(message=f"خطا در تغییر رمز عبور: {str(e)}")

# -----------------------------------
#  خروج کاربر و بلاک کردن توکن JWT
# -----------------------------------


class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass
        return Response({"detail": "خروج با موفقیت انجام شد."})


# ------------------------------------------------
#  نمایش لیست کاربران دعوت‌شده توسط کاربر جاری
# ------------------------------------------------
class ReferralListView(generics.ListAPIView):
    serializer_class = InvitedUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(received_referral__inviter=self.request.user)


# --------------------------------------------------
#  مشاهده یا ویرایش اطلاعات پروفایل کاربر جاری
# --------------------------------------------------
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


# ------------------------------------------------
#  بررسی اعتبار توکن و اطلاعات کاربر از توکن JWT
# ------------------------------------------------
class TestTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "message": "توکن معتبر است.",
            "user_phone": user.phone_number,
            "user_id": str(user.id),
            "user_full_name": user.get_full_name(),
        })


# -----------------------------------
#  خروج کاربر و بلاک کردن توکن JWT
# -----------------------------------
class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass
        return Response({"detail": "خروج با موفقیت انجام شد."})


# import re
# import hashlib
# from rest_framework import serializers
# from django.contrib.auth import get_user_model
# from .models import PhoneOTP, Referral

# User = get_user_model()


# # ───── Validations ─────
# def validate_iran_phone_number(value):
#     if not re.match(r'^09\d{9}$', value):
#         raise serializers.ValidationError("شماره موبایل معتبر نیست.")
#     return value


# def validate_national_code(value):
#     if not re.match(r'^\d{10}$', value):
#         raise serializers.ValidationError("کد ملی معتبر نیست.")
#     return value


# # ───── OTP Serializers ─────
# class SendOTPSerializer(serializers.Serializer):
#     phone_number = serializers.CharField(
#         validators=[validate_iran_phone_number])


# class VerifyOTPSerializer(serializers.Serializer):
#     phone_number = serializers.CharField(
#         validators=[validate_iran_phone_number])
#     code = serializers.CharField(max_length=4)
#     referral_code = serializers.CharField(required=False, allow_blank=True)

#     def validate(self, attrs):
#         phone, code = attrs["phone_number"], attrs["code"]

#         try:
#             otp = PhoneOTP.objects.filter(
#                 phone_number=phone,
#                 purpose='registration',
#                 is_verified=False
#             ).latest("created_at")
#         except PhoneOTP.DoesNotExist:
#             raise serializers.ValidationError(
#                 {"code": "کد تأیید پیدا نشد. لطفاً مجدداً درخواست دهید."})

#         if otp.is_expired():
#             raise serializers.ValidationError({"code": "کد منقضی شده است."})

#         input_hash = hashlib.sha256(code.encode()).hexdigest()
#         if otp.code != input_hash:
#             otp.increase_failed_attempts()
#             if otp.failed_attempts >= 5:
#                 raise serializers.ValidationError(
#                     {"code": "تعداد تلاش‌های ناموفق بیش از حد مجاز است."})
#             raise serializers.ValidationError({"code": "کد تأیید اشتباه است."})

#         otp.is_verified = True
#         otp.save(update_fields=["is_verified"])
#         return attrs


# # ───── Profile Serializers ─────
# class CompleteProfileSerializer(serializers.ModelSerializer):
#     full_name = serializers.CharField(required=True)
#     national_code = serializers.CharField(
#         required=True, validators=[validate_national_code])
#     email = serializers.EmailField(required=False, allow_blank=True)

#     class Meta:
#         model = User
#         fields = ['full_name', 'national_code', 'email']

#     def update(self, instance, validated_data):
#         for attr, val in validated_data.items():
#             setattr(instance, attr, val)
#         instance.save()
#         return instance


# class UserUpdateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['first_name', 'last_name']


# class UserProfileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['id', 'phone_number', 'first_name',
#                   'last_name', 'referral_code', 'date_joined']


# class SimpleUserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['user_uuid', 'first_name',
#                   'last_name', 'phone_number', 'role']


# # ───── Phone Change Serializers ─────
# class RequestPhoneChangeSerializer(serializers.Serializer):
#     new_phone_number = serializers.CharField(
#         validators=[validate_iran_phone_number])

#     def validate_new_phone_number(self, value):
#         if User.objects.filter(phone_number=value).exists():
#             raise serializers.ValidationError(
#                 "این شماره تلفن قبلاً ثبت شده است.")
#         return value


# class VerifyPhoneChangeSerializer(serializers.Serializer):
#     new_phone_number = serializers.CharField(
#         validators=[validate_iran_phone_number])
#     code = serializers.CharField(max_length=6)

#     def validate(self, data):
#         phone, code = data["new_phone_number"], data["code"]

#         try:
#             otp_entry = PhoneOTP.objects.filter(
#                 phone_number=phone, purpose='change_phone', is_verified=False
#             ).latest('created_at')
#         except PhoneOTP.DoesNotExist:
#             raise serializers.ValidationError(
#                 {"code": "کد ارسال نشده یا نامعتبر است."})

#         if otp_entry.is_expired():
#             raise serializers.ValidationError(
#                 {"code": "کد تأیید منقضی شده است."})

#         hashed_code = hashlib.sha256(code.encode()).hexdigest()
#         if otp_entry.code != hashed_code:
#             raise serializers.ValidationError({"code": "کد تأیید اشتباه است."})

#         return data


# # ───── Password Serializers ─────
# class SetPasswordSerializer(serializers.Serializer):
#     password = serializers.CharField(write_only=True, min_length=6)

#     def validate_password(self, value):
#         if ' ' in value:
#             raise serializers.ValidationError(
#                 "رمز عبور نباید شامل فاصله باشد.")
#         return value


# class ChangePasswordSerializer(serializers.Serializer):
#     old_password = serializers.CharField()
#     new_password = serializers.CharField(min_length=6)

#     def validate_old_password(self, value):
#         user = self.context['request'].user
#         if not user.check_password(value):
#             raise serializers.ValidationError("رمز عبور فعلی نادرست است.")
#         return value


# # ───── Referral Serializers ─────
# class ReferralInfoSerializer(serializers.ModelSerializer):
#     invited_full_name = serializers.SerializerMethodField()
#     invited_registered_at = serializers.DateTimeField(
#         source='invited.date_joined')

#     class Meta:
#         model = Referral
#         fields = ['invited_full_name', 'invited_registered_at']

#     def get_invited_full_name(self, obj):
#         return f"{obj.invited.first_name or ''} {obj.invited.last_name or ''}".strip()


# class UserReferralStatsSerializer(serializers.Serializer):
#     total_referrals = serializers.IntegerField()
#     referrals = ReferralInfoSerializer(many=True)
