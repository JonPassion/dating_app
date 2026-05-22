from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, MediaGallery

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'major', 'year', 'interests', 'profile_picture', 'age', 'gender', 'looking_for', 'anonymous_mode', 'hide_from_search']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'interests': forms.Textarea(attrs={'rows': 3, 'placeholder': 'e.g., music, sports, reading, coding'}),
        }

class MediaUploadForm(forms.ModelForm):
    class Meta:
        model = MediaGallery
        fields = ['media_type', 'file', 'caption']
        widgets = {
            'caption': forms.TextInput(attrs={'placeholder': 'Add a caption (optional)'}),
        }
