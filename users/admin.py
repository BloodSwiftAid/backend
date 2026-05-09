from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, Hospital, BloodBank, UserProfile, UserOTP, GlobalConfig, VerificationLog


# ─────────────────────────────────────────────
#  USER
# ─────────────────────────────────────────────
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username', 'email', 'full_name', 'role',
        'is_verified_badge', 'must_change_password', 'is_active',
        'created_by', 'date_created',
    )
    list_filter = ('role', 'is_verified', 'must_change_password', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_created',)
    readonly_fields = ('created_by', 'date_created', 'last_login', 'date_joined')

    fieldsets = BaseUserAdmin.fieldsets + (
        ('SwiftAid Profile', {
            'fields': ('role', 'phone', 'is_verified', 'must_change_password'),
        }),
        ('Audit', {
            'fields': ('created_by', 'date_created'),
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('SwiftAid Profile', {
            'fields': ('role', 'phone', 'is_verified', 'must_change_password'),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    @admin.display(description='Full Name')
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or '—'

    @admin.display(description='Verified', boolean=False)
    def is_verified_badge(self, obj):
        if obj.is_verified:
            return format_html('<span style="color:{};font-weight:bold;">{}</span>', 'green', '✔ Verified')
        return format_html('<span style="color:{}">{}</span>', '#e67e22', '⚠ Unverified')

    @admin.action(description='✔ Mark selected users as verified')
    def verify_users(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} user(s) marked as verified.')

    @admin.action(description='✘ Mark selected users as unverified')
    def unverify_users(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'{updated} user(s) marked as unverified.')

    @admin.action(description='🔑 Force password change on next login')
    def force_password_change(self, request, queryset):
        updated = queryset.update(must_change_password=True)
        self.message_user(request, f'{updated} user(s) will be forced to change password on next login.')

    actions = [verify_users, unverify_users, force_password_change]


# ─────────────────────────────────────────────
#  FACILITY BASE ADMIN (shared actions)
# ─────────────────────────────────────────────
class BaseFacilityAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    @admin.action(description='✅ Verify selected facilities')
    def verify_facility(self, request, queryset):
        for obj in queryset:
            obj.is_verified = True
            obj.save()
            VerificationLog.objects.create(
                admin=request.user,
                hospital=obj if isinstance(obj, Hospital) else None,
                blood_bank=obj if isinstance(obj, BloodBank) else None,
                action='VERIFIED',
            )
        self.message_user(request, f'{queryset.count()} facility(ies) verified.')

    @admin.action(description='❌ Unverify selected facilities')
    def unverify_facility(self, request, queryset):
        for obj in queryset:
            obj.is_verified = False
            obj.save()
            VerificationLog.objects.create(
                admin=request.user,
                hospital=obj if isinstance(obj, Hospital) else None,
                blood_bank=obj if isinstance(obj, BloodBank) else None,
                action='UNVERIFIED',
            )
        self.message_user(request, f'{queryset.count()} facility(ies) unverified.')

    @admin.action(description='🚀 Activate selected facilities')
    def activate_facility(self, request, queryset):
        for obj in queryset:
            obj.is_active = True
            obj.save()
            VerificationLog.objects.create(
                admin=request.user,
                hospital=obj if isinstance(obj, Hospital) else None,
                blood_bank=obj if isinstance(obj, BloodBank) else None,
                action='ACTIVATED',
            )
        self.message_user(request, f'{queryset.count()} facility(ies) activated.')

    @admin.action(description='⛔ Deactivate selected facilities')
    def deactivate_facility(self, request, queryset):
        for obj in queryset:
            obj.is_active = False
            obj.save()
            VerificationLog.objects.create(
                admin=request.user,
                hospital=obj if isinstance(obj, Hospital) else None,
                blood_bank=obj if isinstance(obj, BloodBank) else None,
                action='DEACTIVATED',
            )
        self.message_user(request, f'{queryset.count()} facility(ies) deactivated.')

    actions = [verify_facility, unverify_facility, activate_facility, deactivate_facility]


# ─────────────────────────────────────────────
#  HOSPITAL
# ─────────────────────────────────────────────
@admin.register(Hospital)
class HospitalAdmin(BaseFacilityAdmin):
    list_display = (
        'name', 'hospital_type', 'state', 'area',
        'has_emergency_unit', 'is_verified', 'is_active',
        'created_by', 'date_created',
    )
    list_filter = ('hospital_type', 'state', 'has_emergency_unit', 'is_verified', 'is_active')
    search_fields = ('name', 'contact_email', 'contact_phone', 'address', 'state', 'area')
    list_editable = ('is_verified', 'is_active')
    ordering = ('-date_created',)
    readonly_fields = ('created_by', 'date_created')

    fieldsets = (
        ('Identity', {
            'fields': ('name', 'hospital_type', 'has_emergency_unit'),
        }),
        ('Location', {
            'fields': ('country', 'state', 'area', 'street', 'address', 'latitude', 'longitude'),
        }),
        ('Contact & KYC', {
            'fields': ('contact_email', 'contact_phone', 'kyc_document'),
        }),
        ('Status', {
            'fields': ('is_verified', 'is_active'),
        }),
        ('Audit', {
            'fields': ('created_by', 'date_created'),
            'classes': ('collapse',),
        }),
    )


# ─────────────────────────────────────────────
#  BLOOD BANK
# ─────────────────────────────────────────────
@admin.register(BloodBank)
class BloodBankAdmin(BaseFacilityAdmin):
    list_display = (
        'name', 'license_number', 'state', 'area',
        'storage_capacity_liters', 'commission_percentage',
        'wallet_balance', 'is_verified', 'is_active',
        'created_by', 'date_created',
    )
    list_filter = ('state', 'is_verified', 'is_active')
    search_fields = ('name', 'license_number', 'contact_email', 'contact_phone', 'address', 'state')
    list_editable = ('is_verified', 'is_active')
    ordering = ('-date_created',)
    readonly_fields = ('created_by', 'date_created', 'wallet_balance')

    fieldsets = (
        ('Identity', {
            'fields': ('name', 'license_number'),
        }),
        ('Location', {
            'fields': ('country', 'state', 'area', 'street', 'address', 'latitude', 'longitude'),
        }),
        ('Contact & KYC', {
            'fields': ('contact_email', 'contact_phone', 'kyc_document'),
        }),
        ('Financial', {
            'fields': ('storage_capacity_liters', 'commission_percentage', 'wallet_balance'),
        }),
        ('Status', {
            'fields': ('is_verified', 'is_active'),
        }),
        ('Audit', {
            'fields': ('created_by', 'date_created'),
            'classes': ('collapse',),
        }),
    )


# ─────────────────────────────────────────────
#  USER PROFILE
# ─────────────────────────────────────────────
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_role', 'get_organization', 'created_by', 'date_created')
    search_fields = ('user__username', 'user__email', 'hospital__name', 'blood_bank__name')
    list_filter = ('hospital__state', 'blood_bank__state')
    readonly_fields = ('created_by', 'date_created')
    raw_id_fields = ('user', 'hospital', 'blood_bank')

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    @admin.display(description='Role')
    def get_role(self, obj):
        return obj.user.get_role_display() if obj.user else '—'

    @admin.display(description='Organization')
    def get_organization(self, obj):
        if obj.hospital:
            return format_html('<span style="color:{}">{} {}</span>', '#2980b9', '🏥', obj.hospital.name)
        if obj.blood_bank:
            return format_html('<span style="color:{}">{} {}</span>', '#e74c3c', '🩸', obj.blood_bank.name)
        return '—'


# ─────────────────────────────────────────────
#  USER OTP
# ─────────────────────────────────────────────
@admin.register(UserOTP)
class UserOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp', 'purpose', 'is_used', 'expiry', 'date_created')
    list_filter = ('purpose', 'is_used', 'date_created')
    search_fields = ('user__username', 'user__email', 'otp')
    readonly_fields = ('date_created',)
    ordering = ('-date_created',)


# ─────────────────────────────────────────────
#  GLOBAL CONFIG
# ─────────────────────────────────────────────
@admin.register(GlobalConfig)
class GlobalConfigAdmin(admin.ModelAdmin):
    list_display = (
        'commission_percentage', 'allowed_free_payouts',
        'payout_charge_fee', 'wallet_balance', 'last_modified',
    )
    readonly_fields = ('wallet_balance', 'last_modified', 'created_by')

    fieldsets = (
        ('Commission & Payouts', {
            'fields': ('commission_percentage', 'allowed_free_payouts', 'payout_charge_fee'),
        }),
        ('Platform Wallet', {
            'fields': ('wallet_balance',),
        }),
        ('Contact Info', {
            'fields': ('address', 'contact_email', 'contact_phone'),
        }),
        ('Audit', {
            'fields': ('created_by', 'last_modified'),
            'classes': ('collapse',),
        }),
    )

    def has_add_permission(self, request):
        return not GlobalConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# ─────────────────────────────────────────────
#  VERIFICATION LOG
# ─────────────────────────────────────────────
@admin.register(VerificationLog)
class VerificationLogAdmin(admin.ModelAdmin):
    list_display = ('admin', 'get_target', 'action', 'date_created')
    list_filter = ('action', 'date_created')
    search_fields = ('admin__username', 'hospital__name', 'blood_bank__name')
    readonly_fields = ('admin', 'hospital', 'blood_bank', 'action', 'notes', 'created_by', 'date_created')
    ordering = ('-date_created',)

    @admin.display(description='Target Facility')
    def get_target(self, obj):
        target = obj.hospital or obj.blood_bank
        if target:
            icon = '🏥' if obj.hospital else '🩸'
            return format_html('{} {}', icon, target.name)
        return '—'

    def has_add_permission(self, request):
        return False
