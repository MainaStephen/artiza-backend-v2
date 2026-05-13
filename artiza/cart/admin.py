from django.contrib import admin
from .models import Cart, CartItem

# Inline for CartItem so it shows inside Cart
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0  # don’t show empty extra rows
    readonly_fields = ('product',)  # optional: make product read-only
    can_delete = True

# Admin for Cart
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_items', 'total_price')
    search_fields = ('user__full_name',)
    inlines = [CartItemInline]

    def total_items(self, obj):
        return sum(item.quantity for item in obj.items.all())
    total_items.short_description = 'Total Items'

    def total_price(self, obj):
        return sum(item.product.price * item.quantity for item in obj.items.all())
    total_price.short_description = 'Total Price'

# Admin for CartItem (optional)
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity')
    list_filter = ('cart',)
    search_fields = ('product__name', 'cart__user__full_name')
