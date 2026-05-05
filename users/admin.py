from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Hospital, BloodBank, UserProfile

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'is_verified', 'is_staff', 'date_created')
    list_filter = ('role', 'is_verified', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_created',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('SwiftAid Profile', {'fields': ('role', 'phone', 'is_verified')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('SwiftAid Profile', {'fields': ('role', 'phone', 'is_verified')}),
    )

@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('name', 'hospital_type', 'state', 'lga', 'has_emergency_unit', 'is_verified', 'date_created')
    list_filter = ('hospital_type', 'state', 'has_emergency_unit', 'is_verified')
    search_fields = ('name', 'contact_email', 'contact_phone', 'address')
    list_editable = ('is_verified',)
    ordering = ('-date_created',)

@admin.register(BloodBank)
class BloodBankAdmin(admin.ModelAdmin):
    list_display = ('name', 'license_number', 'state', 'lga', 'storage_capacity_liters', 'is_verified', 'date_created')
    list_filter = ('state', 'is_verified')
    search_fields = ('name', 'license_number', 'contact_email', 'contact_phone', 'address')
    list_editable = ('is_verified',)
    ordering = ('-date_created',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_organization', 'date_created')
    search_fields = ('user__username', 'hospital__name', 'blood_bank__name')
    list_filter = ('hospital__state', 'blood_bank__state')

    def get_organization(self, obj):
        if obj.hospital:
            return f"Hospital: {obj.hospital.name}"
        if obj.blood_bank:
            return f"Blood Bank: {obj.blood_bank.name}"
        return "No Organization"
    get_organization.short_description = 'Organization'
