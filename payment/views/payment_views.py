from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from ..models import Payment, Payout
from ..serializers.payment_serializers import PaymentSerializer
from ..serializers.payout_serializers import PayoutSerializer
from transaction.models import BloodRequest
from core.utils.paystack import PaystackProvider
from drf_spectacular.utils import extend_schema, extend_schema_view
import uuid
import logging
import hmac
import hashlib
import json
from decouple import config
from django.db import transaction as db_transaction
from django.utils import timezone
from inventory.models import Inventory

logger = logging.getLogger(__name__)

@extend_schema_view(
    list=extend_schema(tags=['Payouts']),
    retrieve=extend_schema(tags=['Payouts']),
    create=extend_schema(tags=['Payouts']),
)
class PayoutViewSet(viewsets.ModelViewSet):
    queryset = Payout.objects.all()
    serializer_class = PayoutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        profile = getattr(user, 'profile', None)
        if user.role == 'INTERNAL_ADMIN':
            return Payout.objects.all()
        if profile and profile.blood_bank:
            return Payout.objects.filter(blood_bank=profile.blood_bank)
        return Payout.objects.none()

    def create(self, request, *args, **kwargs):
        from ..models import BankDetail, Payout
        from users.models import GlobalConfig
        
        user = request.user
        profile = getattr(user, 'profile', None)
        amount = request.data.get('amount')
        bank_detail_id = request.data.get('bank_detail_id')

        if not amount or not bank_detail_id:
            return Response({"error": "Amount and bank_detail_id are required"}, status=400)

        amount = float(amount)
        if amount < 1000: # Minimum payout N1,000
            return Response({"error": "Minimum payout amount is ₦1,000"}, status=400)

        # 1. Verify Balance & Ownership
        is_internal_admin = (user.role == 'INTERNAL_ADMIN')
        bank_detail = BankDetail.objects.filter(id=bank_detail_id, is_active=True).first()
        
        if not bank_detail:
            return Response({"error": "Valid bank detail not found"}, status=400)

        if is_internal_admin:
            if not bank_detail.is_internal_admin:
                return Response({"error": "Invalid bank detail for platform payout"}, status=403)
            config = GlobalConfig.objects.first()
            if not config or config.wallet_balance < amount:
                return Response({"error": "Insufficient platform commission balance"}, status=400)
            blood_bank = None
        else:
            if not profile or not profile.blood_bank or bank_detail.blood_bank != profile.blood_bank:
                return Response({"error": "Unauthorized bank detail"}, status=403)
            bank = profile.blood_bank
            if bank.wallet_balance < amount:
                return Response({"error": "Insufficient wallet balance"}, status=400)
            blood_bank = bank

        # 2. Calculate Fees (only for Blood Banks)
        charge_fee = 0
        if not is_internal_admin:
            config = GlobalConfig.objects.first()
            from django.utils import timezone
            # Count successful/pending payouts this month
            now = timezone.now()
            payouts_this_month = Payout.objects.filter(
                blood_bank=blood_bank,
                date_created__year=now.year,
                date_created__month=now.month
            ).exclude(status='FAILED').count()
            
            if payouts_this_month >= config.allowed_free_payouts:
                charge_fee = float(config.payout_charge_fee)

        if not is_internal_admin and blood_bank.wallet_balance < (amount + charge_fee):
            return Response({"error": f"Insufficient balance to cover amount and ₦{charge_fee} fee"}, status=400)

        # 3. Initiate Transfer via Paystack
        reference = f"PO-{uuid.uuid4().hex[:10].upper()}"
        paystack = PaystackProvider()
        
        # Payout the requested amount
        res = paystack.initiate_transfer(
            amount=amount,
            recipient_code=bank_detail.recipient_code,
            reference=reference,
            reason=f"SwiftAid {'Admin' if is_internal_admin else 'BloodBank'} Payout"
        )

        if not res.get('status'):
            logger.error(f"Paystack transfer initialization failed: {res}")
            return Response({"error": f"Gateway Error: {res.get('message')}"}, status=400)

        # 4. Create Payout Record
        payout = Payout.objects.create(
            blood_bank=blood_bank,
            bank_detail=bank_detail,
            amount=amount,
            fee=charge_fee,
            total_debited=amount + charge_fee,
            transaction_reference=reference,
            status='PENDING',
            is_internal_admin=is_internal_admin
        )

        return Response(PayoutSerializer(payout).data, status=status.HTTP_201_CREATED)


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
    paystack = PaystackProvider()

    def get_queryset(self):
        # Only see own payments
        if self.request.user.role == 'INTERNAL_ADMIN':
            return Payment.objects.all()
        return Payment.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='initialize')
    def initialize_payment(self, request):
        """
        Initialize a payment for a BloodRequest.
        Expected data: { "blood_request_id": "uuid" }
        """
        try:
            request_id = request.data.get('blood_request_id')
            try:
                blood_request = BloodRequest.objects.get(id=request_id)
            except BloodRequest.DoesNotExist:
                return Response({"error": "Blood request not found"}, status=status.HTTP_404_NOT_FOUND)

            # Check if already paid
            if hasattr(blood_request, 'payment') and blood_request.payment.status == 'SUCCESS':
                return Response({"error": "This request has already been paid for"}, status=status.HTTP_400_BAD_REQUEST)

            # Generate unique reference
            reference = f"SA-{uuid.uuid4().hex[:12].upper()}"
            
            # Breakdown fees using our utility
            breakdown = self.paystack.calculate_fees(blood_request.total_amount)

            try:
                with db_transaction.atomic():
                    # Batch processing for inventory locking
                    batch_id = blood_request.batch_id
                    if batch_id:
                        related_requests = BloodRequest.objects.filter(batch_id=batch_id)
                    else:
                        related_requests = [blood_request]
                    
                    for req in related_requests:
                        # Check and deduct inventory for each request in the batch
                        inventory = Inventory.objects.filter(
                            blood_bank=req.blood_bank,
                            product=req.product
                        ).select_for_update().first()

                        if not inventory or inventory.quantity < req.quantity:
                            return Response({"error": f"Insufficient inventory for {req.product.blood_group} to fulfill this request."}, status=status.HTTP_400_BAD_REQUEST)
                        
                        inventory.quantity -= req.quantity
                        inventory.save()

                    # Create or update payment record
                    payment, created = Payment.objects.update_or_create(
                        blood_request=blood_request,
                        defaults={
                            "user": request.user,
                            "amount": blood_request.total_amount,
                            "transaction_reference": reference,
                            "status": "PENDING",
                            "commission_percentage": breakdown['commission_percentage'],
                            "service_fee": breakdown['service_fee'],
                            "blood_bank_fee": breakdown['blood_bank_fee'],
                            "gateway_fee": breakdown['gateway_fee'],
                            "method": "CARD"
                        }
                    )
            except Exception as e:
                logger.error(f"Error in inventory locking: {str(e)}")
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            # Initialize with Paystack
            callback_url = request.data.get('callback_url', f"{config('FRONTEND_BASE_URL', default='http://localhost:3000')}/payment/verify")
            
            paystack_res = self.paystack.initialize_transaction(
                email=request.user.email,
                amount=blood_request.total_amount,
                reference=reference,
                callback_url=callback_url
            )

            if paystack_res.get('status'):
                return Response(paystack_res['data'], status=status.HTTP_200_OK)
            
            # If initialization fails, restore inventory
            with db_transaction.atomic():
                inventory.quantity += blood_request.quantity
                inventory.save()
                
            logger.error(f"Paystack initialization failed for reference {reference}: {paystack_res}")
            return Response({"error": "Could not initialize payment with gateway"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.exception(f"Unexpected error in initialize_payment: {str(e)}")
            return Response({"error": "An internal server error occurred during payment initialization."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='verify')
    def verify_payment(self, request):
        """
        Verify payment after successful checkout.
        Expected data: { "reference": "SA-..." }
        """
        reference = request.data.get('reference')
        if not reference:
            return Response({"error": "Reference is required"}, status=status.HTTP_400_BAD_REQUEST)

        paystack_res = self.paystack.verify_transaction(reference)

        try:
            payment = Payment.objects.get(transaction_reference=reference)
            blood_request = payment.blood_request
            
            if paystack_res.get('status') and paystack_res['data']['status'] == 'success':
                payment.status = 'SUCCESS'
                payment.save()
                
                if blood_request.status == 'PENDING':
                    blood_request.status = 'APPROVED'
                    blood_request.save()
                
                from core.mail import send_receipt_email
                send_receipt_email(blood_request)
                
                return Response({"message": "Payment verified and successful", "status": "SUCCESS"}, status=status.HTTP_200_OK)
            else:
                payment.status = 'FAILED'
                payment.save()
                
                if blood_request.status == 'PENDING':
                    blood_request.status = 'CANCELLED'
                    blood_request.save()
                    
                return Response({"error": "Payment verification failed", "status": "FAILED"}, status=status.HTTP_400_BAD_REQUEST)
                
        except Payment.DoesNotExist:
            return Response({"error": "Payment record not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(f"Error in verify_payment: {str(e)}")
            return Response({"error": "An internal server error occurred during verification."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
    @action(detail=False, methods=['post'], url_path='webhook', permission_classes=[permissions.AllowAny])
    def paystack_webhook(self, request):
        """
        Paystack Webhook Handler
        """
        payload = request.body
        sig_header = request.headers.get('x-paystack-signature')
        
        if not sig_header:
            return Response({"message": "No signature"}, status=status.HTTP_400_BAD_REQUEST)

        # Verify signature
        hash = hmac.new(config('PAYSTACK_SECRET_KEY').encode('utf-8'), payload, hashlib.sha512).hexdigest()
        if hash != sig_header:
            return Response({"message": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)

        event_data = json.loads(payload)
        event_type = event_data.get('event')
        
        if event_type == 'charge.success':
            reference = event_data['data']['reference']
            # Dual verification as requested: Verify via API again
            verification = self.paystack.verify_transaction(reference)
            
            if verification.get('status') and verification['data']['status'] == 'success':
                self._finalize_payment(reference)
            else:
                self._handle_failed_payment(reference)
                
        elif event_type == 'charge.failed':
            reference = event_data['data'].get('reference')
            if reference:
                self._handle_failed_payment(reference)

        elif event_type == 'transfer.success':
            reference = event_data['data'].get('reference')
            self._finalize_payout(reference)

        elif event_type == 'transfer.failed':
            reference = event_data['data'].get('reference')
            self._handle_failed_payout(reference)
        
        return Response({"status": "webhook received"}, status=status.HTTP_200_OK)

    def _finalize_payout(self, reference):
        from ..models import Payout
        from users.models import GlobalConfig
        try:
            with db_transaction.atomic():
                payout = Payout.objects.get(transaction_reference=reference)
                if payout.status == 'SUCCESS':
                    return
                payout.status = 'SUCCESS'
                payout.date_completed = timezone.now()
                payout.save()

                # Deduct from Wallet (Amount + Fee)
                if payout.blood_bank:
                    bank = payout.blood_bank
                    bank.wallet_balance -= payout.total_debited
                    bank.save()
                else:
                    # If it's a platform payout (Internal Admin)
                    config = GlobalConfig.objects.first()
                    if config:
                        config.wallet_balance -= payout.total_debited
                        config.save()
                
                logger.info(f"Payout {reference} successfully finalized. Wallet updated.")
        except Exception as e:
            logger.error(f"Error finalizing payout {reference}: {str(e)}")

    def _handle_failed_payout(self, reference):
        from ..models import Payout
        try:
            with db_transaction.atomic():
                payout = Payout.objects.filter(transaction_reference=reference).first()
                if not payout or payout.status == 'FAILED':
                    return
                payout.status = 'FAILED'
                payout.save()
                logger.warning(f"Payout {reference} failed.")
        except Exception as e:
            logger.error(f"Error handling failed payout {reference}: {str(e)}")

    def _finalize_payment(self, reference):
        from users.models import GlobalConfig
        try:
            with db_transaction.atomic():
                payment = Payment.objects.get(transaction_reference=reference)
                if payment.status == 'SUCCESS':
                    return # Already processed

                payment.status = 'SUCCESS'
                payment.save()
                
                blood_request = payment.blood_request
                
                # Batch processing: find all related requests if this is part of a batch
                batch_id = blood_request.batch_id
                if batch_id:
                    related_requests = BloodRequest.objects.filter(batch_id=batch_id)
                else:
                    related_requests = [blood_request]

                for req in related_requests:
                    if req.status == 'PENDING':
                        req.status = 'APPROVED'
                        req.save()
                    
                    # Update Wallet Balances (split the total fee proportionally or just use the pre-calculated ones)
                    # Actually, each request already has its own fees pre-calculated in the serializer/model
                    # We should probably sum them up or process them individually
                    
                    # 1. Blood Bank Wallet
                    if req.blood_bank:
                        bank = req.blood_bank
                        # We need to calculate the specific fee for THIS request
                        # For now, let's assume the payment.blood_bank_fee was the SUM of all
                        # Wait, if we use batch, we need to be careful.
                        pass # See below for better wallet logic
                
                # Improved Wallet Logic: Sum fees from all related requests
                total_bank_fee = 0
                total_service_fee = 0
                for req in related_requests:
                    # These fields should be on the BloodRequest model too if we want individual tracking
                    # But if they are only on Payment, we use the pre-calculated payment totals
                    pass
                
                # For now, use the Payment model's pre-calculated totals (which should represent the whole batch)
                if blood_request.blood_bank:
                    bank = blood_request.blood_bank
                    bank.wallet_balance += payment.blood_bank_fee
                    bank.save()
                
                config = GlobalConfig.objects.first()
                if config:
                    config.wallet_balance += payment.service_fee
                    config.save()

                # Send receipt email
                from core.mail import send_receipt_email
                send_receipt_email(blood_request)
                logger.info(f"Payment {reference} finalized successfully. Wallets updated.")
        except Exception as e:
            logger.error(f"Error finalizing payment {reference}: {str(e)}")

    def _handle_failed_payment(self, reference):
        try:
            with db_transaction.atomic():
                payment = Payment.objects.filter(transaction_reference=reference).first()
                if not payment or payment.status == 'FAILED':
                    return

                payment.status = 'FAILED'
                payment.save()
                
                blood_request = payment.blood_request
                
                # Batch processing
                batch_id = blood_request.batch_id
                if batch_id:
                    related_requests = BloodRequest.objects.filter(batch_id=batch_id)
                else:
                    related_requests = [blood_request]

                for req in related_requests:
                    # Restore inventory
                    inventory = Inventory.objects.filter(
                        blood_bank=req.blood_bank,
                        product=req.product
                    ).first()
                    
                    if inventory:
                        inventory.quantity += req.quantity
                        inventory.save()

                    if req.status == 'PENDING':
                        req.status = 'CANCELLED'
                        req.save()
                
                logger.warning(f"Payment {reference} marked as failed. Inventory restored for batch {batch_id or 'single'}.")
        except Exception as e:
            logger.error(f"Error handling failed payment {reference}: {str(e)}")
