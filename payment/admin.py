from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'blood_request', 'user', 'amount', 'status', 'method', 'date_created')
    list_filter = ('status', 'method', 'date_created')
    search_fields = ('transaction_reference', 'user__username', 'blood_request__id')
    list_editable = ('status',)
    readonly_fields = ('transaction_reference',)
    ordering = ('-date_created',)
