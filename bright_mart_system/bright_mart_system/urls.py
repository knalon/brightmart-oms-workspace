from django.contrib import admin
from django.urls import path, include

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from drf_spectacular.utils import extend_schema

from django.db import connection
from rest_framework import serializers



# Create a quick schema object for the health response layout
class HealthCheckResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    database = serializers.CharField()

@extend_schema(responses={200: HealthCheckResponseSerializer})
@api_view(['GET'])
@permission_classes([AllowAny])
def system_health_check(request):
    # ... (Keep your existing check logic here exactly the same)
    try:
        connection.ensure_connection()
        return Response({"status": "UP", "database": "CONNECTED"}, status=200)
    except Exception:
        return Response({"status": "DOWN", "database": "UNAVAILABLE"}, status=500)



urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Global System Liveness Endpoint Probe
    path('api/health', system_health_check, name='health-check'),
    
    # OpenAPI Documentation Schema Generation Engines
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # Bounded Enterprise Context App Routing Pipelines (Decoupled Architecture)
    path('api/', include('orders.urls')),
    path('api/', include('inventory.urls')),
    path('api/', include('core.urls')),
    path('api/', include('customers.urls')),
]