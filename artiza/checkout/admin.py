from django.contrib import admin
from .models import Order, OrderItem

# Inline for OrderItems inside Order
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price')
    can_delete = False

# Admin for Orders
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_display', 'total', 'is_paid', 'created_at')
    list_filter = ('is_paid', 'created_at')
    search_fields = ('user__email', 'user__full_name', 'shipping_address')
    inlines = [OrderItemInline]

    def user_display(self, obj):
        # Handles custom user models
        if hasattr(obj.user, 'full_name'):
            return obj.user.full_name
        elif hasattr(obj.user, 'email'):
            return obj.user.email
        return f"User #{obj.user.pk}"
    user_display.short_description = 'User'

# Optional: separate admin for OrderItem if you want
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')
    list_filter = ('order',)
    search_fields = ('product__name', 'order__user__email', 'order__user__full_name')
