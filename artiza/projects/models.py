from django.db import models
from django.conf import settings

class ProjectRequest(models.Model):

    STATUS_CHOICES = [
        ("open", "Open"),
        ("in-progress", "In Progress"),
        ("completed", "Completed"),
        # ("cancelled", "Cancelled"),
    ]


    artisan = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="assigned_projects",
    limit_choices_to={'role': 'artisan'},)



    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="service_requests",
        limit_choices_to={'role': 'client'},
    )
    title = models.CharField(max_length=255)
    description = models.TextField()

    budget = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=255, blank=True, null=True)
    deadline = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    date_of_completion = models.DateField(blank=True, null=True)  # ⬅️ new field

    def __str__(self):
        return f"{self.title} ({self.client.full_name})"


class ProjectImage(models.Model):
    
    request = models.ForeignKey(ProjectRequest, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="project_images/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.request.title}"



class ReadyMadeProduct(models.Model):

    CATEGORY_CHOICES = [
        ("furniture", "Furniture"),
        ("decor", "Home Decor"),
        ("art", "Art & Crafts"),
        ("clothing", "Clothing"),
        ("other", "Other"),
    ]

    artisan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="products",
        limit_choices_to={'role': 'artisan'}
    )

    name = models.CharField(max_length=255)
    description = models.TextField()

    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=1)

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)

    location = models.CharField(max_length=255, blank=True, null=True)

    is_available = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ProductImage(models.Model):

    product = models.ForeignKey(
        ReadyMadeProduct,
        on_delete=models.CASCADE,
        related_name="images"
    )

    image = models.ImageField(upload_to="ready_made_product_images/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.name}"
