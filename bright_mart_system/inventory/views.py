from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from .models import Product
from .serializers import ProductDetailSerializer
from core.permissions import IsStaffRole
from django.db.models import Q

class ProductListCreateAPIView(APIView):
    """
    GET  /api/products/ - Fetch full product catalog.
    POST /api/products/ - Provision new product entry into inventory matrix.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProductDetailSerializer

    @extend_schema(operation_id="inventory_products_list")
    def get(self, request):
        products = Product.objects.all()
        serializer = self.serializer_class(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(operation_id="inventory_products_create")
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# RE-ADD THIS CLASS IF IT WAS ACCIDENTALLY DELETED:
class ProductDetailAPIView(APIView):
    """
    GET /api/products/<product_id>/ - Fetch details for a specific item.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProductDetailSerializer

    @extend_schema(operation_id="inventory_products_retrieve")
    def get(self, request, product_id):
        try:
            product = Product.objects.get(product_id=product_id)
            serializer = self.serializer_class(product)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        
    @extend_schema(
        operation_id="products_partial_update",
        request=ProductDetailSerializer,
        responses={200: ProductDetailSerializer},
        description="Partially updates product specs or updates inventory stock metrics."
    )
    def patch(self, request, product_id):
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # partial=True allows you to send ONLY the available_stock field
        serializer = self.serializer_class(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class LowStockAlertAPIView(APIView):
    """
    GET /api/products/low-stock/ - Operational telemetry endpoint.
    Flags items dropping below critical enterprise margins (e.g., threshold = 2).
    """
    permission_classes = [IsAuthenticated, IsStaffRole]
    serializer_class = ProductDetailSerializer

    def get(self, request):
        try:
            threshold = int(request.query_params.get('threshold', 2))
        except ValueError:
            return Response({"error": "Threshold parameter must be an integer."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Refined to guarantee 0 and negative values are aggressively captured
        low_stock_products = Product.objects.filter(available_stock__lte=threshold)
        
        serializer = self.serializer_class(low_stock_products, many=True)
        return Response({
            "alert_triggered": low_stock_products.exists(),
            "critical_threshold": threshold,
            "count": low_stock_products.count(),
            "items": serializer.data
        }, status=status.HTTP_200_OK)