from rest_framework.response import Response
from rest_framework import status
from .models import User


class StandardResponseMixin:
    def success_response(self, message="عملیات با موفقیت انجام شد.", data=None,
                         status_code=status.HTTP_200_OK, user=None):
        response_data = {
            "success": True,
            "message": message,
            "data": data,
        }

        if user and hasattr(user, 'system_role'):
            response_data["role"] = user.system_role

        if user:
            response_data["selected_roles"] = {
                "system_role": getattr(user, 'system_role', None),
                "job_role": getattr(user, 'job_role', None),
                "type_of_car": getattr(user, 'type_of_car', None),
                "status": getattr(user, 'status', None),
            }

        return Response(response_data, status=status_code)

    def error_response(self, message="خطایی رخ داده است.", data=None,
                       status_code=status.HTTP_400_BAD_REQUEST):
        return Response({
            "success": False,
            "message": message,
            "data": data
        }, status=status_code)
