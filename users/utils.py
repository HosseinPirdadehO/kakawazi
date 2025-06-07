# import hashlib
# from .models import PhoneOTP
# from rest_framework import serializers
# import jwt
# from datetime import datetime, timedelta
# from django.conf import settings


# def create_jwt_token(user):
#     payload = {
#         'user_id': user.id,
#         'phone_number': user.phone_number,
#         'exp': datetime.utcnow() + timedelta(hours=1),  # انقضا 1 ساعت بعد
#         'iat': datetime.utcnow(),
#     }
#     token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
#     return token


# def validate_otp_code(phone_number, code, purpose):
#     try:
#         otp_entry = PhoneOTP.objects.filter(
#             phone_number=phone_number,
#             purpose=purpose,
#             is_verified=False
#         ).latest('created_at')
#     except PhoneOTP.DoesNotExist:
#         raise serializers.ValidationError(
#             {"code": "کد تأیید پیدا نشد. لطفاً مجدداً درخواست دهید."})

#     if otp_entry.is_expired():
#         raise serializers.ValidationError({"code": "کد تأیید منقضی شده است."})

#     hashed_code = hashlib.sha256(code.encode()).hexdigest()
#     if otp_entry.code != hashed_code:
#         otp_entry.increase_failed_attempts()
#         if otp_entry.failed_attempts >= 5:
#             raise serializers.ValidationError(
#                 {"code": "تعداد تلاش‌های ناموفق بیش از حد مجاز است."})
#         raise serializers.ValidationError({"code": "کد تأیید اشتباه است."})

#     # اگر رسیدیم اینجا یعنی کد معتبر است، می‌توانیم بلافاصله otp را وریفای کنیم
#     otp_entry.is_verified = True
#     otp_entry.save(update_fields=["is_verified"])
