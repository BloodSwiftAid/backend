from rest_framework import viewsets, permissions
from ..models import BloodType, ProductCategory, Product, Inventory, Donation
from ..serializers.inventory_serializers import (
    BloodTypeSerializer,
    ProductCategorySerializer, 
    ProductSerializer, 
    InventorySerializer,
    DonationSerializer
)
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum

from drf_spectacular.utils import extend_schema, extend_schema_view

@extend_schema_view(
    list=extend_schema(tags=['Inventory - Blood Types']),
    retrieve=extend_schema(tags=['Inventory - Blood Types']),
    create=extend_schema(tags=['Inventory - Blood Types']),
    update=extend_schema(tags=['Inventory - Blood Types']),
    partial_update=extend_schema(tags=['Inventory - Blood Types']),
    destroy=extend_schema(tags=['Inventory - Blood Types']),
)
class BloodTypeViewSet(viewsets.ModelViewSet):
    queryset = BloodType.objects.all()
    serializer_class = BloodTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

@extend_schema_view(
    list=extend_schema(tags=['Inventory - Categories']),
    retrieve=extend_schema(tags=['Inventory - Categories']),
    create=extend_schema(tags=['Inventory - Categories']),
    update=extend_schema(tags=['Inventory - Categories']),
    partial_update=extend_schema(tags=['Inventory - Categories']),
    destroy=extend_schema(tags=['Inventory - Categories']),
)
class ProductCategoryViewSet(viewsets.ModelViewSet):
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

@extend_schema_view(
    list=extend_schema(tags=['Inventory - Products']),
    retrieve=extend_schema(tags=['Inventory - Products']),
    create=extend_schema(tags=['Inventory - Products']),
    update=extend_schema(tags=['Inventory - Products']),
    partial_update=extend_schema(tags=['Inventory - Products']),
    destroy=extend_schema(tags=['Inventory - Products']),
)
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

@extend_schema_view(
    list=extend_schema(tags=['Inventory - Stock']),
    retrieve=extend_schema(tags=['Inventory - Stock']),
    create=extend_schema(tags=['Inventory - Stock']),
    update=extend_schema(tags=['Inventory - Stock']),
    partial_update=extend_schema(tags=['Inventory - Stock']),
    destroy=extend_schema(tags=['Inventory - Stock']),
)
class InventoryViewSet(viewsets.ModelViewSet):
    serializer_class = InventorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        profile = getattr(user, 'profile', None)
        if profile and profile.blood_bank:
            return Inventory.objects.filter(blood_bank=profile.blood_bank)
        elif user.role == 'INTERNAL_ADMIN':
            return Inventory.objects.all()
        return Inventory.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        profile = getattr(user, 'profile', None)
        if profile and profile.blood_bank:
            serializer.save(blood_bank=profile.blood_bank)
        else:
            serializer.save()

@extend_schema_view(
    list=extend_schema(tags=['Inventory - Donations']),
    create=extend_schema(tags=['Inventory - Donations']),
)
class DonationViewSet(viewsets.ModelViewSet):
    serializer_class = DonationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        profile = getattr(user, 'profile', None)
        if profile and profile.blood_bank:
            return Donation.objects.filter(blood_bank=profile.blood_bank)
        elif user.role == 'INTERNAL_ADMIN':
            return Donation.objects.all()
        return Donation.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        profile = getattr(user, 'profile', None)
        if profile and profile.blood_bank:
            # Auto-assign blood bank and update inventory
            donation = serializer.save(blood_bank=profile.blood_bank)
            
            # Find or create inventory for this blood group
            blood_type = BloodType.objects.filter(group=donation.blood_group).first()
            if blood_type:
                inventory, created = Inventory.objects.get_or_create(
                    blood_bank=profile.blood_bank,
                    blood_type=blood_type,
                    defaults={'price': blood_type.base_price}
                )
                inventory.quantity += 1 # Assume 1 unit per donation record
                inventory.save()
        else:
            serializer.save()

class InventoryStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        profile = getattr(user, 'profile', None)
        if not (profile and profile.blood_bank):
            return Response({"error": "Blood bank context required"}, status=400)

        stats = Inventory.objects.filter(blood_bank=profile.blood_bank).values(
            'blood_type__group'
        ).annotate(
            total_quantity=Sum('quantity')
        )

        formatted_stats = {item['blood_type__group']: item['total_quantity'] for item in stats if item['blood_type__group']}
        return Response(formatted_stats)

class MarketplaceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(tags=['Marketplace'])
    def get(self, request):
        from users.models import GlobalConfig
        config = GlobalConfig.objects.first()
        commission_pct = config.commission_percentage if config else 10.0
        
        blood_types = BloodType.objects.filter(is_active=True)
        data = []
        for bt in blood_types:
            total_qty = Inventory.objects.filter(blood_type=bt).aggregate(Sum('quantity'))['quantity__sum'] or 0
            # Calculate price
            commission_amount = (bt.base_price * commission_pct) / 100
            total_price = bt.base_price + commission_amount
            
            data.append({
                "id": bt.id,
                "group": bt.group,
                "available_units": total_qty,
                "base_price": float(bt.base_price),
                "commission_amount": float(commission_amount),
                "total_price": float(total_price)
            })
        return Response(data)
