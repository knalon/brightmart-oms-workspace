from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from .models import Order

# Import from the external CRM app boundary
from customers.serializers import CustomerDetailSerializer

# Import from internal orders schema module
from .serializers import OrderCreateSerializer, OrderDetailSerializer, StatusUpdateSerializer
from inventory.serializers import ProductDetailSerializer

# Look for your existing service imports and add the status updater
from .services import create_brightmart_order, cancel_brightmart_order, update_order_fulfilment_status
import logging

# Add these imports if not present
from customers.models import Customer
from inventory.models import Product

from core.permissions import IsCustomerRole, IsStaffRole, IsStrictSuperuser

logger = logging.getLogger(__name__)

class OrderListCreateAPIView(APIView):
    # Add this hint for drf-spectacular
    permission_classes = [IsAuthenticated, IsCustomerRole]
    serializer_class = OrderCreateSerializer
    
    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        try:
            # 1. Dispatch to Phase 3 Domain Service Layer
            order = create_brightmart_order(
                customer_id=validated_data['customer_id'],
                items_data=validated_data['items'],
                delivery_address=validated_data['delivery_address']
            )
            
            # 2. PLACE THE LOGGER HERE (Inside the try block, after 'order' is created)
            logger.info(f"{order.order_id} - Created successfully. Status: {order.status}. Total: {order.total_amount}")
            
            output_serializer = OrderDetailSerializer(order)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            if "stock" in str(e).lower():
                return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(operation_id="orders_list")
    def get(self, request):
        queryset = Order.objects.all()
        
        # Add basic enterprise endpoint search filters
        customer_id = request.query_params.get('customerId')
        order_status = request.query_params.get('status')
        
        if customer_id:
            queryset = queryset.filter(customer__customer_id=customer_id)
        if order_status:
            queryset = queryset.filter(status=order_status)
            
        serializer = OrderDetailSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderDetailAPIView(APIView):
    """
    Handles GET /api/orders/{orderId}/ to fetch full composite data logs.
    """
    # Add this hint for drf-spectacular
    permission_classes = [IsAuthenticated]
    serializer_class = OrderDetailSerializer
    def get(self, request, order_id):
        order = get_object_or_404(Order, pk=order_id)
        serializer = OrderDetailSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderCancelAPIView(APIView):
    """
    Handles POST /api/orders/{orderId}/cancel/ cleanly using idempotent services.
    """
    # FIX: Reusing OrderDetailSerializer provides a clean component name for the schema
    permission_classes = [IsAuthenticated]
    serializer_class = OrderDetailSerializer

    def post(self, request, order_id):
        try:
            order = cancel_brightmart_order(order_id)
            serializer = OrderDetailSerializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)
        
class CustomerDetailAPIView(APIView):
    """
    GET /api/customers/{customerId} - CRM Interface adapter lookup (Mandatory)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CustomerDetailSerializer

    def get(self, request, customer_id):
        customer = get_object_or_404(Customer, pk=customer_id)
        serializer = self.serializer_class(customer)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductDetailAPIView(APIView):
    """
    GET /api/products/{productId} - SCM Inventory Interface lookup (Mandatory)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProductDetailSerializer

    def get(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        serializer = self.serializer_class(product)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderStatusUpdateAPIView(APIView):
    """
    PATCH /api/orders/{orderId}/status - Fulfilment state transition gate (Mandatory)
    """
    permission_classes = [IsAuthenticated, IsStaffRole]
    serializer_class = StatusUpdateSerializer

    def patch(self, request, order_id):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_status = serializer.validated_data['status']
            order = update_order_fulfilment_status(order_id, new_status)
            
            # Log structural tracking trace event code
            logger.info(f"{order.order_id} - Fulfilment transition state updated to {order.status}")
            
            output_serializer = OrderDetailSerializer(order)
            return Response(output_serializer.data, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            # Map bad workflow modifications explicitly to 409 Conflict codes
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)