from django.db import models

class Product(models.Model):
    product_id = models.CharField(max_length=50, primary_key=True)  # e.g., P-LAP-100
    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available_stock = models.IntegerField(default=0, null=False) # Enforce literal 0

    def __str__(self):
        return f"{self.sku} - {self.name}"