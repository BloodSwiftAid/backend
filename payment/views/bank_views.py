from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from ..models import BankDetail
from ..serializers.bank_serializers import BankDetailSerializer
from core.utils.paystack import PaystackProvider
import logging

logger = logging.getLogger(__name__)

class BankDetailViewSet(viewsets.ModelViewSet):
    serializer_class = BankDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        profile = getattr(user, 'profile', None)
        
        if user.role == 'INTERNAL_ADMIN':
            # Internal admins see platform bank details + everything if they want, 
            # but let's filter to is_internal_admin=True for their own setups
            return BankDetail.objects.filter(is_internal_admin=True)
        
        if profile and profile.blood_bank:
            return BankDetail.objects.filter(blood_bank=profile.blood_bank)
            
        return BankDetail.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        profile = getattr(user, 'profile', None)
        
        # Check limit (max 3)
        existing_count = self.get_queryset().count()
        if existing_count >= 3:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("You can only have up to 3 bank details.")

        # Set ownership
        is_internal_admin = (user.role == 'INTERNAL_ADMIN')
        blood_bank = profile.blood_bank if not is_internal_admin and profile else None
        
        # Call Paystack to create recipient
        paystack = PaystackProvider()
        account_name = self.request.data.get('account_name')
        account_number = self.request.data.get('account_number')
        bank_code = self.request.data.get('bank_code')
        
        res = paystack.create_transfer_recipient(
            name=account_name,
            account_number=account_number,
            bank_code=bank_code
        )
        
        recipient_code = None
        if res.get('status'):
            recipient_code = res['data']['recipient_code']
        else:
            from rest_framework.exceptions import ValidationError
            logger.error(f"Paystack recipient creation failed: {res}")
            raise ValidationError(f"Could not verify bank details with gateway: {res.get('message')}")

        serializer.save(
            created_by=user,
            blood_bank=blood_bank,
            is_internal_admin=is_internal_admin,
            recipient_code=recipient_code
        )
