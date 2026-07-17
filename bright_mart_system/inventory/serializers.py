from rest_framework import serializers
from inventory.models import Product

class ProductDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'