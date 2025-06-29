# اصلی
from django.conf import settings
import requests
import logging

API_KEY = 'L40UGRICQDvHN3F93OuDafT0xiom3okCphDgtrAfYjpng77f9ZzNaahQGyp9wI5b'
TEMPLATE_ID = 312572
URL = "https://api.sms.ir/v1/send/verify"


def send_sms(mobile: str, code: str) -> bool:
    """
    ارسال پیامک از طریق پنل SMS.ir
    :param mobile: شماره موبایل گیرنده (مثال: '09120000000')
    :param code: کد تایید یا متنی که باید در قالب ارسال شود
    :return: True اگر پیامک با موفقیت ارسال شد، در غیر این صورت False
    """
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-API-KEY': API_KEY
    }

    payload = {
        "Mobile": mobile,
        "TemplateId": TEMPLATE_ID,
        "Parameters": [
            {
                "Name": "code",
                "Value": str(code)
            }
        ]
    }

    try:
        response = requests.post(URL, json=payload, headers=headers)
        response.raise_for_status()  # Raises HTTPError for bad status codes

        result = response.json()
        if result.get("status") == 1:
            logging.info("پیامک با موفقیت ارسال شد.")
            return True
        else:
            logging.warning(f"پیامک ارسال نشد: {result.get('message')}")
            return False

    except requests.exceptions.RequestException as e:
        logging.error(f"خطای ارتباط با سرور SMS.ir: {e}")
        return False
    except ValueError:
        logging.error("خطا در پردازش پاسخ JSON از SMS.ir")
        return False


# تست لوکال بک
# def send_sms(mobile: str, code: str) -> bool:
#     if settings.DEBUG:
#         logging.info(
#             f"[FAKE SMS] کد {code} به شماره {mobile} ارسال شد (حالت DEBUG)")
#         return True

#     headers = {
#         'Content-Type': 'application/json',
#         'Accept': 'application/json',
#         'X-API-KEY': API_KEY
#     }

#     payload = {
#         "mobile": mobile,
#         "templateId": TEMPLATE_ID,
#         "parameters": [
#             {
#                 "name": "code",
#                 "value": str(code)
#             }
#         ]
#     }

#     try:
#         response = requests.post(URL, json=payload, headers=headers)
#         response.raise_for_status()

#         result = response.json()
#         if result.get("status") == 1:
#             logging.info("پیامک با موفقیت ارسال شد.")
#             return True
#         else:
#             logging.warning(f"پیامک ارسال نشد: {result.get('message')}")
#             return False

#     except requests.exceptions.RequestException as e:
#         logging.error(f"خطای ارتباط با سرور SMS.ir: {e}")
#         return False
#     except ValueError:
#         logging.error("خطا در پردازش پاسخ JSON از SMS.ir")
#         return False
# #  تست فرانت
# import logging
# from django.conf import settings
# import requests

# # حالت تست فعال باشد یا نه؟
# TEST_MODE = getattr(settings, 'SMS_TEST_MODE', True)  # پیش‌فرض True برای تست

# API_KEY = '...'  # حتماً در محیط واقعی از env استفاده کن
# TEMPLATE_ID = 312572
# URL = "https://api.sms.ir/v1/send/verify"


# def send_sms(mobile: str, code: str) -> bool | str:
#     """
#     اگر TEST_MODE فعال باشد، به‌جای ارسال پیامک، کد را مستقیماً برمی‌گرداند.
#     """
#     if TEST_MODE:
#         logging.info(f"[TEST MODE] کد تأیید برای {mobile}: {code}")
#         return code  # به ویو برگردون تا در خروجی JSON فرستاده بشه

#     # حالت عادی (ارسال واقعی پیامک)
#     headers = {
#         'Content-Type': 'application/json',
#         'Accept': 'application/json',
#         'X-API-KEY': API_KEY
#     }

#     payload = {
#         "Mobile": mobile,
#         "TemplateId": TEMPLATE_ID,
#         "Parameters": [
#             {
#                 "Name": "code",
#                 "Value": str(code)
#             }
#         ]
#     }

#     try:
#         response = requests.post(URL, json=payload, headers=headers)
#         response.raise_for_status()
#         result = response.json()
#         if result.get("status") == 1:
#             logging.info("پیامک با موفقیت ارسال شد.")
#             return True
#         else:
#             logging.warning(f"پیامک ارسال نشد: {result.get('message')}")
#             return False
#     except Exception as e:
#         logging.error(f"خطا در ارسال پیامک: {e}")
#         return False

# import requests
# import logging
# import time

# API_KEY = 'L40UGRICQDvHN3F93OuDafT0xiom3okCphDgtrAfYjpng77f9ZzNaahQGyp9wI5b'
# TEMPLATE_ID = 312572
# URL = "https://api.sms.ir/v1/send/verify"


# def send_sms(mobile: str, code: str, retries=3, delay=2):
#     """
#     ارسال پیامک از طریق SMS.ir با لاگ‌گیری کامل و تلاش مجدد در صورت خطا.

#     :param mobile: شماره موبایل گیرنده
#     :param code: کد تایید
#     :param retries: تعداد تلاش‌ها در صورت خطا
#     :param delay: تاخیر اولیه بین تلاش‌ها (با رشد نمایی)
#     """
#     headers = {
#         'Content-Type': 'application/json',
#         'Accept': 'application/json',
#         'X-API-KEY': API_KEY
#     }

#     payload = {
#         "Mobile": mobile,
#         "TemplateId": TEMPLATE_ID,
#         "Parameters": [
#             {"Name": "code", "Value": str(code)}
#         ]
#     }

#     for attempt in range(1, retries + 1):
#         try:
#             logging.info(f"📨 Sending SMS (attempt {attempt}) to {mobile}...")
#             response = requests.post(
#                 URL, json=payload, headers=headers, timeout=8
#             )
#             logging.info(f"✅ HTTP {response.status_code} received from SMS.ir")

#             # اگر HTTP موفق بود، بررسی محتوای JSON
#             try:
#                 result = response.json()
#                 logging.info(f"📦 SMS.ir JSON response: {result}")

#                 if result.get("status") == 1:
#                     logging.info("🎉 پیامک با موفقیت ارسال شد.")
#                     return True
#                 else:
#                     logging.warning(f"⚠ پیامک ارسال نشد: {result.get('message')}")
#                     return False

#             except ValueError:
#                 logging.error("🚨 خطا در پردازش JSON پاسخ SMS.ir")
#                 return False

#         except requests.exceptions.RequestException as e:
#             logging.error(f"🚧 خطای ارتباط با SMS.ir: {e}")
#             if attempt < retries:
#                 logging.info(f"⏳ دوباره تلاش می‌کنیم در {delay} ثانیه...")
#                 time.sleep(delay)
#                 delay *= 2
#             else:
#                 logging.error("❌ تمام تلاش‌ها برای ارسال SMS شکست خورد.")
#                 return False

#     return False
