# proposals/models.py
from django.db import models
from projects.models import ProjectRequest
from django.conf import settings

class Proposal(models.Model):
    project = models.ForeignKey(ProjectRequest, on_delete=models.CASCADE, related_name='proposals')
    artisan = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='proposals', limit_choices_to={'role': 'artisan'})
    
    proposed_price = models.DecimalField(max_digits=12, decimal_places=2)
    negotiated_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    proposed_date_of_completion = models.DateField(
        null=True,
        blank=True,
        help_text="Temporary field to store converted date"
    )

    note = models.TextField(blank=True, null=True, help_text="Additional notes or details from the artisan")
    is_selected = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('project', 'artisan')
        ordering = ['-created_at']

    def __str__(self):
        return f"Proposal by {self.artisan.full_name} for {self.project.title}"

    # @property
    # def final_price(self):
    #     """Return the negotiated price if available, otherwise proposed price"""
    #     return self.negotiated_price if self.negotiated_price else self.proposed_price

    # def has_negotiation(self):
    #     """Check if this proposal has an associated negotiation"""
    #     return hasattr(self, 'negotiation') and self.negotiation is not None