from django.db import models
from core.model import BaseModel
from transaction.models import BloodRequest
from users.models import User

class Payment(BaseModel):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    )
    METHOD_CHOICES = (
        ('CARD', 'Credit/Debit Card'),
        ('TRANSFER', 'Bank Transfer'),
        ('CASH', 'Cash on Delivery'),
    )
    
    blood_request = models.OneToOneField(BloodRequest, on_delete=models.CASCADE, related_name='payment')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='CARD')
    transaction_reference = models.CharField(max_length=255, blank=True, null=True, unique=True)
    
    def __str__(self):
        return f"Payment {self.id} for Request {self.blood_request.id} - {self.status}"
