from django.urls import path
from .views import CustomerListCreateAPIView, CustomerDetailAPIView

urlpatterns = [
    path('customers/', CustomerListCreateAPIView.as_view(), name='customer-list-create'),
    path('customers/<str:customer_id>/', CustomerDetailAPIView.as_view(), name='customer-detail'),
]