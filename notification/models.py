from django.db import models
from core.model import BaseModel
from users.models import User

class Notification(BaseModel):
    TYPE_CHOICES = (
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('PUSH', 'Push Notification'),
    )
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='EMAIL')
    subject = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    sent_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.notification_type} to {self.user.username} - {self.status}"
