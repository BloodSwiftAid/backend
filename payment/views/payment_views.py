from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from ..models import Payment
from ..serializers.payment_serializers import PaymentSerializer
from transaction.models import BloodRequest
from core.utils.paystack import PaystackProvider
from drf_spectacular.utils import extend_schema, extend_schema_view
import uuid

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

        # Initialize with Paystack
        callback_url = request.data.get('callback_url', f"{config('FRONTEND_BASE_URL', default='http://localhost:5173')}/payment/verify")
        
        paystack_res = self.paystack.initialize_transaction(
            email=request.user.email,
            amount=blood_request.total_amount,
            reference=reference,
            callback_url=callback_url
        )

        if paystack_res.get('status'):
            return Response(paystack_res['data'], status=status.HTTP_200_OK)
        
        return Response({"error": "Could not initialize payment with gateway"}, status=status.HTTP_400_BAD_REQUEST)

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

        if paystack_res.get('status') and paystack_res['data']['status'] == 'success':
            try:
                payment = Payment.objects.get(transaction_reference=reference)
                payment.status = 'SUCCESS'
                payment.save()
                
                # Update blood request status if needed
                blood_request = payment.blood_request
                if blood_request.status == 'PENDING':
                    blood_request.status = 'APPROVED'
                    blood_request.save()
                
                # Send receipt email
                from core.mail import send_receipt_email
                send_receipt_email(blood_request)
                
                return Response({"message": "Payment verified and successful", "status": "SUCCESS"}, status=status.HTTP_200_OK)
            except Payment.DoesNotExist:
                return Response({"error": "Payment record not found"}, status=status.HTTP_404_NOT_FOUND)
        
        return Response({"error": "Payment verification failed", "status": "FAILED"}, status=status.HTTP_400_BAD_REQUEST)
