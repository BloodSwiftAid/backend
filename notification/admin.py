from django.contrib import admin
from django.utils.html import format_html
from .models import Notification


# ─────────────────────────────────────────────
#  NOTIFICATION
# ─────────────────────────────────────────────
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'notification_type', 'subject',
        'status_badge', 'sent_at', 'created_by', 'date_created',
    )
    list_filter = ('notification_type', 'status', 'date_created')
    search_fields = ('user__username', 'user__email', 'subject', 'message')
    readonly_fields = ('sent_at', 'created_by', 'date_created')
    ordering = ('-date_created',)

    fieldsets = (
        ('Recipient', {
            'fields': ('user',),
        }),
        ('Content', {
            'fields': ('notification_type', 'subject', 'message'),
        }),
        ('Delivery', {
            'fields': ('status', 'sent_at'),
        }),
        ('Audit', {
            'fields': ('created_by', 'date_created'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {'SENT': 'green', 'PENDING': '#e67e22', 'FAILED': 'red'}
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="color:{};font-weight:bold;">{}</span>',
            color, obj.get_status_display()
        )

    @admin.action(description='🔄 Retry failed notifications (mark as PENDING)')
    def retry_notifications(self, request, queryset):
        updated = queryset.filter(status='FAILED').update(status='PENDING')
        self.message_user(request, f'{updated} notification(s) reset to PENDING for retry.')

    actions = [retry_notifications]
