from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.inventory_views import ProductCategoryViewSet, ProductViewSet, InventoryViewSet

router = DefaultRouter()
router.register(r'categories', ProductCategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'inventory', InventoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
