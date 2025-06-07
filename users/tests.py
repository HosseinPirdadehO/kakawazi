# from django.test import TestCase

# # Create your tests here.
# import os
# from pathlib import Path
# from datetime import timedelta

# BASE_DIR = Path(__file__).resolve().parent.parent

# # ========================
# # Basic settings
# # ========================

# SECRET_KEY = os.getenv('DJANGO_SECRET_KEY',
#                        'django-insecure-default-key-for-dev-only')

# DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'

# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:3000",
#     "https://tda24.ir",
# ]

# ALLOWED_HOSTS = ['api.tda24.ir']
# # ========================
# # Installed apps & Middleware
# # ========================

# INSTALLED_APPS = [
#     'django.contrib.admin',
#     'django.contrib.auth',
#     'django.contrib.contenttypes',
#     'django.contrib.sessions',
#     'django.contrib.messages',
#     'django.contrib.staticfiles',

#     # Third-party apps
#     'rest_framework',

#     # Local apps
#     'users',
# ]

# AUTH_USER_MODEL = 'users.User'

# MIDDLEWARE = [
#     'django.middleware.security.SecurityMiddleware',
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     'django.middleware.clickjacking.XFrameOptionsMiddleware',
# ]

# ROOT_URLCONF = 'taxi.urls'

# # ========================
# # Templates
# # ========================

# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [],  # اگر تمپلیت های سفارشی دارید اینجا اضافه کنید
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.debug',
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#             ],
#         },
#     },
# ]

# WSGI_APPLICATION = 'taxi.wsgi.application'

# # ========================
# # Database
# # ========================

# DATABASES = {
#     'default': {
#         'ENGINE': os.getenv('DJANGO_DB_ENGINE', 'django.db.backends.sqlite3'),
#         'NAME': os.getenv('DJANGO_DB_NAME', BASE_DIR / 'db.sqlite3'),
#         #
#     }
# }

# # ========================
# # Password validation
# # ========================

# AUTH_PASSWORD_VALIDATORS = [
#     {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
#     {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
#     {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
#     {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
# ]

# # ========================
# # Internationalization
# # ========================

# LANGUAGE_CODE = 'fa'  # زبان فارسی

# TIME_ZONE = 'Asia/Tehran'

# USE_I18N = True
# USE_TZ = True

# # ========================
# # Static and Media files
# # ========================

# STATIC_URL = '/static/'
# STATIC_ROOT = os.getenv('DJANGO_STATIC_ROOT',
#                         os.path.join(BASE_DIR, 'staticfiles'))

# MEDIA_URL = '/media/'
# MEDIA_ROOT = os.getenv('DJANGO_MEDIA_ROOT', os.path.join(BASE_DIR, 'media'))

# # ========================
# # REST Framework & JWT
# # ========================


# REST_FRAMEWORK = {
#     'DEFAULT_AUTHENTICATION_CLASSES': (
#         'rest_framework_simplejwt.authentication.JWTAuthentication',
#     ),
#     'DEFAULT_PERMISSION_CLASSES': (
#         'rest_framework.permissions.IsAuthenticated',
#     ),
# }


# SIMPLE_JWT = {
#     'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
#     'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
#     'AUTH_HEADER_TYPES': ('Bearer',),
# }

# # ========================
# # Logging
# # ========================

# LOG_DIR = os.getenv('DJANGO_LOG_DIR', os.path.join(BASE_DIR, 'logs'))
# os.makedirs(LOG_DIR, exist_ok=True)

# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'verbose': {
#             'format': '[{asctime}] {levelname} {name} {message}',
#             'style': '{',
#         },
#     },
#     'handlers': {
#         'console': {
#             'class': 'logging.StreamHandler',
#             'formatter': 'verbose',
#         },
#         'file': {
#             'class': 'logging.FileHandler',
#             'formatter': 'verbose',
#             'filename': os.path.join(LOG_DIR, 'app.log'),
#             'encoding': 'utf-8',
#         },
#     },
#     'root': {
#         'handlers': ['console', 'file'],
#         'level': 'INFO',
#     },
# }

# # ========================
# # Other settings
# # ========================

# DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# # SIMPLE_JWT = {
# #     'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
# #     'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
# #     'ROTATE_REFRESH_TOKENS': True,  #
# #     'BLACKLIST_AFTER_ROTATION': True, #
# #     'ALGORITHM': 'HS256',
# #     'SIGNING_KEY': SECRET_KEY,
# #     'AUTH_HEADER_TYPES': ('Bearer',),
# #     # تنظیمات دیگر ...
# # }
