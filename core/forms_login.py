# core/forms_login.py
"""
Custom login form for PIN-based authentication
"""
from django import forms
from .models import PortalUser


class PINLoginForm(forms.Form):
    """PIN-based login form with username dropdown."""
    
    username = forms.ChoiceField(
        label='Username',
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg',
            'id': 'id_username'
        })
    )
    pin = forms.CharField(
        max_length=4,
        label='4-Digit PIN',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': '••••',
            'inputmode': 'numeric',
            'maxlength': '4'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically fetch active users for the dropdown
        active_users = PortalUser.objects.filter(is_active=True).order_by('full_name')
        self.fields['username'].choices = [
            (u.username, f"{u.full_name} ({u.get_role_display()})")
            for u in active_users
        ]
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        pin = cleaned_data.get('pin')
        
        if username and pin:
            try:
                user = PortalUser.objects.get(username=username, is_active=True)
                if user.pin_code != str(pin):
                    raise forms.ValidationError("Invalid PIN. Please try again.")
            except PortalUser.DoesNotExist:
                raise forms.ValidationError("User not found.")
        
        return cleaned_data
