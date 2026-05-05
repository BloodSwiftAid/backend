from rest_framework import viewsets, permissions as drf_permissions
from ..models import User, Hospital, BloodBank, UserProfile
from ..serializers.user_serializers import (
    UserSerializer, 
    HospitalSerializer, 
    BloodBankSerializer, 
    UserProfileSerializer
)
from ..permissions import IsInternalAdmin

from drf_spectacular.utils import extend_schema, extend_schema_view

@extend_schema_view(
    list=extend_schema(tags=['Users']),
    retrieve=extend_schema(tags=['Users']),
)
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [drf_permissions.IsAuthenticated, IsInternalAdmin]

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
