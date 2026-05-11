from rest_framework import serializers
from ..models import BloodRequest

from users.serializers.user_serializers import HospitalSerializer, BloodBankSerializer
from payment.serializers.payment_serializers import PaymentSerializer

class BloodRequestSerializer(serializers.ModelSerializer):
    blood_group = serializers.ReadOnlyField(source='product.blood_group')
    requester_name = serializers.SerializerMethodField()
    requester_hospital_details = HospitalSerializer(source='requester_hospital', read_only=True)
    blood_bank_details = BloodBankSerializer(source='blood_bank', read_only=True)
    payment = PaymentSerializer(read_only=True)
    
    class Meta:
        model = BloodRequest
        fields = '__all__'

    def create(self, validated_data):
        from inventory.models import Inventory, Product, BloodType
        
        product = validated_data.get('product')
        blood_type_id = self.initial_data.get('blood_type')
        
        # If product is missing (e.g. from marketplace), resolve it from blood_type
        if not product and blood_type_id:
            bt_obj = BloodType.objects.filter(id=blood_type_id).first()
            if bt_obj:
                product = Product.objects.filter(blood_group=bt_obj.group).first()
                validated_data['product'] = product

        if not product:
            raise serializers.ValidationError({"product": "A valid product or blood type is required."})

        blood_bank = validated_data.get('blood_bank')
        quantity = validated_data.get('quantity', 1)
        
        # Get commission from global config or blood bank
        from users.models import GlobalConfig
        config = GlobalConfig.objects.first()
        commission_pct = float(config.commission_percentage) if config else 10.0
        
        if blood_bank and not config:
            commission_pct = float(blood_bank.commission_percentage)
            
        # Get official base price from Biological Registry (Internal Admin Control)
        bt = BloodType.objects.filter(group=product.blood_group).first()
        official_base_price = float(bt.base_price) if bt else 0.0
        
        # Calculations (Marketplace ignores facility-set POS price for public listings)
        blood_price = official_base_price * quantity
        commission_amount = blood_price * (commission_pct / 100.0)
        total_amount = blood_price + commission_amount + float(validated_data.get('service_fee', 0)) + float(validated_data.get('delivery_fee', 0))
        
        validated_data['blood_price'] = blood_price
        validated_data['commission_amount'] = commission_amount
        validated_data['total_amount'] = total_amount
        
        return super().create(validated_data)

    def get_requester_name(self, obj):
        if obj.requester_hospital:
            return obj.requester_hospital.name
        if obj.requester_user:
            return f"{obj.requester_user.first_name} {obj.requester_user.last_name}"
        return "Direct Sale"
