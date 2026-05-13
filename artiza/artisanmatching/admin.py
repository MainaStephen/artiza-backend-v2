# artisanmatching/admin.py

from django.contrib import admin
from .models import ArtisanMatch


class ArtisanMatchInline(admin.TabularInline):
    model = ArtisanMatch
    extra = 0

    readonly_fields = (
        "artisan",
        "matched_at",
    )

    fields = (
        "artisan",
        "matched_at",
    )

    can_delete = False
    show_change_link = True