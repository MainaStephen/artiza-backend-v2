# portfolio/models.py
from django.db import models
from django.conf import settings
from projects.models import ProjectRequest

class PortfolioItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="portfolio_items"
    )
    project_request = models.OneToOneField(
        ProjectRequest,
        on_delete=models.CASCADE,
        related_name="portfolio_item"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.project_request.title} by {self.user.full_name}"

    # Access fields from ProjectRequest
    @property
    def title(self):
        return self.project_request.title

    @property
    def description(self):
        return self.project_request.description

    @property
    def budget(self):
        return self.project_request.budget

    @property
    def location(self):
        return self.project_request.location

    @property
    def date_of_completion(self):
        return self.project_request.date_of_completion

    @property
    def images(self):
        # Returns all images related to the project request
        return self.project_request.images.all()





class PortfolioProject(models.Model):
    artisan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="portfolio_projects"
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    rating = models.FloatField(help_text="Artisan self-assessed or manually added rating (1–5)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.artisan.full_name})"


class PortfolioProjectImage(models.Model):
    project = models.ForeignKey(
        PortfolioProject,
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField(upload_to="portfolio_projects/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.project.title}"
