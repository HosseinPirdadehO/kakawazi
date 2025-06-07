# from datetime import datetime, timedelta
# from rest_framework import authentication, exceptions
# from django.conf import settings
# from django.contrib.auth import get_user_model
# import jwt
# from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

# User = get_user_model()


# class JWTAuthentication(authentication.BaseAuthentication):
#     keyword = 'Bearer'

#     def authenticate(self, request):
#         auth_header = authentication.get_authorization_header(request).split()

#         if not auth_header or auth_header[0].lower() != self.keyword.lower().encode():
#             return None  # اجازه دسترسی ناشناس

#         if len(auth_header) == 1:
#             raise exceptions.AuthenticationFailed('توکن ارسال نشده است.')
#         elif len(auth_header) > 2:
#             raise exceptions.AuthenticationFailed(
#                 'هدر Authorization نامعتبر است.')

#         token = auth_header[1].decode()
#         return self.authenticate_credentials(token)

#     def authenticate_credentials(self, token):
#         try:
#             payload = jwt.decode(
#                 token,
#                 settings.SECRET_KEY,
#                 algorithms=["HS256"],
#                 options={"verify_aud": False},  # اگر aud استفاده نشود
#             )
#         except ExpiredSignatureError:
#             raise exceptions.AuthenticationFailed('توکن منقضی شده است.')
#         except InvalidTokenError:
#             raise exceptions.AuthenticationFailed('توکن نامعتبر است.')

#         user_id = payload.get('user_id')
#         if not user_id:
#             raise exceptions.AuthenticationFailed('توکن فاقد شناسه کاربر است.')

#         try:
#             user = User.objects.get(id=user_id)
#         except User.DoesNotExist:
#             raise exceptions.AuthenticationFailed('کاربر موجود نیست.')

#         if not user.is_active:
#             raise exceptions.AuthenticationFailed('کاربر غیرفعال است.')

#         return (user, token)


# def generate_jwt_token(user, expire_minutes=60):
#     payload = {
#         'user_id': str(user.id),
#         'phone_number': user.phone_number,
#         'exp': datetime.utcnow() + timedelta(minutes=expire_minutes),
#         'iat': datetime.utcnow(),
#         # 'aud': 'your_audience',  # در صورت نیاز
#         # 'iss': 'your_issuer',    # در صورت نیاز
#     }
#     token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
#     return token if isinstance(token, str) else token.decode('utf-8')
