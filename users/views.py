from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
import hashlib

from .models import PhoneOTP, User, Referral
from .serializers import (
    SendOTPSerializer, VerifyOTPSerializer, CompleteProfileSerializer,
    RequestPhoneChangeSerializer, VerifyPhoneChangeSerializer,
    ReferralInfoSerializer, SimpleUserSerializer, SetPasswordSerializer
)


# توکن JWT برای کاربر
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


# ساخت یا دریافت کاربر
def get_or_create_user(phone_number):
    return User.objects.get_or_create(phone_number=phone_number)


# ثبت دعوت اگر کد رفرال وجود داشته باشد
def create_referral_if_needed(referral_code, new_user):
    if referral_code:
        try:
            inviter = User.objects.get(referral_code=referral_code)
            if not Referral.objects.filter(invited=new_user).exists():
                Referral.objects.create(inviter=inviter, invited=new_user)
        except User.DoesNotExist:
            pass

    if not new_user.referral_code:
        new_user.referral_code = new_user.generate_referral_code()
        new_user.save()


# ارسال کد تأیید
class SendOTPView(APIView):
    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data["phone_number"]

        last_otp = PhoneOTP.objects.filter(
            phone_number=phone_number).order_by("-created_at").first()
        if last_otp and (timezone.now() - last_otp.created_at).seconds < 60:
            return Response(
                {"detail": "لطفاً کمی صبر کنید و سپس دوباره تلاش کنید."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        PhoneOTP.create_and_send_otp(phone_number)
        return Response({"detail": "کد تأیید ارسال شد."}, status=status.HTTP_200_OK)


# تأیید کد OTP
class VerifyOTPView(APIView):
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data['phone_number']
        code = serializer.validated_data['code']
        referral_code = serializer.validated_data.get('referral_code')

        try:
            otp_obj = PhoneOTP.objects.get(
                phone_number=phone_number, code=code, is_verified=False
            )
        except PhoneOTP.DoesNotExist:
            return Response({"error": "کد تأیید نادرست است."}, status=400)

        if otp_obj.is_expired():
            return Response({"error": "کد منقضی شده است."}, status=400)

        otp_obj.is_verified = True
        otp_obj.save()

        user, created = User.objects.get_or_create(phone_number=phone_number)
        if created:
            create_referral_if_needed(referral_code, user)

        tokens = get_tokens_for_user(user)
        return Response({
            "message": "کد تأیید شد.",
            "user_created": created,
            "access": tokens["access"],
            "refresh": tokens["refresh"],
        })


# تکمیل پروفایل
class CompleteProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CompleteProfileSerializer(
            instance=request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "پروفایل با موفقیت تکمیل شد."}, status=status.HTTP_200_OK)


# تنظیم رمز عبور
class SetPasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["password"])
        request.user.save()
        return Response({"message": "رمز عبور با موفقیت ذخیره شد."}, status=status.HTTP_200_OK)


# درخواست تغییر شماره
class RequestPhoneChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RequestPhoneChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_phone = serializer.validated_data["new_phone_number"]

        if new_phone == request.user.phone_number:
            return Response(
                {"detail": "شماره جدید نمی‌تواند با شماره فعلی یکسان باشد."},
                status=status.HTTP_400_BAD_REQUEST
            )

        PhoneOTP.create_and_send_otp(new_phone, purpose="change_phone")
        return Response({"detail": "کد تأیید برای شماره جدید ارسال شد."}, status=status.HTTP_200_OK)


# تأیید تغییر شماره
class VerifyPhoneChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VerifyPhoneChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_phone = serializer.validated_data["new_phone_number"]
        code = serializer.validated_data["code"]

        otp_obj = PhoneOTP.objects.filter(
            phone_number=new_phone, purpose="change_phone", is_verified=False
        ).order_by("-created_at").first()

        if not otp_obj:
            return Response({"detail": "کد تأیید یافت نشد."}, status=400)

        if otp_obj.is_expired():
            return Response({"detail": "کد تأیید منقضی شده است."}, status=400)

        hashed_code = hashlib.sha256(code.encode()).hexdigest()
        if otp_obj.code != hashed_code:
            return Response({"detail": "کد تأیید اشتباه است."}, status=400)

        user = request.user
        user.phone_number = new_phone
        user.is_phone_verified = True
        user.save()

        otp_obj.is_verified = True
        otp_obj.save()

        return Response({"detail": "شماره با موفقیت تغییر کرد."}, status=200)


# لیست ارجاعات من
class UserReferralStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        referrals = Referral.objects.filter(inviter=request.user)
        data = {
            "total_referrals": referrals.count(),
            "referrals": ReferralInfoSerializer(referrals, many=True).data
        }
        return Response(data, status=200)


# ساختار درختی ارجاعات (مدیر → راننده → دانش‌آموز)
class ReferralTreeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        manager = request.user

        if manager.role != 'school_manager':
            return Response({"detail": "دسترسی فقط برای مدیران مدرسه مجاز است."}, status=403)

        tree = []

        driver_referrals = Referral.objects.filter(
            inviter=manager, invited__role='taxi_driver'
        ).select_related('invited')

        for driver_ref in driver_referrals:
            driver = driver_ref.invited
            student_referrals = Referral.objects.filter(
                inviter=driver, invited__role='student'
            ).select_related('invited')

            students = [SimpleUserSerializer(
                ref.invited).data for ref in student_referrals]

            tree.append({
                "driver": SimpleUserSerializer(driver).data,
                "students": students
            })

        return Response({
            "manager": SimpleUserSerializer(manager).data,
            "referral_tree": tree
        }, status=200)
