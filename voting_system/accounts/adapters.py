from django.conf import settings
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib import messages
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        """
        This is called when saving user via allauth registration.
        We override this to set additional data on user object.
        """
        try:
            # Get additional data from the form
            user = super().save_user(request, user, form, commit=False)
            
            # Set custom fields from the form
            if hasattr(form, 'cleaned_data'):
                user.student_id = form.cleaned_data.get('student_id')
                user.faculty = form.cleaned_data.get('faculty')
                user.role = 'voter'  # Set default role
            
            if commit:
                user.save()
            
            return user
            
        except Exception as e:
            logger.error(f"Error in save_user adapter: {str(e)}")
            raise ValidationError("An error occurred during registration. Please try again.")

    def is_open_for_signup(self, request):
        """
        We override this to check if registration is currently allowed.
        """
        try:
            # Check if registration is enabled in settings
            allow_signups = getattr(settings, 'ACCOUNT_ALLOW_SIGNUPS', True)
            return allow_signups
        except Exception as e:
            logger.error(f"Error checking signup status: {str(e)}")
            return False

    def clean_username(self, username):
        """
        Override the default username validation to add custom rules.
        """
        username = super().clean_username(username)
        if len(username) < 5:
            raise ValidationError("Username must be at least 5 characters long.")
        return username

    def clean_email(self, email):
        """
        Override the default email validation to add custom rules.
        """
        email = super().clean_email(email)
        # Add custom email validation if needed
        return email

    def respond_email_verification_sent(self, request, user):
        """
        Override the default email verification sent response.
        """
        try:
            messages.info(request, 
                "Thanks for signing up! Please check your email for verification.")
        except Exception as e:
            logger.error(f"Error in email verification response: {str(e)}")
