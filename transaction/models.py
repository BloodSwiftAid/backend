from django.db import models
from core.model import BaseModel
from users.models import User, Hospital, BloodBank
from inventory.models import Product

class BloodRequest(BaseModel):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('DISPATCHED', 'Dispatched'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    )
    SOURCE_CHOICES = (
        ('MARKETPLACE', 'Marketplace'),
        ('POS', 'Direct POS Sale'),
        ('WHATSAPP', 'WhatsApp Bot'),
    )
    PAYMENT_METHOD_CHOICES = (
        ('TRANSFER', 'Bank Transfer'),
        ('POS', 'POS Terminal'),
        ('CASH', 'Cash Payment'),
    )
    requester_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='requested_bloods')
    requester_hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, null=True, blank=True, related_name='requested_bloods')
    
    blood_bank = models.ForeignKey(BloodBank, on_delete=models.CASCADE, related_name='received_requests', null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    
    # Hospital/Patient info
    patient_name = models.CharField(max_length=255, blank=True, null=True)
    patient_details = models.TextField(blank=True, null=True)
    hospital_location = models.TextField(blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='MARKETPLACE')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='TRANSFER')
    batch_id = models.CharField(max_length=100, blank=True, null=True, help_text="Groups multiple requests in one marketplace session")
    
    # Fees & Pricing
    blood_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    
    # Delivery info
    pickup_location = models.TextField(blank=True, null=True)
    delivery_location = models.TextField(blank=True, null=True)
    dispatch_rider = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_deliveries')

    
    def __str__(self):
        bank_name = self.blood_bank.name if self.blood_bank else "Unassigned"
        return f"Request {self.id} - {self.product} from {bank_name}"
