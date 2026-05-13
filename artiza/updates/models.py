from django.db import models
from django.conf import settings
from projects.models import ProjectRequest


class ProjectMessage(models.Model):
    MESSAGE_TYPES = [
        ("chat", "Chat Message"),
        ("milestone", "Milestone Update"),
    ]

    project = models.ForeignKey(
        ProjectRequest,
        related_name="messages",
        on_delete=models.CASCADE
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default="chat")

    # Chat
    message = models.TextField(blank=True, null=True)

    # Milestone fields
    note = models.TextField(blank=True, null=True)
    progress_percentage = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    # Moderation fields
    flagged = models.BooleanField(default=False)
    blocked = models.BooleanField(default=False)
    reviewed_by_admin = models.BooleanField(default=False)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    # Client reading
    read_by_client = models.BooleanField(default=False)
    read_by_artisan = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.type.upper()} by {self.sender.full_name} - {self.project}"


class ProjectMessageImage(models.Model):
    message = models.ForeignKey(
        ProjectMessage,
        related_name="images",
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="project_messages/")

    def __str__(self):
        return f"Image for Message {self.message.id}"
