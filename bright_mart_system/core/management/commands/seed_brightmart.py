import json
import urllib.request
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.db import transaction
from customers.models import Customer
from inventory.models import Product

class Command(BaseCommand):
    help = "Seeds the database with updated, authentic enterprise mock data from an external API."

    def handle(self, *args, **options):
        self.stdout.write("Clearing old data...")
        # Optional: Clear existing data safely if you want a clean slate
        # Customer.objects.all().delete()
        # User.objects.filter(is_superuser=False).delete()

        self.stdout.write("Seeding roles and groups...")
        customer_group, _ = Group.objects.get_or_create(name='Customer')
        staff_group, _ = Group.objects.get_or_create(name='Staff')

# 1. FETCHING & SEEDING USERS & CUSTOMERS FROM API
        self.stdout.write("Fetching customer accounts from external API...")
        
        # Change the 'results' parameter to however many customers you want to fetch
        API_URL = "https://randomuser.me/api/?results=5" 
        
        try:
            with urllib.request.urlopen(API_URL) as response:
                api_data = json.loads(response.read().decode())
                mock_customers = api_data.get("results", [])
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to fetch data from API: {e}"))
            return

        self.stdout.write(f"Processing {len(mock_customers)} customer records...")

        for i, data in enumerate(mock_customers, start=1001):
            email = data["email"]
            # Extract first and last name safely
            first_name = data["name"]["first"]
            last_name = data["name"]["last"]
            full_name = f"{first_name} {last_name}"
            phone = data["phone"]

            with transaction.atomic():
                # Ensure the User exists (username = email)
                user, created = User.objects.get_or_create(
                    username=email,
                    email=email
                )
                if created:
                    user.set_password("SecureMock123!")
                    user.save()
                    user.groups.add(customer_group)

                # Keep your distinct, easily recognizable Seed ID pattern
                seeded_customer_id = f"C-SEED-{i}"

                # Look up by customer_id directly so MySQL knows it's an update, not a duplicate insert
                Customer.objects.update_or_create(
                    customer_id=seeded_customer_id,
                    defaults={
                        "user": user,
                        "name": full_name,
                        "email": email,
                        "phone": phone
                    }
                )

# 2. SEEDING PRODUCTS (Keeping your stable P-SEED pattern)
        self.stdout.write("Seeding product inventory...")
        products_to_seed = [
            {
                "product_id": "P-SEED-100", 
                "sku": "SEED-BRIGHTBOOK-14", 
                "name": "BrightBook 14 Laptop (Test)", 
                "price": 899.00, 
                "available_stock": 0
            },
            {
                "product_id": "P-SEED-101", 
                "sku": "SEED-HP-BRIGHTVIEW-14", 
                "name": "BrightView-14 (Test)", 
                "price": 578.18, 
                "available_stock": 1
            },
            {
                "product_id": "P-SEED-200", 
                "sku": "SEED-BRIGHTPHONE-S", 
                "name": "BrightPhone S (Test)", 
                "price": 499.99, 
                "available_stock": 15
            },
        ]

        for prod in products_to_seed:
            Product.objects.update_or_create(
                product_id=prod["product_id"],
                defaults={
                    "sku": prod["sku"],
                    "name": prod["name"],
                    "price": prod["price"],
                    "available_stock": prod["available_stock"]
                }
            )
            
        self.stdout.write(self.style.SUCCESS("Database seeded successfully with dynamic API data!"))