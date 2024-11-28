from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime

from .models import Election, Candidate, Vote, ElectionResult
from .forms import ElectionForm, CandidateRegistrationForm, VoteForm, ResultFilterForm
from accounts.models import Profile

class ElectionListView(ListView):
    model = Election
    template_name = 'elections/election_list.html'
    context_object_name = 'elections'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = datetime.now()
        
        # Get active elections
        context['active_elections'] = Election.objects.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        ).order_by('end_date')
        
        # Get completed elections
        context['completed_elections'] = Election.objects.filter(
            end_date__lt=now
        ).order_by('-end_date')
        
        return context

class ElectionDetailView(DetailView):
    model = Election
    template_name = 'elections/election_detail.html'
    context_object_name = 'election'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        election = self.get_object()
        now = datetime.now()

        context['now'] = now
        context['faculty_candidates'] = election.candidate_set.filter(approved=True, position_type='faculty')
        context['general_candidates'] = election.candidate_set.filter(approved=True, position_type='general')
        context['total_approved_candidates'] = election.candidate_set.filter(approved=True).count()

        if user.is_authenticated:
            context['has_voted'] = Vote.objects.filter(
                voter=user,
                election=election
            ).exists()

            if user.role == 'candidate':
                candidate = Candidate.objects.filter(
                    user=user,
                    election=election
                ).first()
                context['is_candidate'] = bool(candidate)
                context['is_approved'] = candidate.approved if candidate else False

        return context

class ElectionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Election
    form_class = ElectionForm
    template_name = 'elections/election_form.html'
    success_url = reverse_lazy('elections:list')

    def test_func(self):
        return self.request.user.role == 'admin'

    def form_valid(self, form):
        messages.success(self.request, 'Election created successfully!')
        return super().form_valid(form)

class ElectionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Election
    form_class = ElectionForm
    template_name = 'elections/election_form.html'
    success_url = reverse_lazy('elections:list')

    def test_func(self):
        return self.request.user.role == 'admin'

    def form_valid(self, form):
        messages.success(self.request, 'Election updated successfully!')
        return super().form_valid(form)

@login_required
def register_as_candidate(request):
    if request.user.role != 'candidate':
        messages.error(request, 'Only candidates can register for elections.')
        return redirect('elections:list')

    if request.method == 'POST':
        form = CandidateRegistrationForm(request.POST, user=request.user)
        if form.is_valid():
            candidate = form.save(commit=False)
            candidate.user = request.user
            candidate.save()

            # Create or update profile
            profile, created = Profile.objects.get_or_create(user=request.user)
            if not hasattr(profile, 'is_general_candidate'):
                profile.is_general_candidate = False
                profile.save()

            messages.success(request, 'Your candidacy has been registered and is pending approval.')
            return redirect('elections:list')
    else:
        form = CandidateRegistrationForm(user=request.user)

    return render(request, 'elections/candidate_registration.html', {'form': form})

@login_required
def vote_view(request, pk):
    election = get_object_or_404(Election, pk=pk)
    user = request.user
    now = datetime.now()

    # Check if election is active
    if not election.is_active or election.end_date < now:
        messages.error(request, 'This election is not active.')
        return redirect('elections:list')

    # Check if user has already voted
    if Vote.objects.filter(voter=user, election=election).exists():
        messages.error(request, 'You have already voted in this election.')
        return redirect('elections:detail', pk=pk)

    if request.method == 'POST':
        form = VoteForm(request.POST, election=election, user=user)
        if form.is_valid():
            vote = Vote.objects.create(
                voter=user,
                election=election
            )
            vote.faculty_candidates.set(form.cleaned_data['faculty_candidates'])
            vote.general_candidates.set(form.cleaned_data['general_candidates'])

            # Update vote counts
            for candidate in form.cleaned_data['faculty_candidates']:
                candidate.vote_count += 1
                candidate.save()
            for candidate in form.cleaned_data['general_candidates']:
                candidate.vote_count += 1
                candidate.save()

            messages.success(request, 'Your vote has been recorded successfully!')
            return redirect('elections:detail', pk=pk)
    else:
        form = VoteForm(election=election, user=user)

    return render(request, 'elections/vote_form.html', {
        'form': form,
        'election': election
    })

