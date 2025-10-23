from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from .models import RequesterProfile, BookRequest

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    whatsapp_number = forms.CharField(max_length=20, help_text="Required. Full phone number including country code, e.g., +255712345678.")
    profile_picture = forms.ImageField(required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

    def clean_whatsapp_number(self):
        """
        Validate that the WhatsApp number is unique.
        """
        whatsapp_number = self.cleaned_data.get('whatsapp_number')
        if RequesterProfile.objects.filter(whatsapp_number=whatsapp_number).exists():
            raise forms.ValidationError("A profile with this WhatsApp number already exists.")
        return whatsapp_number

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # Create the associated RequesterProfile
            RequesterProfile.objects.create(
                user=user,
                whatsapp_name=user.username,
                whatsapp_number=self.cleaned_data.get('whatsapp_number'),
                profile_picture=self.cleaned_data.get('profile_picture')
            )
        return user

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = RequesterProfile
        fields = ['whatsapp_number', 'profile_picture']

class BookRequestForm(forms.ModelForm):
    class Meta:
        model = BookRequest
        fields = ['book_title', 'book_author']
        labels = {
            'book_author': 'Author (Optional)',
        }

class MyRequestsForm(forms.Form):
    whatsapp_number = forms.CharField(max_length=20, label="Enter Your WhatsApp Number to see your requests", required=True)