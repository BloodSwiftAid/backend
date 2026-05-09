from rest_framework import serializers
from ..models import Payout

class PayoutSerializer(serializers.ModelSerializer):
    blood_bank_name = serializers.SerializerMethodField()
    bank_detail_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Payout
        fields = '__all__'

    def get_blood_bank_name(self, obj):
        return obj.blood_bank.name if obj.blood_bank else "Platform Admin"

    def get_bank_detail_details(self, obj):
        if obj.bank_detail:
            return {
                "bank_name": obj.bank_detail.bank_name,
                "account_number": obj.bank_detail.account_number,
                "account_name": obj.bank_detail.account_name
            }
        return None
