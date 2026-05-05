from rest_framework import viewsets, permissions
from ..models import Payment
from ..serializers.payment_serializers import PaymentSerializer

from drf_spectacular.utils import extend_schema, extend_schema_view

@extend_schema_view(
    list=extend_schema(tags=['Payments']),
    retrieve=extend_schema(tags=['Payments']),
    create=extend_schema(tags=['Payments']),
    update=extend_schema(tags=['Payments']),
    partial_update=extend_schema(tags=['Payments']),
    destroy=extend_schema(tags=['Payments']),
)
class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
