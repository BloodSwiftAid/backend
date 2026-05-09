from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.inventory_views import (
    BloodTypeViewSet,
    ProductCategoryViewSet, 
    ProductViewSet, 
    InventoryViewSet, 
    DonationViewSet, 
    InventoryStatsView,
    MarketplaceView
)

router = DefaultRouter()
router.register(r'blood-types', BloodTypeViewSet)
router.register(r'categories', ProductCategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'inventory', InventoryViewSet, basename='inventory')
router.register(r'donations', DonationViewSet, basename='donations')

urlpatterns = [
    path('stats/', InventoryStatsView.as_view(), name='inventory-stats'),
    path('marketplace/', MarketplaceView.as_view(), name='marketplace-list'),
    path('', include(router.urls)),
]
