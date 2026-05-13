from django.db import models
from django.conf import settings

class ArtisanMatch(models.Model):

   

    project = models.ForeignKey(
        "projects.ProjectRequest",
        on_delete=models.CASCADE,
        related_name="matches"
    )

    artisan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="matched_projects"
    )

    

    matched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("project", "artisan")