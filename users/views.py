import hashlib
from django.utils import timezone
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .models import PhoneOTP, User, Referral
from .serializers import (
    SendOTPSerializer,
    VerifyOTPSerializer,
    CompleteProfileSerializer,
    RequestPhoneChangeSerializer,
    VerifyPhoneChangeSerializer,
    UserReferralStatsSerializer,
    ReferralInfoSerializer,
)


def get_or_create_user(phone_number):
    user, created = User.objects.get_or_create(phone_number=phone_number)
    return user, created


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


def generate_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


class SendOTPView(APIView):
    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data["phone_number"]

        last_otp = PhoneOTP.objects.filter(phone_number=phone_number).order_by("-created_at").first()
        if last_otp and (timezone.now() - last_otp.created_at).seconds < 60:
            return Response(
                {"detail": "لطفاً کمی صبر کنید و دوباره تلاش نمایید."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        PhoneOTP.create_and_send_otp(phone_number)
        return Response({"detail": "کد تایید ارسال شد."}, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data["phone_number"]
        referral_code = serializer.validated_data.get("referral_code")

        with transaction.atomic():
            user, created = get_or_create_user(phone_number)
            user.is_phone_verified = True
            user.last_login = timezone.now()
            user.save()

            if created:
                create_referral_if_needed(referral_code, user)

            tokens = generate_tokens_for_user(user)

        return Response({**tokens, "is_new_user": created}, status=status.HTTP_200_OK)


class CompleteProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CompleteProfileSerializer(instance=request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "پروفایل شما با موفقیت تکمیل شد."}, status=status.HTTP_200_OK)


class RequestPhoneChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RequestPhoneChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_phone = serializer.validated_data["new_phone_number"]

        if new_phone == request.user.phone_number:
            return Response(
                {"detail": "شماره جدید نمی‌تواند با شماره فعلی یکسان باشد."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        PhoneOTP.create_and_send_otp(new_phone, purpose="change_phone")

        return Response({"detail": "کد تایید به شماره جدید ارسال شد."}, status=status.HTTP_200_OK)


class VerifyPhoneChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VerifyPhoneChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_phone = serializer.validated_data["new_phone_number"]

        otp_obj = PhoneOTP.objects.filter(
            phone_number=new_phone, purpose="change_phone", is_verified=False
        ).order_by("-created_at").first()

        if not otp_obj:
            return Response({"detail": "کد تأیید اشتباه است یا منقضی شده."}, status=status.HTTP_400_BAD_REQUEST)

        if otp_obj.is_expired():
            return Response({"detail": "کد تأیید منقضی شده است."}, status=status.HTTP_400_BAD_REQUEST)

        code = serializer.validated_data["code"]
        hashed_code = hashlib.sha256(code.encode()).hexdigest()
        if otp_obj.code != hashed_code:
            return Response({"detail": "کد تأیید اشتباه است."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        user.phone_number = new_phone
        user.is_phone_verified = True
        user.save()

        otp_obj.is_verified = True
        otp_obj.save()

        return Response({"detail": "شماره تلفن با موفقیت تغییر کرد."}, status=status.HTTP_200_OK)


class UserReferralStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        referrals = Referral.objects.filter(inviter=user)

        total = referrals.count()
        referral_data = ReferralInfoSerializer(referrals, many=True).data

        data = {
            "total_referrals": total,
            "referrals": referral_data,
        }
        return Response(data, status=status.HTTP_200_OK)