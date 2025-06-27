from rest_framework.response import Response
from rest_framework import status
from .models import User


class StandardResponseMixin:
    def success_response(self, message="عملیات با موفقیت انجام شد.", data=None,
                         status_code=status.HTTP_200_OK, user=None, include_roles=True):
        response_data = {
            "success": True,
            "message": message,
            "data": data,
        }

        if user and hasattr(user, 'system_role'):
            response_data["role"] = user.system_role

        if include_roles:
            response_data["roles"] = self.get_roles_data()

        return Response(response_data, status=status_code)

    def error_response(self, message="خطایی رخ داده است.", data=None,
                       status_code=status.HTTP_400_BAD_REQUEST):
        return Response({
            "success": False,
            "message": message,
            "data": data
        }, status=status_code)

    def get_roles_data(self):
        return {
            "system_roles": [
                {"value": role.value, "label": role.label}
                for role in User.SystemRole
            ],
            "job_roles": [
                {"value": value, "label": label}
                for value, label in User.JOB_ROLE_CHOICES
            ],
            "vehicle_types": [
                {"value": value, "label": label}
                for value, label in User.TYPE_OF_CAR_CHOICES
            ],
            "status_options": [
                {"value": value, "label": label}
                for value, label in User.STATUS_CHOICES
            ]
        }
