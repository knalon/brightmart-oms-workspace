from rest_framework import serializers
from customers.models import Customer

class CustomerDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['customer_id', 'name', 'email', 'phone', 'user']
        # Setting read_only_fields protects the model from accidental writes elsewhere
        read_only_fields = ['customer_id', 'user']