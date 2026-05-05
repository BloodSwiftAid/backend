from rest_framework import viewsets, permissions
from ..models import ProductCategory, Product, Inventory
from ..serializers.inventory_serializers import ProductCategorySerializer, ProductSerializer, InventorySerializer

from drf_spectacular.utils import extend_schema, extend_schema_view

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
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [permissions.IsAuthenticated]
