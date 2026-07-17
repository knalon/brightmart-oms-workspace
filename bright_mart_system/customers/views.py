from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from .models import Customer
from .serializers import CustomerDetailSerializer

class CustomerListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CustomerDetailSerializer

    @extend_schema(operation_id="customers_list")
    def get(self, request):
        customers = Customer.objects.all()
        serializer = self.serializer_class(customers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CustomerDetailAPIView(APIView):
    """
    GET /api/customers/<customer_id>/ - Fetch details for a specific customer.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CustomerDetailSerializer

    @extend_schema(operation_id="customers_retrieve")
    def get(self, request, customer_id):
        try:
            customer = Customer.objects.get(customer_id=customer_id)
            serializer = self.serializer_class(customer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Customer.DoesNotExist:
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)