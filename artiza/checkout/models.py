from django.db import models
from django.conf import settings
from projects.models import ReadyMadeProduct

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_address = models.TextField()
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        if hasattr(self.user, 'full_name'):
            return f"Order #{self.id} by {self.user.full_name}"
        elif hasattr(self.user, 'email'):
            return f"Order #{self.id} by {self.user.email}"
        return f"Order #{self.id}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(ReadyMadeProduct, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # store price at checkout

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
