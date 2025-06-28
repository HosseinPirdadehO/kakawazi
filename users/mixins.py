from rest_framework.response import Response
from rest_framework import status
from .serializers import FullUserProfileSerializer


class StandardResponseMixin:
    def success_response(self, message="عملیات با موفقیت انجام شد.", data=None,
                         status_code=status.HTTP_200_OK, user=None):
        response_data = {
            "success": True,
            "message": message,
            "data": data,
        }

        if user:
            user_data = FullUserProfileSerializer(user).data
            response_data["user"] = user_data

        return Response(response_data, status=status_code)

    def error_response(self, message="خطایی رخ داده است.", data=None,
                       status_code=status.HTTP_400_BAD_REQUEST):
        return Response({
            "success": False,
            "message": message,
            "data": data
        }, status=status_code)
