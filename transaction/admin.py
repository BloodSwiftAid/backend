from django.contrib import admin
from django.utils.html import format_html
from .models import BloodRequest


# ─────────────────────────────────────────────
#  BLOOD REQUEST
# ─────────────────────────────────────────────
@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'batch_id', 'get_requester', 'blood_bank',
        'product', 'quantity', 'status', 'source',
        'total_amount', 'created_by', 'date_created',
    )
    list_filter = ('status', 'source', 'blood_bank', 'date_created')
    search_fields = (
        'batch_id',
        'requester_hospital__name',
        'requester_user__username',
        'requester_user__email',
        'blood_bank__name',
        'product__blood_group',
        'patient_name',
    )
    list_editable = ('status',)
    ordering = ('-date_created',)
    readonly_fields = (
        'blood_price', 'service_fee', 'delivery_fee',
        'commission_amount', 'total_amount',
        'created_by', 'date_created',
    )

    fieldsets = (
        ('Batch', {
            'fields': ('batch_id', 'source'),
            'description': 'Marketplace orders from the same session share a batch_id.',
        }),
        ('Parties', {
            'fields': ('requester_user', 'requester_hospital', 'blood_bank'),
        }),
        ('Product', {
            'fields': ('product', 'quantity'),
        }),
        ('Patient Info', {
            'fields': ('patient_name', 'patient_details', 'hospital_location'),
        }),
        ('Status', {
            'fields': ('status',),
        }),
        ('Financials', {
            'fields': ('blood_price', 'service_fee', 'delivery_fee', 'commission_amount', 'total_amount'),
        }),
        ('Logistics', {
            'fields': ('pickup_location', 'delivery_location', 'dispatch_rider'),
        }),
        ('Audit', {
            'fields': ('created_by', 'date_created'),
            'classes': ('collapse',),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    @admin.display(description='Requester')
    def get_requester(self, obj):
        if obj.requester_hospital:
            return format_html('🏥 {}', obj.requester_hospital.name)
        if obj.requester_user:
            return format_html('👤 {}', obj.requester_user.username)
        return '—'

    @admin.action(description='✅ Approve selected requests')
    def approve_requests(self, request, queryset):
        updated = queryset.filter(status='PENDING').update(status='APPROVED')
        self.message_user(request, f'{updated} request(s) approved.')

    @admin.action(description='❌ Cancel selected requests')
    def cancel_requests(self, request, queryset):
        updated = queryset.exclude(status__in=['DELIVERED', 'CANCELLED']).update(status='CANCELLED')
        self.message_user(request, f'{updated} request(s) cancelled.')

    actions = [approve_requests, cancel_requests]
