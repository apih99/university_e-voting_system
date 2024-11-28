from django import forms
from django.core.exceptions import ValidationError
from .models import Election, Candidate, Vote
from accounts.models import User

class ElectionForm(forms.ModelForm):
    class Meta:
        model = Election
        fields = ['title', 'description', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date >= end_date:
            raise ValidationError("End date must be after start date")

class CandidateRegistrationForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = ['election']
        widgets = {
            'election': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Only show elections where the user hasn't registered as a candidate
            self.fields['election'].queryset = Election.objects.exclude(
                candidate__user=user
            ).filter(is_active=True)

class VoteForm(forms.Form):
    faculty_candidates = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    general_candidates = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    def __init__(self, *args, **kwargs):
        election = kwargs.pop('election')
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

        # Get faculty candidates (those who are not general candidates)
        self.fields['faculty_candidates'].queryset = Candidate.objects.filter(
            election=election,
            user__faculty=user.faculty,
            approved=True
        ).exclude(user__profile__is_general_candidate=True)

        # Get general candidates
        self.fields['general_candidates'].queryset = Candidate.objects.filter(
            election=election,
            user__profile__is_general_candidate=True,
            approved=True
        )

    def clean(self):
        cleaned_data = super().clean()
        faculty_candidates = cleaned_data.get('faculty_candidates', [])
        general_candidates = cleaned_data.get('general_candidates', [])

        if len(faculty_candidates) > 3:
            raise ValidationError("You can only vote for up to 3 faculty candidates")
        
        if len(general_candidates) > 7:
            raise ValidationError("You can only vote for up to 7 general candidates")

        return cleaned_data

class ResultFilterForm(forms.Form):
    faculty = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="All Faculties"
    )
    show_general_only = forms.BooleanField(required=False, label="Show General Candidates Only")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from accounts.models import Faculty
        self.fields['faculty'].queryset = Faculty.objects.all()
