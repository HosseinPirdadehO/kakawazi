from users.models import User, Referral
from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from .models import PhoneOTP

User = get_user_model()


class PhoneNumberSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)


class OTPVerifySerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=4)
    purpose = serializers.CharField(
        required=False, allow_blank=True)  # اختیاری
    referral_code = serializers.CharField(required=False, allow_blank=True)


class SetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True, min_length=6)

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("رمزهای عبور مطابقت ندارند.")
        return attrs


class ProfileCompleteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=False, min_length=6)
    password_confirm = serializers.CharField(
        write_only=True, required=False, min_length=6)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "birth_date",
            "city",
            "state",
            "national_code",
            "plate_number",
            "type_of_car",
            "role",
            "password",
            "password_confirm",
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


class LoginPasswordSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        phone_number = attrs.get('phone_number')
        password = attrs.get('password')

        user = authenticate(username=phone_number, password=password)
        if not user:
            raise serializers.ValidationError(
                "شماره موبایل یا رمز عبور اشتباه است.")
        if not user.is_active:
            raise serializers.ValidationError("کاربر غیرفعال است.")
        attrs['user'] = user
        return attrs


class InvitedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone_number',
                  'first_name', 'last_name', 'date_joined']


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone_number', 'first_name',
                  'last_name', 'email', 'referral_code']
        # شماره و کد رفرال قابل تغییر نیست
        read_only_fields = ['id', 'phone_number', 'referral_code']


# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status, permissions
# from rest_framework.permissions import IsAuthenticated
# from rest_framework_simplejwt.tokens import RefreshToken
# from django.utils import timezone
# import hashlib

# from .models import PhoneOTP, User, Referral
# from .serializers import (
#     SendOTPSerializer, VerifyOTPSerializer, CompleteProfileSerializer,
#     RequestPhoneChangeSerializer, VerifyPhoneChangeSerializer,
#     ReferralInfoSerializer, SimpleUserSerializer,
#     SetPasswordSerializer, ChangePasswordSerializer,
#     UserProfileSerializer, UserUpdateSerializer
# )


# def get_tokens_for_user(user):
#     refresh = RefreshToken.for_user(user)
#     return {
#         'refresh': str(refresh),
#         'access': str(refresh.access_token),
#     }


# def create_referral_if_needed(referral_code, user):
#     if referral_code and not Referral.objects.filter(invited=user).exists():
#         try:
#             inviter = User.objects.get(referral_code=referral_code)
#             Referral.objects.create(inviter=inviter, invited=user)
#         except User.DoesNotExist:
#             pass

#     if not user.referral_code:
#         user.referral_code = user.generate_referral_code()
#         user.save()


# class SendOTPView(APIView):
#     def post(self, request):
#         serializer = SendOTPSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         phone_number = serializer.validated_data["phone_number"]
#         last_otp = PhoneOTP.objects.filter(
#             phone_number=phone_number).order_by("-created_at").first()

#         if last_otp and (timezone.now() - last_otp.created_at).seconds < 60:
#             return Response({"detail": "لطفاً کمی صبر کنید."}, status=429)

#         PhoneOTP.create_and_send_otp(phone_number)
#         return Response({"detail": "کد تأیید ارسال شد."}, status=200)


# class VerifyOTPView(APIView):
#     def post(self, request):
#         serializer = VerifyOTPSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         phone = serializer.validated_data["phone_number"]
#         referral_code = serializer.validated_data.get("referral_code")

#         user, created = User.objects.get_or_create(phone_number=phone)
#         if created:
#             create_referral_if_needed(referral_code, user)

#         tokens = get_tokens_for_user(user)
#         return Response({
#             "message": "کد تأیید شد.",
#             "user_created": created,
#             **tokens
#         })


# class CompleteProfileView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         serializer = CompleteProfileSerializer(
#             request.user, data=request.data, partial=True)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response({"detail": "پروفایل با موفقیت تکمیل شد."}, status=200)


# class SetPasswordView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         serializer = SetPasswordSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         request.user.set_password(serializer.validated_data["password"])
#         request.user.save()
#         return Response({"message": "رمز عبور با موفقیت تنظیم شد."}, status=200)


# class ChangePasswordView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         serializer = ChangePasswordSerializer(
#             data=request.data, context={'request': request})
#         serializer.is_valid(raise_exception=True)
#         request.user.set_password(serializer.validated_data["new_password"])
#         request.user.save()
#         return Response({"message": "رمز عبور با موفقیت تغییر کرد."}, status=200)


# class RequestPhoneChangeView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         serializer = RequestPhoneChangeSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         new_phone = serializer.validated_data["new_phone_number"]

#         if new_phone == request.user.phone_number:
#             return Response({"detail": "شماره جدید نمی‌تواند همان شماره قبلی باشد."}, status=400)

#         PhoneOTP.create_and_send_otp(new_phone, purpose="change_phone")
#         return Response({"detail": "کد تأیید ارسال شد."}, status=200)


# class VerifyPhoneChangeView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         serializer = VerifyPhoneChangeSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         new_phone = serializer.validated_data["new_phone_number"]
#         code = serializer.validated_data["code"]

#         otp_obj = PhoneOTP.objects.filter(
#             phone_number=new_phone,
#             purpose="change_phone",
#             is_verified=False
#         ).order_by("-created_at").first()

#         if not otp_obj:
#             return Response({"detail": "کد تأیید یافت نشد."}, status=400)

#         if otp_obj.is_expired():
#             return Response({"detail": "کد منقضی شده است."}, status=400)

#         hashed_code = hashlib.sha256(code.encode()).hexdigest()
#         if otp_obj.code != hashed_code:
#             return Response({"detail": "کد اشتباه است."}, status=400)

#         request.user.phone_number = new_phone
#         request.user.is_phone_verified = True
#         request.user.save()

#         otp_obj.is_verified = True
#         otp_obj.save()

#         return Response({"detail": "شماره با موفقیت تغییر کرد."}, status=200)


# class UserReferralStatsView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         referrals = Referral.objects.filter(inviter=request.user)
#         return Response({
#             "total_referrals": referrals.count(),
#             "referrals": ReferralInfoSerializer(referrals, many=True).data
#         })


# class ReferralTreeView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         if request.user.role != "school_manager":
#             return Response({"detail": "دسترسی غیرمجاز."}, status=403)

#         tree = []
#         driver_refs = Referral.objects.filter(
#             inviter=request.user, invited__role="taxi_driver")

#         for driver_ref in driver_refs:
#             driver = driver_ref.invited
#             students = Referral.objects.filter(
#                 inviter=driver, invited__role="student")
#             tree.append({
#                 "driver": SimpleUserSerializer(driver).data,
#                 "students": SimpleUserSerializer([s.invited for s in students], many=True).data
#             })

#         return Response({
#             "manager": SimpleUserSerializer(request.user).data,
#             "referral_tree": tree
#         })


# class UserProfileView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         return Response(UserProfileSerializer(request.user).data, status=200)


# class UserProfileUpdateView(APIView):
#     permission_classes = [IsAuthenticated]

#     def put(self, request):
#         serializer = UserUpdateSerializer(
#             request.user, data=request.data, partial=True)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response({"message": "پروفایل با موفقیت به‌روزرسانی شد."})


# class LogoutView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         try:
#             token = RefreshToken(request.data["refresh"])
#             token.blacklist()
#             return Response({"message": "خروج موفقیت‌آمیز بود."}, status=205)
#         except Exception:
#             return Response({"error": "توکن نامعتبر یا از قبل باطل شده است."}, status=400)


# class TestTokenView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         return Response({"message": "Token is valid."})
