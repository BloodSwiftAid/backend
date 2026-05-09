from rest_framework import viewsets, permissions as drf_permissions
from ..models import User, Hospital, BloodBank, UserProfile, GlobalConfig
from ..serializers.user_serializers import (
    UserSerializer, 
    HospitalSerializer, 
    BloodBankSerializer, 
    UserProfileSerializer,
    GlobalConfigSerializer
)
from rest_framework.views import APIView

class GlobalConfigView(APIView):
    permission_classes = [drf_permissions.IsAuthenticated]

    def get(self, request):
        config = GlobalConfig.objects.first()
        if not config:
            # Create default if not exists
            config = GlobalConfig.objects.create(commission_percentage=10.0)
        serializer = GlobalConfigSerializer(config)
        return Response(serializer.data)

    def post(self, request):
        if request.user.role != 'INTERNAL_ADMIN':
            return Response({"error": "Unauthorized"}, status=403)
        
        config = GlobalConfig.objects.first()
        serializer = GlobalConfigSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

class MeView(APIView):
    permission_classes = [drf_permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
from ..permissions import IsInternalAdmin
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction

from drf_spectacular.utils import extend_schema, extend_schema_view

@extend_schema_view(
    list=extend_schema(tags=['Users']),
    retrieve=extend_schema(tags=['Users']),
)
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [drf_permissions.IsAuthenticated, IsInternalAdmin]

    def perform_create(self, serializer):
        raw_password = self.request.data.get('password')
        user = serializer.save()
        
        # If internal admin creates a facility admin, send onboarding email
        if user.role in ['BLOODBANK_ADMIN', 'HOSPITAL_ADMIN']:
            from core.mail import send_templated_email
            from django.conf import settings
            
            send_templated_email(
                recipient=user.email,
                subject="Welcome to the Network - SwiftAid Onboarding",
                template_name="onboarding.html",
                context={
                    "email": user.email,
                    "temporary_password": raw_password or "Set during onboarding",
                    "portal_url": settings.FRONTEND_BASE_URL
                }
            )

@extend_schema_view(
    list=extend_schema(tags=['Hospitals']),
    retrieve=extend_schema(tags=['Hospitals']),
)
class HospitalViewSet(viewsets.ModelViewSet):
    queryset = Hospital.objects.all()
    serializer_class = HospitalSerializer
    permission_classes = [drf_permissions.IsAuthenticated, IsInternalAdmin]

@extend_schema_view(
    list=extend_schema(tags=['Blood Banks']),
    retrieve=extend_schema(tags=['Blood Banks']),
)
class BloodBankViewSet(viewsets.ModelViewSet):
    queryset = BloodBank.objects.all()
    serializer_class = BloodBankSerializer
    permission_classes = [drf_permissions.IsAuthenticated, IsInternalAdmin]

@extend_schema_view(
    list=extend_schema(tags=['Profiles']),
    retrieve=extend_schema(tags=['Profiles']),
)
class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [drf_permissions.IsAuthenticated, IsInternalAdmin]

class StaffManagementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for BLOODBANK_ADMIN and HOSPITAL_ADMIN to manage their own staff.
    """
    serializer_class = UserSerializer
    permission_classes = [drf_permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        profile = getattr(user, 'profile', None)
        if not profile:
            return User.objects.none()
        
        if user.role == 'BLOODBANK_ADMIN' and profile.blood_bank:
            # Get all users whose profile points to the same blood bank
            return User.objects.filter(profile__blood_bank=profile.blood_bank)
        elif user.role == 'HOSPITAL_ADMIN' and profile.hospital:
            return User.objects.filter(profile__hospital=profile.hospital)
        elif user.role == 'INTERNAL_ADMIN':
            return User.objects.all()
        return User.objects.none()

    @transaction.atomic
    def perform_create(self, serializer):
        user = self.request.user
        admin_profile = getattr(user, 'profile', None)
        
        # Capture raw password before it's hashed by serializer (if sent)
        raw_password = self.request.data.get('password')
        
        # Save the new staff user
        staff_user = serializer.save()
        
        # Create profile automatically
        facility_name = "SwiftAid System"
        if user.role == 'BLOODBANK_ADMIN':
            staff_user.role = 'BLOODBANK_STAFF'
            staff_user.save()
            UserProfile.objects.create(user=staff_user, blood_bank=admin_profile.blood_bank)
            facility_name = admin_profile.blood_bank.name
        elif user.role == 'HOSPITAL_ADMIN':
            staff_user.role = 'HOSPITAL_STAFF'
            staff_user.save()
            UserProfile.objects.create(user=staff_user, hospital=admin_profile.hospital)
            facility_name = admin_profile.hospital.name
        
        # Send email
        from core.mail import send_templated_email
        from django.conf import settings
        
        send_templated_email(
            recipient=staff_user.email,
            subject=f"Access Granted - {facility_name}",
            template_name="new_user.html",
            context={
                "facility_name": facility_name,
                "email": staff_user.email,
                "temporary_password": raw_password or "Set during onboarding",
                "portal_url": settings.FRONTEND_BASE_URL
            }
        )
        
    @action(detail=True, methods=['post'], url_path='reset-password')
    def reset_password(self, request, pk=None):
        staff_user = self.get_object()
        new_password = request.data.get('password')
        if not new_password:
            return Response({"message": "Password is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        staff_user.set_password(new_password)
        staff_user.must_change_password = True
        staff_user.save()
        return Response({"message": f"Password reset successfully for {staff_user.username}."})
