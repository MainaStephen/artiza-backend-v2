# negotiations/models.py
from django.db import models
from proposals.models import Proposal
from users.models import User

class Negotiation(models.Model):
    proposal = models.OneToOneField(
        Proposal, on_delete=models.CASCADE, related_name="negotiation"
    )
    final_agreed_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pending_final_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Changed from pending_final_offer
    is_closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Add notification fields
    has_unread_client = models.BooleanField(default=False)
    has_unread_artisan = models.BooleanField(default=False)
    last_message_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Negotiation for {self.proposal.project.title}"


class NegotiationMessage(models.Model):
    negotiation = models.ForeignKey(
        Negotiation,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    offer = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False)

    # Read status
    read_by_client = models.BooleanField(default=False)
    read_by_artisan = models.BooleanField(default=False)

    # ⚡ New fields for moderation
    blocked = models.BooleanField(default=False)
    flagged = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender} -> {self.negotiation.proposal.project.title}: {self.message[:30]}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            self.update_negotiation_unread_status()

    def update_negotiation_unread_status(self):
        negotiation = self.negotiation
        if self.sender.role == 'client':
            negotiation.has_unread_artisan = True
        elif self.sender.role == 'artisan':
            negotiation.has_unread_client = True
        negotiation.last_message_time = self.timestamp
        negotiation.save()
