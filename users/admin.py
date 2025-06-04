from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, PhoneOTP, Referral
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ['phone_number']
    list_display = (
        'phone_number', 'get_full_name', 'role', 'type_of_car', 'plate_number',
        'is_phone_verified', 'is_active', 'is_staff', 'date_joined', 'status'
    )
    list_filter = ('is_staff', 'is_active', 'status', 'role', 'type_of_car')
    search_fields = (
        'phone_number', 'first_name', 'last_name', 'email',
        'referral_code', 'national_code', 'plate_number'
    )
    readonly_fields = ('date_joined', 'last_login',
                       'user_uuid', 'referral_code')

    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        (_('Personal info'), {
            'fields': (
                'first_name', 'last_name', 'email', 'birth_date',
                'city', 'state', 'national_code', 'image',
                'role', 'type_of_car', 'plate_number'
            )
        }),
        (_('Permissions'), {'fields': ('is_active', 'is_staff',
         'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Additional info'), {
            'fields': ('status', 'is_phone_verified', 'referral_code', 'user_uuid')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'password1', 'password2', 'role', 'type_of_car', 'plate_number'),
        }),
    )

    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'نام کامل'


@admin.register(PhoneOTP)
class PhoneOTPAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'code', 'purpose',
                    'is_verified', 'created_at', 'is_expired')
    list_filter = ('purpose', 'is_verified', 'created_at')
    search_fields = ('phone_number', 'code')
    readonly_fields = ('created_at',)

    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = 'منقضی شده؟'


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ('inviter', 'invited', 'created_at')
    list_filter = ('created_at', 'invited')
    search_fields = (
        'inviter__phone_number',
        'inviter__first_name',
        'inviter__last_name',
        'invited__phone_number',
        'invited__first_name',
        'invited__last_name',
    )
    readonly_fields = ('created_at',)
