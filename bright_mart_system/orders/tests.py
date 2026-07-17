from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from customers.models import Customer
from inventory.models import Product
from orders.models import Order

class BrightMartOrderAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Seed scenario baselines matching the evaluation data model specifications
        self.customer = Customer.objects.create(
            customer_id="C-1001", name="Maya", email="maya@example.com", phone="+9591"
        )
        self.product = Product.objects.create(
            product_id="P-LAP-100", sku="BRIGHTBOOK-14", name="BrightBook 14 Laptop", price=899.00, available_stock=5
        )
        self.create_url = reverse('order-list-create')

    def test_create_order_success_reduces_stock(self):
        """Verify successful order creation updates state and reduces stock counts (BR03, BR04)."""
        payload = {
            "customerId": "C-1001",
            "items": [{"product_id": "P-LAP-100", "quantity": 1}],
            "deliveryAddress": "25 Market Street"
        }
        response = self.client.post(self.create_url, payload, format='json')
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'CONFIRMED')
        self.assertEqual(float(response.data['total_amount']), 899.00)
        
        # Enforce inventory rule check
        self.product.refresh_from_db()
        self.assertEqual(self.product.available_stock, 4)

    def test_create_order_insufficient_stock_fails(self):
        """Verify order requests exceeding stock metrics are blocked with a 409 conflict (BR03)."""
        payload = {
            "customerId": "C-1001",
            "items": [{"product_id": "P-LAP-100", "quantity": 6}],
            "deliveryAddress": "25 Market Street"
        }
        response = self.client.post(self.create_url, payload, format='json')
        self.assertEqual(response.status_code, 409)
        
        # Enforce that stock pool remains unaltered
        self.product.refresh_from_db()
        self.assertEqual(self.product.available_stock, 5)

    def test_order_idempotent_cancellation(self):
        """Verify confirmed orders can restore inventory parameters accurately exactly once (BR08)."""
        # Create order manually via logic pipeline
        payload = {
            "customerId": "C-1001",
            "items": [{"product_id": "P-LAP-100", "quantity": 1}],
            "deliveryAddress": "25 Market Street"
        }
        create_res = self.client.post(self.create_url, payload, format='json')
        order_id = create_res.data['order_id']
        
        cancel_url = reverse('order-cancel', kwargs={'order_id': order_id})
        
        # Hit cancellation action threshold (1st Hit)
        response_1 = self.client.post(cancel_url, format='json')
        self.assertEqual(response_1.status_code, 200)
        self.assertEqual(response_1.data['status'], 'CANCELLED')
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.available_stock, 5) # Stock restored
        
        # Hit execution action thread again to check for multi-add protection (2nd Hit)
        response_2 = self.client.post(cancel_url, format='json')
        self.assertEqual(response_2.status_code, 200)
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.available_stock, 5) # Remains 5, no double inventory ballooning!