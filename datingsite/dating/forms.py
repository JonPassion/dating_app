from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, MediaGallery


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    age = forms.IntegerField(required=True, min_value=16, max_value=100)
    gender = forms.ChoiceField(
        required=True,
        choices=[
            ('', 'Select gender'),
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
            ('prefer_not_to_say', 'Prefer not to say'),
        ]
    )
    looking_for = forms.ChoiceField(
        required=True,
        choices=[
            ('', 'Select preference'),
            ('male', 'Male'),
            ('female', 'Female'),
            ('both', 'Both'),
            ('other', 'Other'),
        ]
    )
    major = forms.CharField(max_length=100, required=False)
    year = forms.IntegerField(required=False, min_value=1, max_value=6)
    campus = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'e.g., Main Campus, North Campus'})
    )
    bio = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Tell us a bit about yourself…'})
    )
    profile_picture = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=commit)
        return user


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'bio', 'major', 'year', 'interests', 'profile_picture',
            'age', 'gender', 'looking_for', 'campus',
            'anonymous_mode', 'hide_from_search',
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'interests': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'e.g., music, sports, reading, coding'
            }),
            'campus': forms.TextInput(attrs={
                'placeholder': 'e.g., Main Campus, North Campus, City Campus'
            }),
        }


class MediaUploadForm(forms.ModelForm):
    class Meta:
        model = MediaGallery
        fields = ['media_type', 'file', 'caption']
        widgets = {
            'caption': forms.TextInput(attrs={'placeholder': 'Add a caption (optional)'}),
        }
