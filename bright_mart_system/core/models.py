from django.db import models
from orders.models import Order

class Payment(models.Model):
    payment_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20)  # APPROVED or DECLINED
    transaction_ref = models.CharField(max_length=100)

class Shipment(models.Model):
    shipment_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='shipments')
    carrier = models.CharField(max_length=50, blank=True, null=True)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20)