from rest_framework import serializers
from ..models import User, Hospital, BloodBank, UserProfile, GlobalConfig

class HospitalSerializer(serializers.ModelSerializer):
    staff = serializers.SerializerMethodField()

    class Meta:
        model = Hospital
        fields = '__all__'

    def get_staff(self, obj):
        profiles = UserProfile.objects.filter(hospital=obj)
        users = [profile.user for profile in profiles]
        return UserSerializer(users, many=True).data

class BloodBankSerializer(serializers.ModelSerializer):
    staff = serializers.SerializerMethodField()

    class Meta:
        model = BloodBank
        fields = '__all__'

    def get_staff(self, obj):
        # Get all users who have a profile linked to this blood bank
        profiles = UserProfile.objects.filter(blood_bank=obj)
        users = [profile.user for profile in profiles]
        return UserSerializer(users, many=True).data

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'first_name', 'last_name', 'role', 'phone', 'is_verified', 'must_change_password')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        # Set must_change_password to True for new onboarded users
        validated_data['must_change_password'] = True
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        request = self.context.get('request')
        
        # If self-updating, we can assume setup is being done
        if request and request.user == instance:
            if password or validated_data:
                instance.must_change_password = False
        
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='user', write_only=True)
    hospital_id = serializers.PrimaryKeyRelatedField(queryset=Hospital.objects.all(), source='hospital', write_only=True, required=False, allow_null=True)
    blood_bank_id = serializers.PrimaryKeyRelatedField(queryset=BloodBank.objects.all(), source='blood_bank', write_only=True, required=False, allow_null=True)
    
    user = UserSerializer(read_only=True)
    hospital = HospitalSerializer(read_only=True)
    blood_bank = BloodBankSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ('id', 'user', 'hospital', 'blood_bank', 'user_id', 'hospital_id', 'blood_bank_id')

class GlobalConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalConfig
        fields = '__all__'
