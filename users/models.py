from django.db import models
from django.contrib.auth.models import AbstractUser
from core.model import BaseModel

class User(AbstractUser, BaseModel):
    ROLE_CHOICES = (
        ('HOSPITAL_ADMIN', 'Hospital Admin'),
        ('HOSPITAL_STAFF', 'Hospital Staff'),
        ('BLOODBANK_ADMIN', 'Bloodbank Admin'),
        ('BLOODBANK_STAFF', 'Bloodbank Staff'),
        ('PUBLIC_USER', 'Public User'),
        ('DISPATCH_RIDER', 'Dispatch Rider'),
        ('INTERNAL_ADMIN', 'Internal Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='PUBLIC_USER')
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    
    otp = models.CharField(max_length=10, blank=True, null=True)
    otp_expiry = models.DateTimeField(blank=True, null=True)
    must_change_password = models.BooleanField(default=False)

    def __str__(self):
        return self.username

class UserOTP(BaseModel):
    PURPOSE_CHOICES = (
        ('VERIFICATION', 'Email/Phone Verification'),
        ('PASSWORD_RESET', 'Password Reset'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    otp = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default='VERIFICATION')
    is_used = models.BooleanField(default=False)
    expiry = models.DateTimeField()

    def __str__(self):
        return f"{self.user.username} - {self.otp} ({self.purpose})"

class BaseOrganization(BaseModel):
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    country = models.CharField(max_length=100, default='Nigeria')
    state = models.CharField(max_length=100, blank=True, null=True)
    area = models.CharField(max_length=100, blank=True, null=True)
    street = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Contact & KYC
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    kyc_document = models.FileField(upload_to='kyc_docs/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

class Hospital(BaseOrganization):
    hospital_type = models.CharField(max_length=100, blank=True, null=True) # e.g. General, Private
    has_emergency_unit = models.BooleanField(default=True)

class BloodBank(BaseOrganization):
    license_number = models.CharField(max_length=100, blank=True, null=True)
    storage_capacity_liters = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=10.0) # Default 10%
    wallet_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)

class UserProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, null=True, blank=True, related_name='staff')
    blood_bank = models.ForeignKey(BloodBank, on_delete=models.SET_NULL, null=True, blank=True, related_name='staff')
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.hospital and self.user.role in ['HOSPITAL_STAFF', 'HOSPITAL_ADMIN']:
            staff_count = UserProfile.objects.filter(hospital=self.hospital).exclude(id=self.id).count()
            if staff_count >= 10: # Increased limit for hospital
                raise ValidationError("This hospital has reached the maximum staff limit.")
        
        if self.blood_bank and self.user.role in ['BLOODBANK_STAFF', 'BLOODBANK_ADMIN']:
            staff_count = UserProfile.objects.filter(blood_bank=self.blood_bank).exclude(id=self.id).count()
            if staff_count >= 5:
                raise ValidationError("This blood bank has reached the maximum staff limit.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class GlobalConfig(BaseModel):
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=10.0)
    address = models.TextField(blank=True, null=True, default="123 SwiftAid Tech Plaza, Lagos, Nigeria")
    contact_email = models.EmailField(blank=True, null=True, default="support@swiftaid.com")
    contact_phone = models.CharField(max_length=20, blank=True, null=True, default="+234 800 SWIFTAID")
    wallet_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    allowed_free_payouts = models.IntegerField(default=2, help_text="Number of free payouts per month for blood banks")
    payout_charge_fee = models.DecimalField(max_digits=10, decimal_places=2, default=50.0, help_text="Flat fee charged after free payouts are exhausted")
    
    class Meta:
        verbose_name = "Global Configuration"
        verbose_name_plural = "Global Configurations"

    def __str__(self):
        return f"Global Config (Commission: {self.commission_percentage}%)"


class VerificationLog(BaseModel):
    ACTION_CHOICES = (
        ('VERIFIED', 'Verified'),
        ('UNVERIFIED', 'Unverified'),
        ('ACTIVATED', 'Activated'),
        ('DEACTIVATED', 'Deactivated'),
    )
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='verification_actions')
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, null=True, blank=True)
    blood_bank = models.ForeignKey(BloodBank, on_delete=models.CASCADE, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Verification Log"
        verbose_name_plural = "Verification Logs"
        ordering = ['-date_created']

    def __str__(self):
        target = self.hospital or self.blood_bank
        admin_name = self.admin.username if self.admin else "System"
        return f"{admin_name} {self.action} {target.name if target else 'N/A'}"
