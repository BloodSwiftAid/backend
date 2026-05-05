from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ..views.user_views import UserViewSet, HospitalViewSet, BloodBankViewSet, UserProfileViewSet
from ..views.stats_views import SystemStatsView

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'hospitals', HospitalViewSet)
router.register(r'blood-banks', BloodBankViewSet)
router.register(r'profiles', UserProfileViewSet)

urlpatterns = [
    path('system-stats/', SystemStatsView.as_view(), name='system-stats'),
    path('', include(router.urls)),
]
