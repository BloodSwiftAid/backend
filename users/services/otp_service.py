import random
import string
from django.utils import timezone
from datetime import timedelta
from ..models import UserOTP

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

def create_user_otp(user, purpose='VERIFICATION'):
    otp_code = generate_otp()
    expiry_time = timezone.now() + timedelta(minutes=10) # 10 minutes expiry
    
    # Deactivate previous unused OTPs for the same purpose
    UserOTP.objects.filter(user=user, purpose=purpose, is_used=False).update(is_used=True)
    
    return UserOTP.objects.create(
        user=user,
        otp=otp_code,
        purpose=purpose,
        expiry=expiry_time
    )

def verify_otp(user, otp_code, purpose='VERIFICATION'):
    otp_obj = UserOTP.objects.filter(
        user=user, 
        otp=otp_code, 
        purpose=purpose, 
        is_used=False,
        expiry__gt=timezone.now()
    ).first()
    
    if otp_obj:
        otp_obj.is_used = True
        otp_obj.save()
        return True
    return False
