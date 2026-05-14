from django.contrib import admin
from .models import ArtisanApplication, ArtisanDocument


class ArtisanDocumentInline(admin.TabularInline):
    model = ArtisanDocument
    extra = 1


@admin.register(ArtisanApplication)
class ArtisanApplicationAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone_number", "years_of_experience", "created_at")
    search_fields = ("name", "email", "phone_number")
    inlines = [ArtisanDocumentInline]


@admin.register(ArtisanDocument)
class ArtisanDocumentAdmin(admin.ModelAdmin):
    list_display = ("application", "file", "uploaded_at")
    search_fields = ("application__name",)