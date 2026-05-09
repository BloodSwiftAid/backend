from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ..views.user_views import UserViewSet, HospitalViewSet, BloodBankViewSet, UserProfileViewSet, StaffManagementViewSet, GlobalConfigView, MeView
from ..views.stats_views import SystemStatsView

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'hospitals', HospitalViewSet)
router.register(r'blood-banks', BloodBankViewSet)
router.register(r'profiles', UserProfileViewSet)
router.register(r'staff', StaffManagementViewSet, basename='staff-management')

urlpatterns = [
    path('me/', MeView.as_view(), name='user-me'),
    path('system-stats/', SystemStatsView.as_view(), name='system-stats'),
    path('global-config/', GlobalConfigView.as_view(), name='global-config'),
    path('', include(router.urls)),
]
