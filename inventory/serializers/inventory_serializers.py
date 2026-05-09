from rest_framework import serializers
from ..models import BloodType, ProductCategory, Product, Inventory, Donation

class BloodTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BloodType
        fields = '__all__'

class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class InventorySerializer(serializers.ModelSerializer):
    blood_group = serializers.ReadOnlyField(source='blood_type.group')
    
    class Meta:
        model = Inventory
        fields = '__all__'
        read_only_fields = ['blood_bank']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.blood_type:
            data['blood_type_details'] = BloodTypeSerializer(instance.blood_type).data
        if instance.blood_bank:
            data['commission_percentage'] = instance.blood_bank.commission_percentage
        return data

class DonationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donation
        fields = '__all__'
        read_only_fields = ['blood_bank']
