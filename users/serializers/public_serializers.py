from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import Hospital, BloodBank, PotentialDonor, UserProfile
from django.db import transaction

User = get_user_model()

class FacilityRegistrationSerializer(serializers.Serializer):
    facility_type = serializers.ChoiceField(choices=['hospital', 'bloodbank'])
    facility_name = serializers.CharField(max_length=255)
    
    # Bloodbank specific
    license_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    logistics_status = serializers.CharField(required=False, allow_blank=True)
    
    # Hospital specific
    hospital_type = serializers.CharField(max_length=100, required=False, allow_blank=True)
    has_emergency_unit = serializers.BooleanField(default=False)
    
    # Admin / Contact Details
    admin_name = serializers.CharField(max_length=255)
    admin_email = serializers.EmailField()
    admin_phone = serializers.CharField(max_length=20)
    
    # Address Details
    operational_address = serializers.CharField(required=True, allow_blank=False)
    country = serializers.CharField(default='Nigeria', allow_blank=False)
    state = serializers.CharField(max_length=100, required=True, allow_blank=False)
    lga = serializers.CharField(max_length=100, required=True, allow_blank=False)
    city = serializers.CharField(max_length=100)

    def validate_admin_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs):
        facility_type = attrs.get('facility_type')
        if facility_type == 'bloodbank':
            if not attrs.get('license_number') or attrs.get('license_number').strip() == '':
                raise serializers.ValidationError({"license_number": "License number is required for Blood Banks."})
        
        # Ensure mandatory fields are present
        required_fields = ['state', 'lga', 'country', 'admin_name', 'admin_email', 'admin_phone', 'operational_address', 'facility_name']
        for field in required_fields:
            if not attrs.get(field):
                raise serializers.ValidationError({field: f"{field.replace('_', ' ').title()} is strictly required."})
        
        return attrs

    def create(self, validated_data):
        facility_type = validated_data.pop('facility_type')
        admin_name = validated_data.pop('admin_name')
        admin_email = validated_data.pop('admin_email')
        admin_phone = validated_data.pop('admin_phone')
        
        with transaction.atomic():
            # 1. Create the admin user
            # Provide a dummy password or set an unusable one since it's unverified
            user = User(
                username=admin_email,
                email=admin_email,
                first_name=admin_name.split()[0] if admin_name else '',
                last_name=' '.join(admin_name.split()[1:]) if len(admin_name.split()) > 1 else '',
                phone=admin_phone,
                role='HOSPITAL_ADMIN' if facility_type == 'hospital' else 'BLOODBANK_ADMIN',
                is_verified=False
            )
            user.set_unusable_password()
            user.save()

            # 2. Create the facility
            common_facility_data = {
                'name': validated_data.get('facility_name'),
                'address': validated_data.get('operational_address'),
                'country': validated_data.get('country'),
                'state': validated_data.get('state'),
                'area': validated_data.get('lga'),
                'city': validated_data.get('city'),
                'contact_email': admin_email,
                'contact_phone': admin_phone,
                'is_verified': False,
                'is_active': False
            }

            if facility_type == 'hospital':
                facility = Hospital.objects.create(
                    **common_facility_data,
                    hospital_type=validated_data.get('hospital_type', 'General'),
                    has_emergency_unit=validated_data.get('has_emergency_unit', False)
                )
                # 3. Link user to facility
                UserProfile.objects.create(user=user, hospital=facility)
            else:
                facility = BloodBank.objects.create(
                    **common_facility_data,
                    license_number=validated_data.get('license_number', ''),
                    logistics_status=validated_data.get('logistics_status', '')
                )
                UserProfile.objects.create(user=user, blood_bank=facility)

        return facility


class PotentialDonorSerializer(serializers.ModelSerializer):
    class Meta:
        model = PotentialDonor
        fields = [
            'full_name', 'email', 'phone', 'blood_group', 
            'address', 'country', 'state', 'city', 'lga'
        ]
