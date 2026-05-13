from django.contrib import admin

from .models import (
    ProjectRequest,
    ProjectImage,
    ReadyMadeProduct,
    ProductImage,
)

from artisanmatching.models import ArtisanMatch


# =========================
# Project Images Inline
# =========================
class RequestImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1

    fields = (
        "image",
        "uploaded_at",
    )

    readonly_fields = (
        "uploaded_at",
    )


# =========================
# Matched Artisans Inline
# =========================
class ArtisanMatchInline(admin.TabularInline):
    model = ArtisanMatch
    extra = 0

    fields = (
        "artisan",
        "matched_at",
    )

    readonly_fields = (
        "artisan",
        "matched_at",
    )

    can_delete = False
    show_change_link = True


# =========================
# Project Request Admin
# =========================
@admin.register(ProjectRequest)
class ServiceRequestAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "title",
        "client",
        "budget",
        "status",
        "created_at",
        "date_of_completion",
    )

    list_filter = (
        "status",
        "created_at",
        "artisan",
    )

    search_fields = (
        "title",
        "description",
        "client__full_name",
        "client__email",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)

    # ADD THIS
    inlines = [
        RequestImageInline,
        ArtisanMatchInline,
    ]

    fieldsets = (
        ("Request Details", {
            "fields": (
                "client",
                "title",
                "description",
                "budget",
                "location",
                "deadline",
                "artisan",
            )
        }),

        ("Status & Metadata", {
            "fields": (
                "status",
                "created_at",
                "updated_at",
                "date_of_completion",
            )
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related("client")


# =========================
# Product Images Inline
# =========================
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

    readonly_fields = (
        "uploaded_at",
    )


# =========================
# Ready Made Product Admin
# =========================
@admin.register(ReadyMadeProduct)
class ReadyMadeProductAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "artisan",
        "category",
        "price",
        "stock",
        "is_available",
        "created_at",
    )

    list_filter = (
        "category",
        "is_available",
        "created_at",
    )

    search_fields = (
        "name",
        "description",
        "artisan__username",
        "location",
    )

    ordering = (
        "-created_at",
    )

    inlines = [
        ProductImageInline,
    ]