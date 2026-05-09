from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.views import TokenObtainPairView
from ..serializers.auth_serializers import (
    RequestOTPSerializer, 
    ResetPasswordSerializer, 
    ChangePasswordSerializer,
    MyTokenObtainPairSerializer
)

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
from ..services.otp_service import create_user_otp, verify_otp

User = get_user_model()

class RequestPasswordResetOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(request=RequestOTPSerializer, tags=['Auth'])
    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = User.objects.filter(email=email).first()
        if user:
            otp_obj = create_user_otp(user, purpose='PASSWORD_RESET')
            
            # Send templated email
            from core.mail import send_templated_email
            from django.conf import settings
            
            send_templated_email(
                recipient=user.email,
                subject="Password Reset - SwiftAid Authorization Code",
                template_name="forgot_password.html",
                context={
                    "reset_code": otp_obj.otp
                }
            )
            
            return Response({"message": "OTP sent to your email."}, status=status.HTTP_200_OK)
        
        from rest_framework.exceptions import NotFound
        raise NotFound("User with this email does not exist.")

class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(request=ResetPasswordSerializer, tags=['Auth'])
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        new_password = serializer.validated_data['new_password']
        
        user = User.objects.filter(email=email).first()
        if user and verify_otp(user, otp, purpose='PASSWORD_RESET'):
            user.set_password(new_password)
            user.save()
            return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)
        
        from rest_framework.exceptions import ValidationError
        raise ValidationError("Invalid or expired OTP.")

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(request=ChangePasswordSerializer, tags=['Auth'])
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        if user.check_password(serializer.validated_data['old_password']):
            user.set_password(serializer.validated_data['new_password'])
            user.must_change_password = False
            user.save()
            return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)
        
        from rest_framework.exceptions import ValidationError
        raise ValidationError("Incorrect old password.")

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(tags=['Auth'])
    def post(self, request):
        # In a real JWT app, you might blacklist the token here
        return Response({"message": "Logout successful."}, status=status.HTTP_200_OK)
