from django.contrib import admin
from django.utils import timezone
from .models import ProjectMessage, ProjectMessageImage


@admin.register(ProjectMessage)
class ProjectMessageAdmin(admin.ModelAdmin):
    list_display = (
        "id", "project", "sender", "type",
        "flagged", "blocked", "reviewed_by_admin","progress_percentage"
    )

    list_filter = ("flagged", "blocked", "reviewed_by_admin")

    search_fields = ("message", "sender__full_name")

    fields = (
        "project",
        "sender",
        "type",
        "message",
        "note",
        "progress_percentage",
        "flagged",
        "blocked",
        "reviewed_by_admin",
        "reviewed_at",
        "created_at",
        "read_by_client"
    )

    readonly_fields = ("created_at",)

    def save_model(self, request, obj, form, change):
        if obj.reviewed_by_admin and obj.reviewed_at is None:
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(ProjectMessageImage)
class ProjectMessageImageAdmin(admin.ModelAdmin):
    list_display = ("id", "message", "image")
