import hashlib
from rest_framework import generics, permissions
from users.models import Referral
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .sms_service import send_sms

from .serializers import (
    PhoneNumberSerializer,
    OTPVerifySerializer,
    ProfileCompleteSerializer,
    LoginPasswordSerializer,
    SetPasswordSerializer,
    InvitedUserSerializer, UserProfileSerializer
)
from .models import PhoneOTP

User = get_user_model()


# ارسال OTP به شماره

class SendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone_number = request.data.get('phone_number')
        purpose = request.data.get('purpose', 'registration')

        if not phone_number:
            return Response({"error": "شماره موبایل ارسال نشده است."}, status=status.HTTP_400_BAD_REQUEST)

        # حذف OTPهای قبلی برای این شماره و هدف
        PhoneOTP.objects.filter(phone_number=phone_number,
                                is_verified=False, purpose=purpose).delete()

        # ایجاد کد جدید
        raw_code = PhoneOTP.generate_code()
        hashed_code = hashlib.sha256(raw_code.encode()).hexdigest()

        # ذخیره در دیتابیس
        otp = PhoneOTP.objects.create(
            phone_number=phone_number,
            code=hashed_code,
            purpose=purpose
        )

        # ارسال پیامک
        success = send_sms(phone_number, raw_code)
        if success:
            return Response({"message": "کد تایید ارسال شد."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "ارسال پیامک با خطا مواجه شد."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# تایید OTP و ورود یا ثبت نام


class VerifyOTPView(generics.GenericAPIView):
    serializer_class = OTPVerifySerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("Validation errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone = serializer.validated_data['phone_number']
        otp = serializer.validated_data['otp']
        referral_code = serializer.validated_data.get('referral_code', None)
        purpose = serializer.validated_data.get(
            'purpose', None)  # اگر خواستی purpose هم بگیری

        # اگر قصد داری purpose هم بگیری، ابتدا تو Serializer اضافه کن

        # کوئری فیلتر
        otp_queryset = PhoneOTP.objects.filter(
            phone_number=phone, is_verified=False)
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

        user, created = User.objects.get_or_create(phone_number=phone)
        if created:
            user.is_phone_verified = True
            user.is_active = True

            if referral_code:
                try:
                    inviter = User.objects.get(referral_code=referral_code)
                except User.DoesNotExist:
                    inviter = None

                if inviter:
                    Referral.objects.create(inviter=inviter, invited=user)

            user.save()
            profile_complete = False
        else:
            profile_complete = all([user.first_name, user.last_name])

        refresh = RefreshToken.for_user(user)
        data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "profile_complete": profile_complete,
        }

        return Response(data)
# ورود با پسورد


class LoginWithPasswordView(generics.GenericAPIView):
    serializer_class = LoginPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        })


# تکمیل پروفایل و ست کردن پسورد
class CompleteProfileView(generics.UpdateAPIView):
    serializer_class = ProfileCompleteSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


# تغییر پسورد جداگانه (اگر لازم بود)
class SetPasswordView(generics.GenericAPIView):
    serializer_class = SetPasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data['password']
        user = request.user
        user.set_password(password)
        user.save()
        return Response({"detail": "رمز عبور با موفقیت تغییر کرد."})


# خروج (logout)
class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # اگر refresh token رو از کلاینت بفرستیم، می‌تونیم blacklist کنیم
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass
        return Response({"detail": "خروج با موفقیت انجام شد."})

# from rest_framework_simplejwt.tokens import RefreshToken
# from rest_framework.views import APIView
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework import status

# class LogoutView(APIView):
#     permission_classes = (IsAuthenticated,)

#     def post(self, request):
#         try:
#             refresh_token = request.data["refresh"]
#             token = RefreshToken(refresh_token)
#             token.blacklist()  # اضافه کردن توکن به بلک‌لیست
#             return Response(status=status.HTTP_205_RESET_CONTENT)
#         except Exception as e:
#             return Response(status=status.HTTP_400_BAD_REQUEST)


class ReferralListView(generics.ListAPIView):
    serializer_class = InvitedUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # لیست Referralهایی که این کاربر دعوت کرده
        return User.objects.filter(received_referral__inviter=user)


class TestTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            "message": "توکن معتبر است.",
            "user_phone": user.phone_number,
            "user_id": str(user.id),
            "user_full_name": user.get_full_name(),
        }
        return Response(data)


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # فقط کاربر جاری پروفایل خودش را می‌بیند و ویرایش می‌کند
        return self.request.user


class TestTokenView(APIView):
    def get(self, request):
        return Response({"message": "Test token view works!"})

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
