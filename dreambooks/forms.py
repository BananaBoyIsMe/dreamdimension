from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import Story, Genre, Chapter, Review

User = get_user_model()

class ChapterForm(forms.ModelForm):
    class Meta:
        model = Chapter
        # adjust field names to match your model:
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Chapter title'}),
            'content': forms.Textarea(attrs={'rows': 12, 'placeholder': 'Write the chapter content here...'}),
        }

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text='Required. Enter a valid email address.')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email')
        if commit:
            user.save()
        return user

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Write your review…'}),
        }

class StoryForm(forms.ModelForm):
    genres = forms.ModelMultipleChoiceField(
        queryset=Genre.objects.none(),  # set in __init__ to avoid import-time issues
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text='Select one or more genres'
    )

    class Meta:
        model = Story
        fields = ['title', 'description', 'cover_image', 'genres']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Story title'}),
            'description': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Short description / blurb'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['genres'].queryset = Genre.objects.all()

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, f"{i} ★") for i in range(1,6)]),
            'comment': forms.Textarea(attrs={'rows':3, 'placeholder':'Write your review...'}),
        }
