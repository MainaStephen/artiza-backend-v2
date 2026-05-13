from rest_framework import serializers
from .models import Cart, CartItem
from projects.serializers import ReadyMadeProductSerializer
from projects.models import ReadyMadeProduct

class CartItemSerializer(serializers.ModelSerializer):
    product = ReadyMadeProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=ReadyMadeProduct.objects.all(), source='product', write_only=True
    )

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items']
