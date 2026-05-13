from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomLoginView,
    register_client,
    PasswordResetView,
    PasswordResetConfirmView,
    UserProfileView,
    CreateArtisanView,
    ActivateAccountView,
    UserManagementView,
    UserAddressView,
    UserReadyProductsPaymentStatusView,
    UpdateArtisanTierView,  # Add this import
)

urlpatterns = [
    path("register/", register_client, name="register"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("forgot-password/", PasswordResetView.as_view(), name="forgot-password"),
    path("reset/<uidb64>/<token>/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    
    # Admin endpoints
    path("admin/create-artisan/", CreateArtisanView.as_view(), name="create-artisan"),
    path("admin/update-tier/<int:user_id>/", UpdateArtisanTierView.as_view(), name="update-tier"),  # Add this line
    
    # Activation
    path("auth/activate/<uidb64>/<token>/", ActivateAccountView.as_view(), name="activate-account"),
    
    # User management
    path("user-management-data/", UserManagementView.as_view(), name="user-management"),
    
    # User address details in checkout
    path('address-details/', UserAddressView.as_view(), name="address-details"),
    path('ready-products-payment-status/', UserReadyProductsPaymentStatusView.as_view(), name="payment-status"),
]