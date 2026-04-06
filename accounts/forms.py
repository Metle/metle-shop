from django import forms

from .models import Customer


class CustomerRegistrationForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['full_name', 'email', 'mobile_number', 'language', 'currency']
        widgets = {
            'language': forms.HiddenInput(),
            'currency': forms.HiddenInput(),
        }
