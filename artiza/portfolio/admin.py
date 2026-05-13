from django.contrib import admin
from .models import PortfolioItem,PortfolioProject


admin.site.register(PortfolioProject)

@admin.register(PortfolioItem)
class PortfolioItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "project_title",
        "date_of_completion",
        "created_at",
    )

    list_filter = (
        "created_at",
        "user__role",
        "project_request__date_of_completion",
    )

    search_fields = (
        "user__full_name",
        "project_request__title",
    )

    readonly_fields = (
        "created_at",
        "project_date_of_completion",   # ← ADDED HERE
    )

    # ----- LIST VIEW FIELDS -----
    def project_title(self, obj):
        return obj.project_request.title
    project_title.short_description = "Project"

    def date_of_completion(self, obj):
        return obj.project_request.date_of_completion


    # ----- DETAIL VIEW READ-ONLY FIELD -----
    def project_date_of_completion(self, obj):
        return obj.project_request.date_of_completion
    project_date_of_completion.short_description = "Date of Completion"

    # ----- ADMIN PAGE LAYOUT -----
    fieldsets = (
        (None, {
            "fields": (
                "user",
                "project_request",
                "project_date_of_completion",   # ← SHOWS COMPLETION DATE
                "created_at",
            )
        }),
    )
