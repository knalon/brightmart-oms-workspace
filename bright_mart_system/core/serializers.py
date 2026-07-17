from django.contrib.auth.models import User, Group
from django.db import transaction
from rest_framework import serializers
from customers.models import Customer

class ShippingWebhookInputSerializer(serializers.Serializer):
    event = serializers.ChoiceField(choices=['parcel.shipped', 'parcel.delivered'])
    tracking_number = serializers.CharField(max_length=100)
    order_id = serializers.CharField(max_length=50)
    carrier = serializers.CharField(max_length=50, required=False)

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    name = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        # Clean, non-repetitive payload fields for the frontend
        fields = ['email', 'password', 'name', 'phone']

    def create(self, validated_data):
        email = validated_data['email']
        
        with transaction.atomic():
            # 1. Automate username by using the unique email address string
            user = User.objects.create_user(
                username=email, 
                email=email,
                password=validated_data['password']
            )
            
            customer_group, _ = Group.objects.get_or_create(name='Customer')
            user.groups.add(customer_group)
            
            # 2. Automate the customer_id sequence tracking robustly
            # Filter out 'C-SEED-' prefixes to find the highest standard 'C-XXXX' format
            last_customer = Customer.objects.filter(
                customer_id__startswith='C-'
            ).exclude(
                customer_id__contains='SEED'
            ).order_by('-customer_id').first()

            if last_customer:
                try:
                    # Always take the very last element after splitting to catch the number safely
                    parts = last_customer.customer_id.split('-')
                    next_number = int(parts[-1]) + 1
                except (ValueError, IndexError):
                    next_number = 1001
            else:
                next_number = 1001
                
            auto_customer_id = f"C-{next_number}"
            
            # 3. Create the profile record with automated values
            Customer.objects.create(
                user=user,
                customer_id=auto_customer_id,
                name=validated_data['name'],
                email=email,
                phone=validated_data['phone']
            )
            
            return user
        
class StaffRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']

    def create(self, validated_data):
        with transaction.atomic():
            # Create a user with internal staff flags turned on natively
            user = User.objects.create_user(
                username=validated_data['username'],
                email=validated_data.get('email', ''),
                password=validated_data['password'],
                first_name=validated_data.get('first_name', ''),
                last_name=validated_data.get('last_name', ''),
                is_staff=True # Natively grants Django admin rights
            )
            
            # Map them strictly to your Staff group for view protection guards
            staff_group, _ = Group.objects.get_or_create(name='Staff')
            user.groups.add(staff_group)
            
            return user