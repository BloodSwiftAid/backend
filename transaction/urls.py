from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.transaction_views import BloodRequestViewSet, RevenueStatsView, LiveActivityView

router = DefaultRouter()
router.register(r'requests', BloodRequestViewSet, basename='blood-request')

urlpatterns = [
    path('revenue-stats/', RevenueStatsView.as_view(), name='revenue-stats'),
    path('live-activity/', LiveActivityView.as_view(), name='live-activity'),
    path('', include(router.urls)),
]
