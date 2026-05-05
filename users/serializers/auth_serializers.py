from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        login_id = attrs.get("username")
        password = attrs.get("password")

        # Try standard authentication (username)
        user = authenticate(username=login_id, password=password)
        
        if not user:
            # Try email authentication
            User = get_user_model()
            try:
                user_obj = User.objects.get(email=login_id)
                user = authenticate(username=user_obj.username, password=password)
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                user = None

        if user:
            if not user.is_active:
                raise serializers.ValidationError("User is inactive.")
            
            # SimpleJWT's super().validate expects the credentials in attrs to work with authenticate()
            # Since we already authenticated, we can manually set the user
            self.user = user
            data = {}
            refresh = self.get_token(user)
            data["refresh"] = str(refresh)
            data["access"] = str(refresh.access_token)
            
            data['role'] = user.role
            data['username'] = user.username
            data['email'] = user.email
            data['must_change_password'] = user.must_change_password
            return data
        
        raise serializers.ValidationError("No active account found with the given credentials")

class RequestOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)
    
    def validate_new_password(self, value):
        validate_password(value)
        return value

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    
    def validate_new_password(self, value):
        validate_password(value)
        return value
