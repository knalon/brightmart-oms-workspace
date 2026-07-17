from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from .models import Order, OrderItem
# At the top of orders/serializers.py

@extend_schema_field(serializers.BooleanField)
def get_stockReserved(self, obj):
    return obj.status not in ['PENDING', 'CANCELLED']

class StatusUpdateSerializer(serializers.Serializer):
    status = serializers.CharField(max_length=20)
    
class OrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.CharField(max_length=50)
    quantity = serializers.IntegerField()

class OrderItemDetailSerializer(serializers.ModelSerializer):
    product_id = serializers.CharField(source='product.product_id')
    product_name = serializers.CharField(source='product.name')

    class Meta:
        model = OrderItem
        fields = ['product_id', 'product_name', 'quantity', 'unit_price']

class OrderCreateSerializer(serializers.Serializer):
    customerId = serializers.CharField(source='customer_id')
    items = OrderItemInputSerializer(many=True)
    deliveryAddress = serializers.CharField(source='delivery_address')

class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemDetailSerializer(many=True, read_only=True)
    customerId = serializers.CharField(source='customer.customer_id')
    paymentStatus = serializers.SerializerMethodField()
    stockReserved = serializers.SerializerMethodField()

# Inside OrderDetailSerializer...

    class Meta:
        model = Order
        fields = [
            'order_id', 
            'customerId', 
            'status', 
            'paymentStatus', 
            'stockReserved', 
            'total_amount', 
            'delivery_address', 
            'order_date',
            'items'
        ]

    @extend_schema_field(serializers.CharField)
    def get_paymentStatus(self, obj):
        latest_payment = obj.payments.last()
        return latest_payment.status if latest_payment else "PENDING"

    @extend_schema_field(serializers.BooleanField)
    def get_stockReserved(self, obj):
        return obj.status not in ['PENDING', 'CANCELLED']