@login_required
def toggle_election_status(request, pk):
    if not request.user.role == 'admin':
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('elections:list')
    
    election = get_object_or_404(Election, pk=pk)
    election.is_active = not election.is_active
    election.save()
    
    status = "activated" if election.is_active else "deactivated"
    messages.success(request, f"Election '{election.title}' has been {status}.")
    return redirect('elections:edit', pk=pk)

@login_required
def end_election(request, pk):
    if request.user.role != 'admin':
        messages.error(request, "You don't have permission to end elections.")
        return redirect('elections:election_list')
    
    election = get_object_or_404(Election, pk=pk)
    
    if request.method == 'POST':
        if election.has_ended():
            messages.warning(request, "This election has already ended.")
        else:
            election.manually_ended = True
            election.save()
            messages.success(request, f"Election '{election.title}' has been ended successfully.")
        return redirect('elections:election_results', pk=election.pk)
    
    return render(request, 'elections/end_election_confirm.html', {'election': election})

@login_required
def election_results(request, pk):
    election = get_object_or_404(Election, pk=pk)
    now = datetime.now()
    
    # Only show results if election has ended or user is admin
    if election.end_date > now and request.user.role != 'admin':
        messages.error(request, 'Results will be available after the election ends.')
        return redirect('elections:detail', pk=pk)

    form = ResultFilterForm(request.GET)
    candidates = Candidate.objects.filter(election=election, approved=True)

    if form.is_valid():
        faculty = form.cleaned_data.get('faculty')
        show_general_only = form.cleaned_data.get('show_general_only')

        if faculty:
            candidates = candidates.filter(user__faculty=faculty)
        if show_general_only:
            candidates = candidates.filter(position_type='general')

    # Get all votes for this election
    votes = Vote.objects.filter(election=election)
    total_voters = votes.count()

    # Initialize result data structure
    result_data = {
        'total_voters': total_voters,
        'faculty_wise_results': {},
        'general_results': [],
        'total_faculty_votes': 0,
        'total_general_votes': 0
    }

    # Process faculty candidates
    faculty_candidates = candidates.filter(position_type='faculty')
    for candidate in faculty_candidates:
        faculty_votes = votes.filter(faculty_candidates=candidate).count()
        result_data['total_faculty_votes'] += faculty_votes
        
        faculty_name = candidate.user.faculty
        if faculty_name not in result_data['faculty_wise_results']:
            result_data['faculty_wise_results'][faculty_name] = []
            
        result_data['faculty_wise_results'][faculty_name].append({
            'candidate': candidate,
            'votes': faculty_votes,
            'percentage': (faculty_votes / total_voters * 100) if total_voters > 0 else 0
        })

    # Process general candidates
    general_candidates = candidates.filter(position_type='general')
    for candidate in general_candidates:
        general_votes = votes.filter(general_candidates=candidate).count()
        result_data['total_general_votes'] += general_votes
        result_data['general_results'].append({
            'candidate': candidate,
            'votes': general_votes,
            'percentage': (general_votes / total_voters * 100) if total_voters > 0 else 0
        })

    # Sort results by votes
    for faculty in result_data['faculty_wise_results']:
        result_data['faculty_wise_results'][faculty].sort(
            key=lambda x: (-x['votes'], x['candidate'].user.get_full_name())
        )
    result_data['general_results'].sort(
        key=lambda x: (-x['votes'], x['candidate'].user.get_full_name())
    )

    return render(request, 'elections/election_results.html', {
        'election': election,
        'result_data': result_data,
        'form': form
    })
