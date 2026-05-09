from django.contrib import admin
from django.utils.html import format_html
from .models import Payment, BankDetail, Payout


# ─────────────────────────────────────────────
#  PAYMENT
# ─────────────────────────────────────────────
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'transaction_reference', 'get_requester', 'blood_request',
        'amount', 'service_fee', 'blood_bank_fee', 'gateway_fee',
        'status', 'method', 'created_by', 'date_created',
    )
    list_filter = ('status', 'method', 'date_created')
    search_fields = (
        'transaction_reference', 'user__username', 'user__email',
        'blood_request__id', 'blood_request__batch_id',
    )
    list_editable = ('status',)
    readonly_fields = (
        'transaction_reference', 'commission_percentage',
        'service_fee', 'blood_bank_fee', 'gateway_fee',
        'created_by', 'date_created',
    )
    ordering = ('-date_created',)

    fieldsets = (
        ('Transaction Identity', {
            'fields': ('transaction_reference', 'blood_request', 'user'),
        }),
        ('Financials', {
            'fields': ('amount', 'commission_percentage', 'service_fee', 'blood_bank_fee', 'gateway_fee'),
            'description': 'Gateway fee is borne by the merchant (payer). Blood bank fee is net after platform commission.',
        }),
        ('Status', {
            'fields': ('status', 'method'),
        }),
        ('Audit', {
            'fields': ('created_by', 'date_created'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Requester')
    def get_requester(self, obj):
        return obj.user.username if obj.user else '—'

    @admin.action(description='✅ Mark selected payments as SUCCESS')
    def mark_success(self, request, queryset):
        updated = queryset.update(status='SUCCESS')
        self.message_user(request, f'{updated} payment(s) marked as SUCCESS.')

    @admin.action(description='❌ Mark selected payments as FAILED')
    def mark_failed(self, request, queryset):
        updated = queryset.update(status='FAILED')
        self.message_user(request, f'{updated} payment(s) marked as FAILED.')

    actions = [mark_success, mark_failed]


# ─────────────────────────────────────────────
#  BANK DETAIL
# ─────────────────────────────────────────────
@admin.register(BankDetail)
class BankDetailAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'get_owner', 'bank_name', 'account_name',
        'account_number', 'bank_code', 'is_active',
        'is_internal_admin', 'created_by', 'date_created',
    )
    list_filter = ('is_active', 'is_internal_admin', 'bank_name', 'date_created')
    search_fields = ('account_number', 'account_name', 'bank_name', 'blood_bank__name', 'recipient_code')
    list_editable = ('is_active',)
    readonly_fields = ('recipient_code', 'created_by', 'date_created')
    raw_id_fields = ('blood_bank',)
    ordering = ('-date_created',)

    fieldsets = (
        ('Owner', {
            'fields': ('blood_bank', 'is_internal_admin'),
        }),
        ('Bank Details', {
            'fields': ('bank_name', 'bank_code', 'account_number', 'account_name', 'recipient_code'),
        }),
        ('Status', {
            'fields': ('is_active',),
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

    @admin.display(description='Owner')
    def get_owner(self, obj):
        if obj.is_internal_admin:
            return format_html('<span style="color:{};font-weight:bold;">{}</span>', '#8e44ad', 'Platform Admin')
        return obj.blood_bank.name if obj.blood_bank else '—'


# ─────────────────────────────────────────────
#  PAYOUT
# ─────────────────────────────────────────────
@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'get_recipient', 'amount', 'fee', 'total_debited',
        'status', 'is_internal_admin', 'created_by',
        'date_completed', 'date_created',
    )
    list_filter = ('status', 'is_internal_admin', 'date_created', 'date_completed')
    search_fields = ('transaction_reference', 'blood_bank__name')
    readonly_fields = (
        'transaction_reference', 'total_debited',
        'date_completed', 'created_by', 'date_created',
    )
    ordering = ('-date_created',)

    fieldsets = (
        ('Recipient', {
            'fields': ('blood_bank', 'bank_detail', 'is_internal_admin'),
        }),
        ('Financials', {
            'fields': ('amount', 'fee', 'total_debited'),
        }),
        ('Status', {
            'fields': ('status', 'transaction_reference', 'date_completed'),
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

    @admin.display(description='Recipient')
    def get_recipient(self, obj):
        if obj.is_internal_admin:
            return format_html('<span style="color:{};font-weight:bold;">{}</span>', '#8e44ad', 'Platform Admin')
        return obj.blood_bank.name if obj.blood_bank else '—'

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {'SUCCESS': 'green', 'PENDING': '#e67e22', 'FAILED': 'red'}
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="color:{};font-weight:bold;">{}</span>',
            color, obj.get_status_display()
        )

    @admin.action(description='✅ Mark selected payouts as SUCCESS')
    def mark_success(self, request, queryset):
        updated = queryset.update(status='SUCCESS')
        self.message_user(request, f'{updated} payout(s) marked as SUCCESS.')

    @admin.action(description='❌ Mark selected payouts as FAILED')
    def mark_failed(self, request, queryset):
        updated = queryset.update(status='FAILED')
        self.message_user(request, f'{updated} payout(s) marked as FAILED.')

    actions = [mark_success, mark_failed]
