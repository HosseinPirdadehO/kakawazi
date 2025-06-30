from rest_framework.response import Response
from rest_framework import status


class StandardResponseMixin:
    """
    Mixin to standardize API responses
    """

    def success_response(self, data=None, message='عملیات با موفقیت انجام شد', status_code=200):
        return Response({
            'status': True,
            'message': message,
            'data': data,
            'errors': None
        }, status=status_code)

    def error_response(self, errors=None, message='خطا در انجام عملیات', status_code=400):
        return Response({
            'status': False,
            'message': message,
            'data': None,
            'errors': errors
        }, status=status_code)


class WalletResponseMixin(StandardResponseMixin):
    """
    Mixin to format wallet response with referral data
    """

    def wallet_response(self, wallet, transactions=None, message='اطلاعات کیف پول', status_code=200):
        user = wallet.user

        # دعوتی‌ها
        invited_users_qs = user.sent_referrals.select_related('invited')

        invited_users = list(
            invited_users_qs.values(
                'invited__id', 'invited__first_name', 'invited__last_name', 'invited__phone_number'
            )
        )

        invited_users_cleaned = [
            {
                'id': u['invited__id'],
                'first_name': u['invited__first_name'],
                'last_name': u['invited__last_name'],
                'phone_number': u['invited__phone_number']
            } for u in invited_users
        ]

        data = {
            'balance': wallet.balance,
            'updated_at': wallet.updated_at,
            'created_at': wallet.created_at,
            'referrals_count': invited_users_qs.count(),
            'referrals': invited_users_cleaned
        }

        if transactions is not None:
            data['transactions'] = transactions

        return self.success_response(data=data, message=message, status_code=status_code)
