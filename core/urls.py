"""core URL Configuration"""
from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

def api_root(request):
    """Root API endpoint with system information"""
    return JsonResponse({
        'name': 'SwiftAid Blood Bank API',
        'description': 'Comprehensive backend API system for managing blood bank inventory, transactions, and user onboarding.',
        'version': '1.0.0',
        'authentication': 'JWT Bearer Token Required',
    })


urlpatterns = [

    path('', api_root, name='api_root'),
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Authentication
    path('api/v1/auth/', include('users.urls.auth')),
    path('api/v1/user/', include('users.urls.users')),

    
    # API Services
    path('api/v1/inventory/', include('inventory.urls')),
    path('api/v1/transaction/', include('transaction.urls')),
    path('api/v1/payment/', include('payment.urls')),
    path('api/v1/notification/', include('notification.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
