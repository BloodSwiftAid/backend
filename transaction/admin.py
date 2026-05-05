from django.contrib import admin
from .models import BloodRequest

@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_requester', 'blood_bank', 'product', 'quantity', 'status', 'total_amount', 'date_created')
    list_filter = ('status', 'source', 'blood_bank', 'date_created')
    search_fields = ('requester_hospital__name', 'blood_bank__name', 'product__blood_group')
    list_editable = ('status',)
    
    fieldsets = (
        ('Parties Involved', {
            'fields': (('requester_user', 'requester_hospital'), 'blood_bank')
        }),
        ('Request Details', {
            'fields': ('product', 'quantity', 'status', 'source')
        }),
        ('Financials', {
            'fields': ('blood_price', 'service_fee', 'delivery_fee', 'total_amount')
        }),
        ('Logistics', {
            'fields': ('pickup_location', 'delivery_location', 'dispatch_rider')
        }),
    )

    def get_requester(self, obj):
        return obj.requester_hospital.name if obj.requester_hospital else obj.requester_user.username
    get_requester.short_description = 'Requester'
