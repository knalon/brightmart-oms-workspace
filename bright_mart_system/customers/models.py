from django.db import models
from django.contrib.auth.models import User

class Customer(models.Model):
    # This guarantees every customer row is bound to a secure Django Auth User
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='customer_profile'
    )
    customer_id = models.CharField(max_length=50, primary_key=True)  # e.g., C-1001
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.customer_id} - {self.name}"