from rest_framework import serializers
from ..models import BankDetail

class BankDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankDetail
        fields = '__all__'
        read_only_fields = ['recipient_code', 'is_internal_admin', 'date_created', 'created_by']
