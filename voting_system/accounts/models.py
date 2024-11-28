from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

class Faculty(models.Model):
    name = models.CharField(max_length=100)
    max_winners = models.IntegerField(default=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Faculties"

    def __str__(self):
        return self.name

class User(AbstractUser):
    ROLES = (
        ('voter', 'Voter'),
        ('candidate', 'Candidate'),
        ('admin', 'Administrator'),
    )

    role = models.CharField(max_length=20, choices=ROLES, default='voter')
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True)
    student_id = models.CharField(
        max_length=20,
        unique=True,
        validators=[RegexValidator(r'^\d{8}$', 'Student ID must be 8 digits')]
    )
    phone_number = models.CharField(max_length=15, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['username']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    photo = models.ImageField(upload_to='profile_photos/', blank=True)
    personal_statement = models.TextField(max_length=1000, blank=True)
    campaign_promises = models.TextField(max_length=2000, blank=True)
    is_general_candidate = models.BooleanField(default=False)

    def __str__(self):
        return f"Profile of {self.user.username}"
