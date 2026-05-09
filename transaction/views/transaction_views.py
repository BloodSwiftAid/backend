from rest_framework import viewsets, permissions
from ..models import BloodRequest
from ..serializers.transaction_serializers import BloodRequestSerializer
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction, models
from inventory.models import Inventory

from drf_spectacular.utils import extend_schema, extend_schema_view

@extend_schema_view(
    list=extend_schema(tags=['Transactions']),
    retrieve=extend_schema(tags=['Transactions']),
    create=extend_schema(tags=['Transactions']),
    update=extend_schema(tags=['Transactions']),
    partial_update=extend_schema(tags=['Transactions']),
    destroy=extend_schema(tags=['Transactions']),
)
class BloodRequestViewSet(viewsets.ModelViewSet):
    serializer_class = BloodRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        profile = getattr(user, 'profile', None)
        if profile and profile.hospital:
            serializer.save(requester_user=user, requester_hospital=profile.hospital)
        else:
            serializer.save(requester_user=user)

    def get_queryset(self):
        user = self.request.user
        profile = getattr(user, 'profile', None)
        if profile and profile.blood_bank:
            return BloodRequest.objects.filter(blood_bank=profile.blood_bank)
        elif profile and profile.hospital:
            return BloodRequest.objects.filter(requester_hospital=profile.hospital)
        elif user.role == 'INTERNAL_ADMIN':
            return BloodRequest.objects.all()
        return BloodRequest.objects.none()

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def approve(self, request, pk=None):
        blood_request = self.get_object()
        if blood_request.status != 'PENDING':
            return Response({"message": "Only pending requests can be approved."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check inventory
        inventory = Inventory.objects.filter(
            blood_bank=blood_request.blood_bank,
            product=blood_request.product
        ).first()

        if not inventory or inventory.quantity < blood_request.quantity:
            return Response({"message": "Insufficient inventory to fulfill this request."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Deduct from inventory
        inventory.quantity -= blood_request.quantity
        inventory.save()

        blood_request.status = 'APPROVED'
        blood_request.save()
        
        return Response({"message": "Request approved and inventory reserved."})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        blood_request = self.get_object()
        blood_request.status = 'REJECTED'
        blood_request.save()
        return Response({"message": "Request rejected."})

    @action(detail=False, methods=['post'], url_path='pos-sale')
    @transaction.atomic
    def direct_pos_sale(self, request):
        user = request.user
        profile = getattr(user, 'profile', None)
        if not (profile and profile.blood_bank):
            return Response({"message": "Only blood bank staff can perform POS sales."}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create the request as fulfilled immediately
        blood_request = serializer.save(
            blood_bank=profile.blood_bank,
            status='DELIVERED',
            source='POS'
        )

        # Deduct inventory
        inventory = Inventory.objects.filter(
            blood_bank=profile.blood_bank,
            product=blood_request.product
        ).first()

        if not inventory or inventory.quantity < blood_request.quantity:
            # Rollback transaction
            transaction.set_rollback(True)
            return Response({"message": "Insufficient inventory for this sale."}, status=status.HTTP_400_BAD_REQUEST)
        
        inventory.quantity -= blood_request.quantity
        inventory.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

class RevenueStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.db.models import Sum, Count
        from django.db.models.functions import TruncMonth
        from django.utils import timezone
        import datetime

        user = request.user
        profile = getattr(user, 'profile', None)
        
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Base Query
        if user.role == 'INTERNAL_ADMIN':
            queryset = BloodRequest.objects.filter(status='DELIVERED')
        elif profile and profile.blood_bank:
            queryset = BloodRequest.objects.filter(blood_bank=profile.blood_bank, status='DELIVERED')
        else:
            return Response({"error": "Unauthorized"}, status=403)

        # 1. Overall Revenue
        total_revenue = queryset.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        total_commission = queryset.aggregate(Sum('commission_amount'))['commission_amount__sum'] or 0
        
        # 2. Monthly Revenue
        monthly_revenue = queryset.filter(date_created__gte=start_of_month).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        monthly_commission = queryset.filter(date_created__gte=start_of_month).aggregate(Sum('commission_amount'))['commission_amount__sum'] or 0

        # 3. Revenue per Blood Type
        revenue_by_type = queryset.values('product__blood_group').annotate(
            amount=Sum('total_amount'),
            profit=Sum('commission_amount')
        ).order_by('product__blood_group')

        # 4. Graph Data (Last 6 Months)
        six_months_ago = now - datetime.timedelta(days=180)
        graph_data = queryset.filter(date_created__gte=six_months_ago).annotate(
            month=TruncMonth('date_created')
        ).values('month').annotate(
            revenue=Sum('total_amount'),
            profit=Sum('commission_amount'),
            pos_revenue=Sum('total_amount', filter=models.Q(source='POS')),
            market_revenue=Sum('total_amount', filter=models.Q(source='MARKETPLACE'))
        ).order_by('month')

        # 5. Revenue per Facility (For Internal Admin)
        revenue_by_facility = []
        if user.role == 'INTERNAL_ADMIN':
            revenue_by_facility = queryset.values(
                'blood_bank__id', 
                'blood_bank__name'
            ).annotate(
                total_revenue=Sum('total_amount'),
                total_profit=Sum('commission_amount'),
                request_count=Count('id')
            ).order_by('-total_revenue')

        # Trend calculation (Comparison with last month)
        start_of_last_month = (start_of_month - datetime.timedelta(days=1)).replace(day=1)
        end_of_last_month = start_of_month - datetime.timedelta(microseconds=1)
        
        last_month_revenue = queryset.filter(
            date_created__gte=start_of_last_month,
            date_created__lte=end_of_last_month
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

        revenue_trend = 0
        if last_month_revenue > 0:
            revenue_trend = round(((monthly_revenue - last_month_revenue) / last_month_revenue) * 100, 1)

        return Response({
            "total_revenue": total_revenue,
            "total_profit": total_commission,
            "monthly_revenue": monthly_revenue,
            "monthly_profit": monthly_commission,
            "revenue_by_type": revenue_by_type,
            "graph_data": graph_data,
            "revenue_by_facility": revenue_by_facility,
            "revenue_trend": revenue_trend
        })

class LiveActivityView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != 'INTERNAL_ADMIN':
            return Response({"error": "Unauthorized"}, status=403)
        
        recent_requests = BloodRequest.objects.select_related('blood_bank', 'product').order_by('-date_created')[:15]
        # Include fields like source, status, total_amount, blood_bank__name, product__blood_group
        data = []
        for req in recent_requests:
            data.append({
                "id": req.id,
                "facility": req.blood_bank.name if req.blood_bank else "System",
                "type": req.product.blood_group if req.product else "N/A",
                "quantity": req.quantity,
                "amount": float(req.total_amount),
                "status": req.status,
                "source": req.source,
                "timestamp": req.date_created
            })
        return Response(data)
