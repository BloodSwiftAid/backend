from rest_framework import viewsets, permissions
from ..models import Notification
from ..serializers.notification_serializers import NotificationSerializer

from drf_spectacular.utils import extend_schema, extend_schema_view

@extend_schema_view(
    list=extend_schema(tags=['Notifications']),
    retrieve=extend_schema(tags=['Notifications']),
    create=extend_schema(tags=['Notifications']),
    update=extend_schema(tags=['Notifications']),
    partial_update=extend_schema(tags=['Notifications']),
    destroy=extend_schema(tags=['Notifications']),
)
class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
