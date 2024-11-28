from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.db import IntegrityError, transaction
from .models import User, Profile, Faculty
from allauth.account.forms import SignupForm
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'student_id', 'faculty')

class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = ('username', 'email', 'student_id', 'faculty')

class CustomSignupForm(SignupForm):
    student_id = forms.CharField(
        max_length=8,
        min_length=8,
        help_text='Enter your 8-digit student ID',
        widget=forms.TextInput(attrs={
            'placeholder': '12345678',
            'pattern': '\\d{8}',
            'title': 'Student ID must be exactly 8 digits'
        })
    )
    faculty = forms.ModelChoiceField(
        queryset=Faculty.objects.all(),
        empty_label="Select your faculty",
        required=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['faculty'].queryset = Faculty.objects.all().order_by('name')
        self.fields['student_id'].label = 'Student ID*'
        self.fields['faculty'].label = 'Faculty*'
        self.fields['email'].required = True
        self.fields['username'].help_text = 'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'

    def clean_student_id(self):
        student_id = self.cleaned_data.get('student_id')
        if not student_id:
            raise forms.ValidationError("Student ID is required.")
        if not student_id.isdigit():
            raise forms.ValidationError("Student ID must contain only digits.")
        if len(student_id) != 8:
            raise forms.ValidationError("Student ID must be exactly 8 digits.")
        
        # Check if student ID is already in use
        if User.objects.filter(student_id=student_id).exists():
            raise forms.ValidationError("This student ID is already registered.")
        
        return student_id

    def clean_faculty(self):
        faculty = self.cleaned_data.get('faculty')
        if not faculty:
            raise forms.ValidationError("Please select your faculty.")
        return faculty

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('username'):
            raise forms.ValidationError("Username is required.")
        if not cleaned_data.get('email'):
            raise forms.ValidationError("Email is required.")
        return cleaned_data

    def save(self, request):
        try:
            with transaction.atomic():
                # First check if student_id is unique again to prevent race conditions
                student_id = self.cleaned_data.get('student_id')
                if User.objects.filter(student_id=student_id).exists():
                    raise forms.ValidationError("This student ID is already registered.")

                # Create the user using the parent class's save method
                user = super().save(request)
                
                # Set additional fields
                user.student_id = student_id
                user.faculty = self.cleaned_data.get('faculty')
                user.role = 'voter'
                user.save()

                # Create the profile if it doesn't exist
                Profile.objects.get_or_create(user=user)
                
                logger.info(f"Successfully created user with student ID: {student_id}")
                return user

        except IntegrityError as e:
            logger.error(f"IntegrityError during signup: {str(e)}")
            raise forms.ValidationError("This student ID or username is already in use.")
        except Exception as e:
            logger.error(f"Error during signup: {str(e)}")
            raise forms.ValidationError(f"An error occurred during registration: {str(e)}")

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'photo']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

class CandidateProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'photo', 'personal_statement', 'campaign_promises', 'is_general_candidate']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'personal_statement': forms.Textarea(attrs={'rows': 6}),
            'campaign_promises': forms.Textarea(attrs={'rows': 8}),
        }
