# core/auth.py
"""
Custom authentication backend for PIN + Username login
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class PINAuthBackend(ModelBackend):
    """Custom backend for PIN-based authentication."""
    
    def authenticate(self, request, username=None, pin=None, **kwargs):
        """Authenticate using username and 4-digit PIN."""
        try:
            user = User.objects.get(username=username)
            if user.pin_code == str(pin) and user.is_active:
                return user
        except User.DoesNotExist:
            return None
        return None
