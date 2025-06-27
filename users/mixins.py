from rest_framework.response import Response
from rest_framework import status


class StandardResponseMixin:
    def success_response(self, message="عملیات با موفقیت انجام شد.", data=None, status_code=status.HTTP_200_OK, user=None):
        response_data = {
            "success": True,
            "message": message,
            "data": data,
        }

        if user and hasattr(user, 'system_role'):
            response_data["role"] = user.system_role

        return Response(response_data, status=status_code)

    def error_response(self, message="خطایی رخ داده است.", data=None, status_code=status.HTTP_400_BAD_REQUEST):
        return Response({
            "success": False,
            "message": message,
            "data": data
        }, status=status_code)
