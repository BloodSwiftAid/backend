from django.db import models
from core.model import BaseModel
from transaction.models import BloodRequest
from users.models import User, BloodBank

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
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total amount paid by customer")
    
    # Financial Breakdown
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, help_text="Platform profit")
    blood_bank_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, help_text="Amount for blood bank")
    gateway_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, help_text="Payment gateway fee")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='CARD')
    transaction_reference = models.CharField(max_length=255, blank=True, null=True, unique=True)

class BankDetail(BaseModel):
    blood_bank = models.ForeignKey(BloodBank, on_delete=models.CASCADE, related_name='bank_details', null=True, blank=True)
    account_number = models.CharField(max_length=20)
    account_name = models.CharField(max_length=255)
    bank_name = models.CharField(max_length=100)
    bank_code = models.CharField(max_length=20)
    recipient_code = models.CharField(max_length=100, blank=True, null=True)
    
    is_internal_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        owner = "Platform Admin" if self.is_internal_admin else (self.blood_bank.name if self.blood_bank else "Unknown")
        return f"{owner} - {self.bank_name} ({self.account_number})"

class Payout(BaseModel):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    )
    blood_bank = models.ForeignKey(BloodBank, on_delete=models.CASCADE, related_name='payouts', null=True, blank=True)
    bank_detail = models.ForeignKey(BankDetail, on_delete=models.SET_NULL, null=True, blank=True, related_name='payouts')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount sent to recipient")
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, help_text="Fee charged for this payout")
    total_debited = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, help_text="Total amount deducted from wallet")
    
    transaction_reference = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    date_completed = models.DateTimeField(null=True, blank=True)
    
    is_internal_admin = models.BooleanField(default=False)

    def __str__(self):
        owner = "Internal Admin" if self.is_internal_admin else (self.blood_bank.name if self.blood_bank else "Platform")
        return f"Payout to {owner} - ₦{self.amount} ({self.status})"
