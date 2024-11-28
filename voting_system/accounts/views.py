from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import UpdateView, DetailView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.core.exceptions import ValidationError
import logging
import traceback
from .models import User, Profile
from .forms import ProfileUpdateForm, CandidateProfileForm

logger = logging.getLogger(__name__)

@login_required
def profile_view(request):
    try:
        if request.method == 'POST':
            form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your profile has been updated!')
                return redirect('profile')
        else:
            form = ProfileUpdateForm(instance=request.user.profile)
        
        context = {
            'form': form,
            'user': request.user
        }
        return render(request, 'accounts/profile.html', context)
    except Exception as e:
        logger.error(f"Error in profile_view: {str(e)}\n{traceback.format_exc()}")
        messages.error(request, "An error occurred while updating your profile.")
        return redirect('profile')

class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'accounts/user_detail.html'
    context_object_name = 'viewed_user'

class CandidateProfileView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Profile
    form_class = CandidateProfileForm
    template_name = 'accounts/candidate_profile.html'
    success_url = reverse_lazy('accounts:profile')

    def test_func(self):
        return self.request.user.role == 'candidate'

    def get_object(self):
        return self.request.user.profile

    def form_valid(self, form):
        try:
            messages.success(self.request, 'Your candidate profile has been updated!')
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error in CandidateProfileView form_valid: {str(e)}\n{traceback.format_exc()}")
            messages.error(self.request, "An error occurred while updating your candidate profile.")
            return redirect('accounts:profile')

@login_required
def dashboard_view(request):
    try:
        context = {
            'user': request.user,
        }
        if request.user.role == 'voter':
            # Add voter-specific data
            context['votes'] = request.user.vote_set.all()
        elif request.user.role == 'candidate':
            # Add candidate-specific data
            context['elections'] = request.user.candidate_set.all()
        elif request.user.role == 'admin':
            # Add admin-specific data
            from elections.models import Election
            context['total_voters'] = User.objects.filter(role='voter').count()
            context['total_candidates'] = User.objects.filter(role='candidate').count()
            context['active_elections'] = Election.objects.filter(is_active=True).count()
        
        return render(request, 'accounts/dashboard.html', context)
    except Exception as e:
        logger.error(f"Error in dashboard_view: {str(e)}\n{traceback.format_exc()}")
        messages.error(request, "An error occurred while loading the dashboard.")
        return redirect('home')

def handle_signup_error(request, error_message):
    """Helper function to handle signup errors"""
    logger.error(f"Signup Error: {error_message}\n{traceback.format_exc()}")
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'error',
            'message': str(error_message)
        }, status=400)
    messages.error(request, str(error_message))
    return redirect('account_signup')
