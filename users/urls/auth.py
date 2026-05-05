from django.urls import path
from ..views.auth_views import (
    RequestPasswordResetOTPView, 
    ResetPasswordView, 
    ChangePasswordView,
    MyTokenObtainPairView
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('password-reset-request/', RequestPasswordResetOTPView.as_view(), name='password_reset_request'),
    path('password-reset-confirm/', ResetPasswordView.as_view(), name='password_reset_confirm'),
    path('password-change/', ChangePasswordView.as_view(), name='password_change'),
]
