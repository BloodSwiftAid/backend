from django.urls import path
from ..views.auth_views import (
    RequestPasswordResetOTPView, 
    ResetPasswordView, 
    ChangePasswordView,
    LogoutView,
    MyTokenObtainPairView
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('otp/request/', RequestPasswordResetOTPView.as_view(), name='password_reset_request'),
    path('otp/verify/', ResetPasswordView.as_view(), name='password_reset_confirm'),
    path('password/change/', ChangePasswordView.as_view(), name='password_change'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
