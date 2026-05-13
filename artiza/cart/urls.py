from django.urls import path
from .views import AddToCartView, CartDetailView, RemoveFromCartView,UpdateCartItemQuantity 

urlpatterns = [
    path('', CartDetailView.as_view(), name='cart-detail'),
    path('add/', AddToCartView.as_view(), name='cart-add'),
    path('remove/<int:pk>/', RemoveFromCartView.as_view(), name='cart-remove'),
    path('update/<int:pk>/', UpdateCartItemQuantity.as_view(), name='update-cart-item'),
]
