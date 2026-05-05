from rest_framework import viewsets, permissions
from ..models import BloodRequest
from ..serializers.transaction_serializers import BloodRequestSerializer

from drf_spectacular.utils import extend_schema, extend_schema_view

@extend_schema_view(
    list=extend_schema(tags=['Transactions']),
    retrieve=extend_schema(tags=['Transactions']),
    create=extend_schema(tags=['Transactions']),
    update=extend_schema(tags=['Transactions']),
    partial_update=extend_schema(tags=['Transactions']),
    destroy=extend_schema(tags=['Transactions']),
)
class BloodRequestViewSet(viewsets.ModelViewSet):
    queryset = BloodRequest.objects.all()
    serializer_class = BloodRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
