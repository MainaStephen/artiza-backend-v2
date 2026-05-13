from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, UserProfile, ArtisanProfile


# =========================
# Artisan Inline
# =========================
class ArtisanProfileInline(admin.StackedInline):
    model = ArtisanProfile
    extra = 0
    can_delete = False
    fk_name = "user"
    max_num = 1


# =========================
# User Admin
# =========================
@admin.register(User)
class UserAdmin(BaseUserAdmin):

    inlines = [ArtisanProfileInline]

    fieldsets = (
        (None, {"fields": ("email", "password")}),

        ("Personal Info", {
            "fields": (
                "full_name",
                "phone_number",
                "profile_picture",
                "address",
                "agree_to_terms",
                "terms_accepted_at",
            )
        }),

        ("Role & Status", {
            "fields": (
                "role",
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),

        ("Payments", {
            "fields": ("has_paid_ready_products",)
        }),

        ("Important Dates", {
            "fields": (
                "last_login",
                "date_joined",
            )
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "full_name",
                "phone_number",
                "role",
                "password1",
                "password2",
            ),
        }),
    )

    list_display = (
        "email",
        "full_name",
        "role",
        "is_active",
        "is_staff",
        "artisan_tier",
    )

    list_filter = ("role", "is_active", "is_staff")

    search_fields = ("email", "full_name", "phone_number")

    ordering = ("email",)

    def artisan_tier(self, obj):
        return getattr(getattr(obj, "artisan_profile", None), "tier", "-")

    artisan_tier.short_description = "Tier"


# =========================
# UserProfile Admin
# =========================
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "last_shipping_address", "last_phone_number")
    search_fields = ("user__email",)


# =========================
# Artisan Profile Admin
# =========================
@admin.register(ArtisanProfile)
class ArtisanProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "tier")
    list_filter = ("tier",)
    search_fields = ("user__email",)
    autocomplete_fields = ["user"]