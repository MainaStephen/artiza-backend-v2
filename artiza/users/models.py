from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from django.conf import settings


# ==============================
#  Custom User Manager
# ==============================
class CustomUserManager(BaseUserManager):
    def create_user(self, email, full_name, phone_number, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")

        email = self.normalize_email(email).lower()

        user = self.model(
            email=email,
            full_name=full_name,
            phone_number=phone_number,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, phone_number="0000000000", **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")

        return self.create_user(
            email=email,
            full_name=full_name,
            phone_number=phone_number,
            password=password,
            **extra_fields
        )


# ==============================
#  User Model
# ==============================
class User(AbstractBaseUser, PermissionsMixin):

    ROLE_CHOICES = [
        ("artisan", "Artisan"),
        ("client", "Client"),
        ("admin", "Admin"),
    ]

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="client")

    profile_picture = models.ImageField(upload_to="profile_pictures/", blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)

    agree_to_terms = models.BooleanField(default=False)
    terms_accepted_at = models.DateTimeField(null=True, blank=True)

    has_paid_ready_products = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    def __str__(self):
        return self.email


# ==============================
#  User Profile
# ==============================
class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    last_shipping_address = models.TextField(blank=True, null=True)
    last_phone_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"Profile ({self.user.email})"


# ==============================
#  Artisan Profile
# ==============================
class ArtisanProfile(models.Model):

    TIER_CHOICES = [
        ("bronze", "Bronze"),
        ("silver", "Silver"),
        ("gold", "Gold"),
        ("premium", "Premium"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="artisan_profile"
    )

    tier = models.CharField(
        max_length=20,
        choices=TIER_CHOICES,
        default="bronze"
    )
    average_rating = models.FloatField(default=0)
    completed_projects = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.full_name} - {self.tier}"