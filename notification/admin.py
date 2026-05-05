from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'subject', 'status', 'date_created', 'sent_at')
    list_filter = ('notification_type', 'status', 'date_created')
    search_fields = ('user__username', 'subject', 'message')
    readonly_fields = ('sent_at',)
    ordering = ('-date_created',)
