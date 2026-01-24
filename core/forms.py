from django import forms
from django.contrib.auth.models import User
from .models import Vendor
from .models import Product


class RegisterForm(forms.Form):
    phone = forms.CharField(
        label="Phone Number",
        help_text="Include country code e.g +2348012345678",
        widget=forms.TextInput(attrs={
            'placeholder': '+2348012345678'
        })
    )

    username = forms.CharField()
    business_name = forms.CharField()
    address = forms.CharField()
    country = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean_phone(self):
        phone = self.cleaned_data['phone']

        if not phone.startswith('+'):
            raise forms.ValidationError(
                "Phone number must include country code e.g +234..."
            )

        if len(phone) < 10:
            raise forms.ValidationError("Invalid phone number")

        return phone

class LoginForm(forms.Form):
    phone = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': '+2348012345678'
        })
    )

    password = forms.CharField(widget=forms.PasswordInput)

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'description', 'status']


class ForgotPasswordForm(forms.Form):
    username = forms.CharField()
    phone = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': '+2348012345678'})
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        phone = cleaned_data.get('phone')

        from .models import Vendor

        try:
            user = Vendor.objects.get(user__username=username, phone=phone)
            cleaned_data['vendor'] = user
        except Vendor.DoesNotExist:
            raise forms.ValidationError("No account found with this username and phone number.")

        return cleaned_data
