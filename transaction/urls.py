from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.transaction_views import BloodRequestViewSet

router = DefaultRouter()
router.register(r'requests', BloodRequestViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
