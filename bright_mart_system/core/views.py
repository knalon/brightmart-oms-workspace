from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.contrib.auth.models import update_last_login
from orders.models import Order
from core.models import Shipment
from orders.serializers import OrderDetailSerializer
from .serializers import ShippingWebhookInputSerializer
import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema
from .serializers import UserRegistrationSerializer, StaffRegistrationSerializer
from .permissions import IsStrictSuperuser


logger = logging.getLogger('orders')
class ObtainAuthTokenAPIView(APIView):
    """
    POST /api/auth/token/ - Handshakes user credentials.
    Returns a secure persistent API Token required for header authorization.
    """
    permission_classes = [AllowAny]  # Must be open so users can log in!
    serializer_class = AuthTokenSerializer

    @extend_schema(operation_id="auth_token_create")
    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            # 🌟 THE MAGIC STEP: Manually update last_login in the database
            update_last_login(None, user)
        
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.pk,
                'email': user.email
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ShippingCarrierWebhookAPIView(APIView):
    """
    POST /api/webhooks/shipping/ - Integrates with external 3PL carrier APIs.
    Updates internal core Shipment tracking logs and updates order fulfillment states.
    """
    # FIX: Explicit hint tells drf-spectacular how to map this request structure
    permission_classes = [AllowAny]
    serializer_class = ShippingWebhookInputSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        carrier_event = serializer.validated_data['event']
        tracking_number = serializer.validated_data['tracking_number']
        order_id = serializer.validated_data['order_id']

        # Map external event payloads to core system state steps
        EVENT_MAP = {
            'parcel.shipped': 'SHIPPED',
            'parcel.delivered': 'DELIVERED'
        }

        target_status = EVENT_MAP.get(carrier_event)
        if not target_status:
            return Response({"error": f"Unhandled event type: {carrier_event}"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            try:
                # Lock the row to prevent racing conditions with manual dashboard clicks
                order = Order.objects.select_for_update().get(pk=order_id)
                shipment, _ = Shipment.objects.get_or_create(order=order)
                
                # Update integration records
                shipment.tracking_number = tracking_number
                shipment.carrier = serializer.validated_data.get('carrier', 'BrightMart Express')
                shipment.status = target_status
                shipment.save()

                # Step the core lifecycle state forward directly via business validation logic rules
                order.status = target_status
                order.save()
                
                logger.info(f"WEBHOOK SUCCESS: {order.order_id} stepped to {target_status} via external event sync.")
                
                return Response({
                    "message": "Webhook processed successfully.",
                    "order": OrderDetailSerializer(order).data
                }, status=status.HTTP_200_OK)

            except Order.DoesNotExist:
                return Response({"error": f"Order reference {order_id} could not be resolved."}, status=status.HTTP_404_NOT_FOUND)
            
class UserRegistrationAPIView(APIView):
    # CRITICAL: Spectacular needs this explicit property to map the fields in the UI
    serializer_class = UserRegistrationSerializer

    @extend_schema(
        operation_id="auth_register",
        request=UserRegistrationSerializer,
        responses={201: UserRegistrationSerializer}
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User and Customer profile successfully created."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffRegistrationAPIView(APIView):
    # Lock this down so ONLY an existing superuser can hit it to provision employees
    permission_classes = [IsStrictSuperuser]
    serializer_class = StaffRegistrationSerializer

    @extend_schema(
        operation_id="auth_register_staff",
        request=StaffRegistrationSerializer,
        responses={201: StaffRegistrationSerializer}
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Staff account provisioned successfully."}, status=201)
        return Response(serializer.errors, status=400)