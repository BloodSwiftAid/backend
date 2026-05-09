from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.payment_views import PaymentViewSet, PayoutViewSet

from .views.bank_views import BankDetailViewSet

router = DefaultRouter()
router.register(r'payments', PaymentViewSet)
router.register(r'payouts', PayoutViewSet)
router.register(r'bank-details', BankDetailViewSet, basename='bank-details')

urlpatterns = [
    path('', include(router.urls)),
]
