# from django.db import models


# class ArtisanApplication(models.Model):
#     # ARTISAN_TYPES = [
#     #     ('Painter', 'Painter'),
#     #     ('Sculptor', 'Sculptor'),
#     #     ('Woodworker', 'Woodworker'),
#     #     ('Metal Artist', 'Metal Artist'),
#     #     ('Textile Artist', 'Textile Artist'),
#     #     ('Jewelry Maker', 'Jewelry Maker'),
#     #     ('Potter', 'Potter'),
#     #     ('Weaver', 'Weaver'),
#     #     ('Glass Artist', 'Glass Artist'),
#     #     ('Other', 'Other'),
#     # ]

#     name = models.CharField(max_length=255)
#     email = models.EmailField()
#     phone_number = models.CharField(max_length=20)
#     years_of_experience = models.PositiveIntegerField()

#     # artisan_type = models.CharField(
#     #     max_length=50,
#     #     choices=ARTISAN_TYPES,
#     #     blank=True,
#     #     null=True
#     # )

#     portfolio = models.URLField(blank=True, null=True)
#     bio = models.TextField(blank=True, null=True)

#     documents = models.FileField(upload_to='artisan_documents/')

#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.name


from django.db import models

STATUS_CHOICES = [
    ("pending", "Pending"),
    ("approved", "Approved"),
    ("rejected", "Rejected"),
]
class ArtisanApplication(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    years_of_experience = models.PositiveIntegerField()
    application_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    portfolio_url = models.URLField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ArtisanDocument(models.Model):
    application = models.ForeignKey(
        ArtisanApplication,
        related_name="documents",
        on_delete=models.CASCADE
    )

    file = models.FileField(upload_to="artisan_documents/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.application.name} document"