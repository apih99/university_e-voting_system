from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from datetime import datetime

# Create your models here.

class Election(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    manually_ended = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Collect all validation errors
        errors = {}
        
        # Validate that both dates are provided
        if not self.start_date:
            errors['start_date'] = 'Start date is required'
        if not self.end_date:
            errors['end_date'] = 'End date is required'
            
        # Only proceed with date comparison if both dates are provided
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                errors['end_date'] = 'End date must be after start date'
            
            # Only check if start date is in past for new elections
            if not self.pk and self.start_date < datetime.now():
                errors['start_date'] = 'Start date cannot be in the past'
        
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.title

    def is_ongoing(self):
        now = datetime.now()
        return now >= self.start_date and now < self.end_date and not self.manually_ended

    def has_ended(self):
        return datetime.now() >= self.end_date or self.manually_ended

    def has_started(self):
        now = datetime.now()
        return now >= self.start_date

    class Meta:
        ordering = ['-created_at']

class Candidate(models.Model):
    POSITION_CHOICES = [
        ('faculty', 'Faculty Representative'),
        ('general', 'General Position'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    position_type = models.CharField(max_length=20, choices=POSITION_CHOICES, default='general')
    manifesto = models.TextField(help_text="Candidate's election manifesto and goals", blank=True)
    photo = models.ImageField(upload_to='candidate_photos/', null=True, blank=True)
    approved = models.BooleanField(default=False)
    vote_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['user', 'election']]
        ordering = ['-created_at']

    def clean(self):
        errors = {}
        
        # Check if election is still open for registration
        if self.election.start_date <= datetime.now():
            errors['election'] = 'Cannot register for an election that has already started'
            
        # Check if user is eligible (you may need to adjust this based on your User model)
        if hasattr(self.user, 'faculty') and self.position_type == 'faculty':
            if not self.user.faculty:
                errors['position_type'] = 'User must belong to a faculty to run for faculty representative'
                
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.election.title} ({self.get_position_type_display()})"

class Vote(models.Model):
    voter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    faculty_candidates = models.ManyToManyField(
        Candidate, 
        related_name='faculty_votes',
        limit_choices_to={'user__role': 'candidate'}
    )
    general_candidates = models.ManyToManyField(
        Candidate,
        related_name='general_votes',
        limit_choices_to={'user__role': 'candidate'}
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('voter', 'election')

    def clean(self):
        if self.faculty_candidates.count() > 3:
            raise ValidationError("Cannot vote for more than 3 faculty candidates")
        if self.general_candidates.count() > 7:
            raise ValidationError("Cannot vote for more than 7 general candidates")

    def __str__(self):
        return f"{self.voter.username}'s vote in {self.election.title}"

class ElectionResult(models.Model):
    election = models.OneToOneField(Election, on_delete=models.CASCADE)
    total_voters = models.IntegerField(default=0)
    total_votes_cast = models.IntegerField(default=0)
    result_data = models.JSONField(default=dict)
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Results for {self.election.title}"
