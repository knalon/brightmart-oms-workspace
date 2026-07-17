import uuid
from django.db import transaction
from django.core.exceptions import ValidationError
from customers.models import Customer
from inventory.models import Product
from .models import Order, OrderItem

import uuid
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Order, OrderItem
from customers.models import Customer
from inventory.models import Product
from core.models import Payment
from core.services import PaymentGatewayService  # 👈 Make sure to import your new service!

def create_brightmart_order(customer_id: str, items_data: list, delivery_address: str) -> Order:
    """
    Orchestrates order ingestion: coordinates customer verification, server-side 
    pricing rules, atomic inventory isolation, and test billing confirmations (BR01-BR05).
    """
    # BR01: Validate that the order contains items
    if not items_data:
        raise ValidationError("An order must contain at least one item.")

    # Wrap the entire process in an atomic database transaction block
    with transaction.atomic():
        # Verify customer profile exists (CRM adapter placeholder context)
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            raise ValidationError(f"Customer with ID {customer_id} does not exist.")

        total_amount = 0
        order_items_to_create = []

        # 1. Enforce Server-Side Inventory Verification & Calculations
        for item in items_data:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 0)

            # BR01: Validate quantity bounds
            if quantity <= 0:
                raise ValidationError("Requested quantity must be greater than zero.")

            try:
                # select_for_update() locks rows in MySQL until the transaction commits, 
                # preventing concurrent double-selling anomalies
                product = Product.objects.select_for_update().get(pk=product_id)
            except Product.DoesNotExist:
                raise ValidationError(f"Product with ID {product_id} does not exist.")

            # BR03: Enforce available stock limits
            if product.available_stock < quantity:
                raise ValidationError(
                    f"Insufficient stock for {product.name}. Requested: {quantity}, Available: {product.available_stock}"
                )

            # BR04: Reserve stock immediately within the isolation block
            product.available_stock -= quantity
            product.save()

            # BR02 & BR04: Pull official server-side price records and calculate subtotal
            item_total = product.price * quantity
            total_amount += item_total

            order_items_to_create.append({
                'product': product,
                'quantity': quantity,
                'unit_price': product.price
            })

        # Generate a unique order identifier string matching the required scenario structure
        generated_order_id = f"BM-{uuid.uuid4().hex[:6].upper()}"

        # 2. Build the structural baseline order record
        order = Order.objects.create(
            order_id=generated_order_id,
            customer=customer,
            total_amount=total_amount,
            delivery_address=delivery_address,
            status='PENDING'
        )

        # Bulk save order items linked directly to the parent order
        for item_info in order_items_to_create:
            OrderItem.objects.create(
                order=order,
                product=item_info['product'],
                quantity=item_info['quantity'],
                unit_price=item_info['unit_price']
            )

        # 3. Process Third-Party Test Billing Rules (BR05)
        # 🌟 DYNAMIC INTEGRATION: Call our external Payment Gateway Service!
        payment_status, txn_ref = PaymentGatewayService.authorize_payment(
            order_id=generated_order_id,
            amount=total_amount
        )

        if payment_status == 'APPROVED':
            order.status = 'CONFIRMED'
            order.save()

            # Record formal transaction logs to the core module
            Payment.objects.create(
                order=order,
                amount=total_amount,
                status='APPROVED',
                transaction_ref=txn_ref if txn_ref else f"TX-MOCK-{uuid.uuid4().hex[:8].upper()}"
            )
        else:
            # Raising a validation error within transaction.atomic() completely rolls back 
            # all structural writes and returns reserved inventory items back to their initial counts automatically.
            raise ValidationError("Transaction declined by the payment processing terminal.")

        return order

def cancel_brightmart_order(order_id: str) -> Order:
    """
    Handles business logic cancellation gates and performs idempotent 
    inventory restoration processes safely (BR07, BR08).
    """
    with transaction.atomic():
        try:
            # Lock the order instance using select_for_update() to secure state updates
            order = Order.objects.select_for_update().get(pk=order_id)
        except Order.DoesNotExist:
            raise ValidationError(f"Order {order_id} cannot be resolved.")

        # BR07: Restrict actions on orders that have already reached fulfillment pipelines
        if order.status in ['PROCESSING', 'SHIPPED', 'DELIVERED']:
            raise ValidationError(f"Order cannot be cancelled because its current status is {order.status}.")

        # BR08: Idempotency safety path. If the cancellation was already processed, 
        # return the resource gracefully without executing secondary database additions.
        if order.status == 'CANCELLED':
            return order

        # Loop over items to reverse the initial stock allocation
        for item in order.items.all():
            product = Product.objects.select_for_update().get(pk=item.product.pk)
            product.available_stock += item.quantity
            product.save()

        # Update and seal the object state change
        order.status = 'CANCELLED'
        order.save()

        return order
    
def update_order_fulfilment_status(order_id: str, new_status: str) -> Order:
    """
    Enforces the mandatory core status sequence transition gates (BR06, BR10).
    Valid path: PENDING -> CONFIRMED -> PROCESSING -> SHIPPED -> DELIVERED
    """
    VALID_TRANSITIONS = {
        'PENDING': ['CONFIRMED', 'CANCELLED'],
        'CONFIRMED': ['PROCESSING', 'CANCELLED'],
        'PROCESSING': ['SHIPPED'],
        'SHIPPED': ['DELIVERED'],
        'DELIVERED': [],
        'CANCELLED': []
    }

    with transaction.atomic():
        try:
            order = Order.objects.select_for_update().get(pk=order_id)
        except Order.DoesNotExist:
            raise ValidationError(f"Order {order_id} cannot be found.")

        current_status = order.status
        normalized_new_status = new_status.upper()

        # BR10: Validate transition sequence logic
        if normalized_new_status not in VALID_TRANSITIONS.get(current_status, []):
            raise ValidationError(
                f"Invalid state transition. Cannot move order from {current_status} directly to {normalized_new_status}."
            )

        order.status = normalized_new_status
        order.save()
        return order