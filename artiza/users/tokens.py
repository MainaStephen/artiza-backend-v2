# accounts/tokens.py
from django.contrib.auth.tokens import PasswordResetTokenGenerator

activation_token = PasswordResetTokenGenerator()
