import requests


API_KEY = 'L40UGRICQDvHN3F93OuDafT0xiom3okCphDgtrAfYjpng77f9ZzNaahQGyp9wI5b'
TEMPLATE_ID = 312572
URL = "https://api.sms.ir/v1/send/verify"


def send_sms(mobile, code):
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-API-KEY': API_KEY
    }

    data = {
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
        response = requests.post(URL, json=data, headers=headers)
        print("HTTP status code:", response.status_code)

        if response.status_code != 200:
            print("ارسال ناموفق - کد وضعیت:", response.status_code)
            return False

        result = response.json()
        print("SMS.ir response JSON:", result)

        if result.get("status") == 1:
            print("✅ پیامک با موفقیت ارسال شد.")
            return True
        else:
            print("❌ پیامک ارسال نشد:", result.get("message"))
            return False

    except Exception as e:
        print("⚠️ خطا در ارسال پیامک:", str(e))
        return False
