from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils import timezone
from django.contrib.auth import authenticate
from .models import User, ArtisanProfile
from django.contrib.auth.models import User as DjangoUser


# ---------------------------
# 🔐 Custom JWT Token Serializer
# ---------------------------
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["full_name"] = user.full_name
        token["email"] = user.email
        return token

    def validate(self, attrs):
        email = attrs.get("email").lower().strip()
        password = attrs.get("password")
        user = authenticate(email=email, password=password)

        if not user:
            raise serializers.ValidationError({"error": "Invalid email or password."})

        if not user.is_active:
            raise serializers.ValidationError({"error": "Your account is not activated yet."})

        self.user = user
        data = super().validate(attrs)
        data.update({
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
        })
        return data


# ---------------------------
# 🧍 User Registration Serializer
# ---------------------------
class RegisterUserSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)
    agree_to_terms = serializers.BooleanField(write_only=True)
    phone_number = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = [
            "full_name",
            "phone_number",
            "email",
            "password",
            "password2",
            "role",
            "agree_to_terms",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_agree_to_terms(self, value):
        if not value:
            raise serializers.ValidationError(
                "You must agree to the Terms & Conditions to continue."
            )
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs.get("password2"):
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        agree_to_terms = validated_data.pop("agree_to_terms")

        user = User.objects.create_user(
            email=validated_data["email"],
            full_name=validated_data["full_name"],
            phone_number=validated_data["phone_number"],  
            password=validated_data["password"],
            role="client",
        )

        if agree_to_terms:
            user.agree_to_terms = True
            user.terms_accepted_at = timezone.now()
            user.save()

        return user
    
import secrets
import string

# class ArtisanCreateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ["full_name", "email", "phone_number", "role"]
#         extra_kwargs = {
#             "role": {"default": "artisan"},
#         }

#     def generate_random_password(self, length=12):
#         """Generate a secure random password"""
#         alphabet = string.ascii_letters + string.digits + string.punctuation
#         return ''.join(secrets.choice(alphabet) for _ in range(length))

#     def create(self, validated_data):
#         password = self.generate_random_password()
#         user = User.objects.create_user(
#             full_name=validated_data["full_name"],
#             email=validated_data["email"],
#             phone_number=validated_data["phone_number"],
#             role="artisan",
#             password=password,  # ✅ use generated random password
#             is_active=False,    # artisan inactive until activation
#         )
#         return user

import secrets
import string
from rest_framework import serializers
from .models import User, ArtisanProfile
# In your serializers.py

class ArtisanCreateSerializer(serializers.ModelSerializer):
    tier = serializers.ChoiceField(choices=['bronze', 'silver', 'gold'], default='bronze', write_only=True)
    
    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone_number', 'tier']
    
    def create(self, validated_data):
        tier = validated_data.pop('tier', 'bronze')
        user = User.objects.create_user(
            **validated_data,
            role='artisan',
            is_active=False  # Inactive until email verification
        )
        # Note: ArtisanProfile will be created in the view
        return user   
    
    
# ---------------------------
# 🔁 Password Reset Serializers
# ---------------------------
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("No user with this email exists.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password1 = serializers.CharField(write_only=True, min_length=8)
    new_password2 = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        if attrs["new_password1"] != attrs["new_password2"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs



class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'phone_number', 'profile_picture']
        read_only_fields = ['id', 'email']  # Email usually shouldn't be editable
        
class UserReadyProductsPaymentStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'has_paid_ready_products']
        read_only_fields = ['id', 'full_name', 'email']
        
        
        
 