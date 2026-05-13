from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer

# class AddToCartView(generics.CreateAPIView):
#     serializer_class = CartItemSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def perform_create(self, serializer):
#         cart, _ = Cart.objects.get_or_create(user=self.request.user)
#         product = serializer.validated_data['product']
#         quantity = serializer.validated_data.get('quantity', 1)

#         # Try to get existing CartItem
#         item = CartItem.objects.filter(cart=cart, product=product).first()

#         if item:
#             # Product already in cart → increase quantity
#             item.quantity += quantity
#             item.save()
#         else:
#             # Product not in cart → create new
#             serializer.save(cart=cart)



from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Cart, CartItem
from .serializers import CartItemSerializer

class AddToCartView(generics.CreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        product = serializer.validated_data['product']
        quantity = serializer.validated_data.get('quantity', 1)

        item = CartItem.objects.filter(cart=cart, product=product).first()

        if item:
            # Increase quantity
            item.quantity += quantity
            item.save()
        else:
            serializer.save(cart=cart, quantity=quantity)



# View cart items
class CartDetailView(generics.RetrieveAPIView):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart

# Remove item from cart
class RemoveFromCartView(generics.DestroyAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = 'pk'

    def get_queryset(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return CartItem.objects.filter(cart=cart)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from .models import Cart, CartItem

class UpdateCartItemQuantity(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        try:
            cart, _ = Cart.objects.get_or_create(user=request.user)

            item = CartItem.objects.get(id=pk, cart=cart)

            quantity = request.data.get("quantity")

            if quantity is None:
                return Response(
                    {"error": "Quantity is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            quantity = int(quantity)

            if quantity < 1:
                return Response(
                    {"error": "Quantity must be at least 1"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if quantity > item.product.stock:
                return Response(
                    {"error": f"Only {item.product.stock} items in stock"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
          

            item.quantity = quantity
            item.save()

            return Response({
                "message": "Cart quantity updated",
                "item_id": item.id,
                "quantity": item.quantity
            })

        except CartItem.DoesNotExist:
            return Response(
                {"error": "Cart item not found"},
                status=status.HTTP_404_NOT_FOUND
            )
