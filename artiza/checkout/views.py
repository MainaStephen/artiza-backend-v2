from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response
from cart.models import Cart, CartItem
from .models import Order, OrderItem
from users.models import UserProfile


class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        cart, _ = Cart.objects.get_or_create(user=user)

        cart_item_ids = request.data.get("cart_items", [])

        if not cart_item_ids:
            return Response({"error": "No items selected."}, status=400)

        cart_items = CartItem.objects.filter(id__in=cart_item_ids, cart=cart)

        if not cart_items.exists():
            return Response({"error": "Selected items not found in cart."}, status=400)

        profile, _ = UserProfile.objects.get_or_create(user=user)

        shipping_address = request.data.get("shipping_address") or profile.last_shipping_address
        phone_number = request.data.get("phone_number") or profile.last_phone_number

        if not shipping_address or not phone_number:
            return Response(
                {"error": "Shipping address and phone number are required."},
                status=400
            )

        total = sum(item.product.price * item.quantity for item in cart_items)

        order = Order.objects.create(
            user=user,
            shipping_address=shipping_address,
            total=total
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )

            item.product.stock -= item.quantity
            
            if item.product.stock == 0:
                item.product.is_available = False
                
            item.product.save()

            # delete only this item
            item.delete()

        profile.last_shipping_address = shipping_address
        profile.last_phone_number = phone_number
        profile.save()

        return Response({
            "message": "Order placed successfully",
            "order_id": order.id
        }, status=status.HTTP_201_CREATED)
