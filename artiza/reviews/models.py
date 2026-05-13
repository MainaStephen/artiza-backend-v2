from django.db import models
from django.contrib.auth import get_user_model
from projects.models import ProjectRequest

User = get_user_model()


class Rating(models.Model):
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="ratings_made",
        limit_choices_to={'role': 'client'}
    )

    artisan = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="ratings_received",
        limit_choices_to={'role': 'artisan'}
    )

    project = models.ForeignKey(
        ProjectRequest,
        on_delete=models.CASCADE,
        related_name="ratings"
    )

    score = models.IntegerField()  # 1–5
    review = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("client", "artisan", "project")

    def __str__(self):
        return f"{self.client} rated {self.artisan} {self.score} for {self.project.title}"


class RatingImage(models.Model):
    rating = models.ForeignKey(
        Rating,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to="rating_images/",null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for rating {self.rating.id}"
