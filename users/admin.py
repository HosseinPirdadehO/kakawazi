from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PhoneOTP, Referral


# =================== Inline ===================
class ReferralInline(admin.TabularInline):
    model = Referral
    fk_name = 'inviter'
    extra = 0
    readonly_fields = ('invited', 'created_at')
    verbose_name = "کاربر دعوت‌شده"
    verbose_name_plural = "کاربران دعوت‌شده"


# =================== UserAdmin ===================
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [ReferralInline]

    fieldsets = (
        ("اطلاعات ورود", {
            'fields': ('phone_number', 'password', 'is_phone_verified')
        }),
        ("اطلاعات شخصی", {
            'fields': ('first_name', 'last_name', 'email', 'birth_date', 'image', 'name_school')
        }),
        ("موقعیت جغرافیایی", {
            'fields': ('state', 'city', )
        }),
        ("اطلاعات ماشین", {
            'fields': ('plate_number', 'type_of_car')
        }),
        ("نقش و وضعیت", {
            'fields': ('system_role', 'job_role', 'status', 'is_active', 'is_staff', 'is_superuser')
        }),
        ("سیستم ارجاع", {
            'fields': ('referral_code', 'referral')
        }),
        ("زمان‌ها", {
            'fields': ('created_at', 'date_joined', 'last_login')
        }),
        ("دسترسی‌ها", {
            'fields': ('groups', 'user_permissions')
        }),
    )

    add_fieldsets = (
        ("ساخت کاربر جدید", {
            'classes': ('wide',),
            'fields': (
                'phone_number',
                'password1',
                'password2',
                'system_role',
                'name_school',
                'job_role',
                'is_staff',
                'is_superuser',
                'is_active',
            ),
        }),
    )

    list_display = (
        'phone_number',
        'get_full_name',
        'system_role',
        'job_role',
        'referral_link',
        'name_school',
        'referral_count',
        'is_staff',
        'is_active',
    )

    list_filter = (
        'system_role',
        'job_role',
        'is_staff',
        'is_active',
        'status',
    )

    search_fields = (
        'phone_number',
        'first_name',
        'last_name',
        'email',
        'referral_code',
    )

    ordering = ('-created_at',)

    readonly_fields = ('created_at', 'date_joined',
                       'last_login', 'referral_code')

    def get_full_name(self, obj):
        return obj.get_full_name() or "—"
    get_full_name.short_description = 'نام کامل'

    def referral_link(self, obj):
        if obj.referral:
            return obj.referral.get_full_name() or obj.referral.phone_number
        return "-"
    referral_link.short_description = "دعوت‌کننده"

    def referral_count(self, obj):
        return obj.referrals.count()
    referral_count.short_description = "تعداد ارجاعات"


@admin.register(PhoneOTP)
class PhoneOTPAdmin(admin.ModelAdmin):
    list_display = (
        'phone_number', 'purpose', 'created_at', 'is_verified', 'failed_attempts', 'is_expired_display'
    )
    list_filter = ('purpose', 'is_verified', 'created_at')
    search_fields = ('phone_number',)
    readonly_fields = ('code', 'created_at')

    def is_expired_display(self, obj):
        return obj.is_expired()
    is_expired_display.boolean = True
    is_expired_display.short_description = "منقضی؟"


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ('inviter_name', 'invited_name', 'created_at')
    search_fields = ('inviter__phone_number', 'invited__phone_number')
    list_filter = ('created_at',)
    readonly_fields = ('inviter', 'invited', 'created_at')

    def inviter_name(self, obj):
        return obj.inviter.get_full_name() or obj.inviter.phone_number
    inviter_name.short_description = "دعوت‌کننده"

    def invited_name(self, obj):
        return obj.invited.get_full_name() or obj.invited.phone_number
    invited_name.short_description = "دعوت‌شده"
