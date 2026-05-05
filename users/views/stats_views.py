from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from ..models import User, Hospital, BloodBank
from ..permissions import IsInternalAdmin

class SystemStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsInternalAdmin]

    def get(self, request):
        stats = {
            "blood_banks": BloodBank.objects.count(),
            "hospitals": Hospital.objects.count(),
            "total_users": User.objects.exclude(role='INTERNAL_ADMIN').count(),
            # You can add more complex logic for pending verifications across both models
            "pending_verifications": Hospital.objects.filter(is_verified=False).count() + BloodBank.objects.filter(is_verified=False).count(),
        }
        return Response(stats)
