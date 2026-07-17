from django.urls import path
from .views import ShippingCarrierWebhookAPIView, ObtainAuthTokenAPIView
from .views import UserRegistrationAPIView, StaffRegistrationAPIView

urlpatterns = [
    path('webhooks/shipping/', ShippingCarrierWebhookAPIView.as_view(), name='webhook-shipping'),
    path('auth/token/', ObtainAuthTokenAPIView.as_view(), name='api-token-auth'),
    path('auth/register/', UserRegistrationAPIView.as_view(), name='user-register'),
    path('auth/register-staff/', StaffRegistrationAPIView.as_view(), name='staff-register'),
]