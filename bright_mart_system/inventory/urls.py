from django.urls import path
from .views import ProductListCreateAPIView, ProductDetailAPIView, LowStockAlertAPIView

urlpatterns = [
    path('products/', ProductListCreateAPIView.as_view(), name='product-list-create'),
    path('products/low-stock/', LowStockAlertAPIView.as_view(), name='product-low-stock'),
    path('products/<str:product_id>/', ProductDetailAPIView.as_view(), name='product-detail'),
]