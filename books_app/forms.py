from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from django.contrib.auth.models import User
from .models import RequesterProfile, BookRequest, BookAvailable

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    whatsapp_number = forms.CharField(
        max_length=20, 
        label="WhatsApp Number",
        widget=forms.TextInput(attrs={'placeholder': 'e.g., +255712345678'})
    )
    profile_picture = forms.ImageField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = 'Choose a unique username'
        self.fields['email'].widget.attrs['placeholder'] = 'your.email@example.com'
        # Remove default help texts
        self.fields['username'].help_text = None
        self.fields['password2'].help_text = None
        for field in self.fields.values():
            field.help_text = None

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
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'your.email@example.com'})
        }

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = RequesterProfile
        fields = ['whatsapp_number', 'profile_picture']
        widgets = {
            'whatsapp_number': forms.TextInput(attrs={'placeholder': 'e.g., +255712345678'})
        }

class CustomPasswordChangeForm(PasswordChangeForm):
    """A custom password change form to remove help text and add placeholders."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs['placeholder'] = 'Enter your current password'
        self.fields['new_password1'].widget.attrs['placeholder'] = 'Enter your new password'
        self.fields['new_password2'].widget.attrs['placeholder'] = 'Confirm your new password'
        # Remove all help text
        for field in self.fields.values():
            field.help_text = None

class BookRequestForm(forms.ModelForm):
    class Meta:
        model = BookRequest
        fields = ['book_title', 'book_author']
        labels = {
            'book_author': 'Author (Optional)',
        }

class BookUploadForm(forms.ModelForm):
    """
    A form for users to upload new books to the catalog.
    """
    class Meta:
        model = BookAvailable
        fields = ['title', 'author', 'book_file', 'cover_image', 'published_date']
        widgets = {'published_date': forms.DateInput(attrs={'type': 'date'})}

class BookUploadURLForm(forms.ModelForm):
    """
    A form for creating a book entry by providing a URL to the book file.
    """
    book_url = forms.URLField(label="Book URL", widget=forms.URLInput(attrs={'placeholder': 'https://example.com/book.pdf'}))

    class Meta:
        model = BookAvailable
        # 'book_file' is excluded because we're providing a URL instead.
        fields = ['title', 'author', 'cover_image', 'published_date']
        widgets = {'published_date': forms.DateInput(attrs={'type': 'date'})}