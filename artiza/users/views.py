from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from .models import User
from .serializers import (
    CustomTokenObtainPairSerializer,
    RegisterUserSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    UserProfileSerializer,
)
from django.utils import timezone

from rest_framework.views import APIView
from .emails import send_reset_password_email,send_activation_email
from .tokens import activation_token
from .serializers import ArtisanCreateSerializer
from rest_framework.permissions import IsAdminUser
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.encoding import force_bytes


# ✅ JWT Login
class CustomLoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


# ✅ Registration
@api_view(["POST"])
@permission_classes([AllowAny])
def register_client(request):
    serializer = RegisterUserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {
                "message": "Registration successful.",
                # "user": {
                #     "id": user.id,
                #     "email": user.email,
                #     "full_name": user.full_name,
                #     "role": user.role,
                #     "phone_number": user.phone_number
                # },
            },
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class CreateArtisanView(generics.CreateAPIView):
    serializer_class = ArtisanCreateSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        user = serializer.save()  # artisan created inactive
        
        # Create ArtisanProfile for the new artisan
        tier = self.request.data.get('tier', 'bronze')
        ArtisanProfile.objects.create(user=user, tier=tier)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = activation_token.make_token(user)

        # Frontend activation link
        FRONTEND_URL = "https://artiza.co.ke"
        activation_link = f"{FRONTEND_URL}/activate-account/{uid}/{token}/"

        # Send email using your helper
        send_activation_email({"user": user, "activation_url": activation_link})



# from django.db import transaction


# class CreateArtisanView(generics.CreateAPIView):
#     serializer_class = ArtisanCreateSerializer
#     permission_classes = [IsAdminUser]

#     def perform_create(self, serializer):
#         try:
#             with transaction.atomic():
#                 # Create user but do not commit yet
#                 user = serializer.save()  # artisan created inactive

#                 uid = urlsafe_base64_encode(force_bytes(user.pk))
#                 token = activation_token.make_token(user)

#                 FRONTEND_URL = "http://146.190.52.91"
#                 activation_link = f"{FRONTEND_URL}/activate-account/{uid}/{token}/"

#                 # Send email synchronously
#                 # Raise exception if sending fails
#                 send_activation_email({"user": user, "activation_url": activation_link})

#         except Exception as e:
#             # Log the error if needed
#             print("Error sending activation email:", e)
#             # Re-raise to ensure DRF returns 500
#             raise




class ActivateAccountView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"error": "Invalid activation link."}, status=400)

        if not activation_token.check_token(user, token):
            return Response({"error": "Activation link expired or invalid."}, status=400)

        if user.is_active:
            return Response({"message": "Account already activated."}, status=200)

        agree_to_terms = request.data.get("agree_to_terms")
        if agree_to_terms is not True:
            return Response(
                {"error": "You must agree to the Terms & Conditions to activate your account."},
                status=400,
            )

        password = request.data.get("password")
        password2 = request.data.get("password2", password)  # optional: confirm password field

        if not password:
            return Response({"error": "Password is required."}, status=400)

        if password != password2:
            return Response({"error": "Passwords do not match."}, status=400)

        # ✅ Set the password properly
        user.set_password(password)
        user.is_active = True
        user.agree_to_terms = True
        user.terms_accepted_at = timezone.now()
        user.save()

        return Response({"message": "Account activated successfully!"}, status=200)



# ✅ Request password reset
class PasswordResetView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].lower()
        user = User.objects.filter(email=email).first()

        if user:
            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            # reset_url = f"http://localhost:3000/reset-password/{uidb64}/{token}/"
            reset_url = f"https://artiza.co.ke/reset-password/{uidb64}/{token}/"
            send_reset_password_email({"user": user, "reset_url": reset_url})

        return Response(
            {"message": "If this email is registered, a reset link has been sent."},
            status=status.HTTP_200_OK,
        )


# ✅ Confirm new password
class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"error": "Invalid or expired link."}, status=400)

        if not PasswordResetTokenGenerator().check_token(user, token):
            return Response({"error": "Token invalid or expired."}, status=400)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user.set_password(serializer.validated_data["new_password1"])
        user.save()

        return Response({"message": "Password reset successful."}, status=200)



class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        
        return self.request.user
    
    
    
    
    
    


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from .models import User, ArtisanProfile

class UserManagementView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role != "admin":
            return Response({"detail": "Access denied."}, status=403)

        users = User.objects.all().select_related('artisan_profile')

        total_users = users.count()
        artisans = users.filter(role="artisan").count()
        clients = users.filter(role="client").count()

        # Initialize tier counts
        bronze_count = 0
        silver_count = 0
        gold_count = 0
      

        user_list = []

        for u in users:
            tier = None
            
            # Get tier for artisan users
            if u.role == "artisan":
                # Check if artisan profile exists using try/except
                try:
                    # Try to get the existing profile
                    artisan_profile = ArtisanProfile.objects.get(user=u)
                    tier = artisan_profile.tier
                except ArtisanProfile.DoesNotExist:
                    # Only create if it doesn't exist
                    artisan_profile = ArtisanProfile.objects.create(
                        user=u, 
                        tier='bronze'
                    )
                    tier = 'bronze'
                
                # Count tiers (only if we have a tier)
                if tier == 'bronze':
                    bronze_count += 1
                elif tier == 'silver':
                    silver_count += 1
                elif tier == 'gold':
                    gold_count += 1
               

            user_list.append({
                "id": u.id,
                "name": u.full_name,
                "email": u.email,
                "role": u.role,
                "tier": tier,
                "status": "active" if u.is_active else "inactive",
                "created_at": u.date_joined.strftime("%Y-%m-%d"),
                "phone": u.phone_number,
            })

        response_data = {
            "total_users": total_users,
            "artisan_count": artisans,
            "client_count": clients,
            "bronze_count": bronze_count,
            "silver_count": silver_count,
            "gold_count": gold_count,
            "users": user_list
        }

        return Response(response_data)
    
        
# users/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from .models import UserProfile

class UserAddressView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        return Response({
            "email": request.user.email,
            "last_shipping_address": profile.last_shipping_address,
            "last_phone_number": profile.last_phone_number
        })
        
class UserReadyProductsPaymentStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "email": user.email,
            "has_paid_ready_products": user.has_paid_ready_products
        })
        
        
        
        
       
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.shortcuts import get_object_or_404
from .models import User, ArtisanProfile

class UpdateArtisanTierView(APIView):
    permission_classes = [permissions.IsAdminUser]  # Only admins can update tiers

    def patch(self, request, user_id):
        artisan = get_object_or_404(User, id=user_id, role='artisan')
        tier = request.data.get('tier')
        
        if tier not in ['bronze', 'silver', 'gold']:
            return Response(
                {"error": "Invalid tier. Must be bronze, silver or gold"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create artisan profile
        profile, created = ArtisanProfile.objects.get_or_create(user=artisan)
        profile.tier = tier
        profile.save()
        
        return Response({
            "message": f"Tier updated to {tier} for {artisan.full_name}",
            "tier": tier
        }, status=status.HTTP_200_OK)