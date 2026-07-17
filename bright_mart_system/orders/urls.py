from django.urls import path
from .views import (
    OrderListCreateAPIView, 
    OrderDetailAPIView, 
    OrderCancelAPIView,
    CustomerDetailAPIView,
    ProductDetailAPIView,
    OrderStatusUpdateAPIView
)

urlpatterns = [
    # # Bounded Boundaries Context Targets
    # path('customers/<str:customer_id>/', CustomerDetailAPIView.as_view(), name='customer-detail'),
    # path('products/<str:product_id>/', ProductDetailAPIView.as_view(), name='product-detail'),
    
    # Core Order Processing Pipeline Engine
    path('orders/', OrderListCreateAPIView.as_view(), name='order-list-create'),
    path('orders/<str:order_id>/', OrderDetailAPIView.as_view(), name='order-detail'),
    path('orders/<str:order_id>/status/', OrderStatusUpdateAPIView.as_view(), name='order-status-update'),
    path('orders/<str:order_id>/cancel/', OrderCancelAPIView.as_view(), name='order-cancel'),
]