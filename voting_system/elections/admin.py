from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.db.models import Count
from .models import Election, Candidate, Vote, ElectionResult
from accounts.models import Faculty

User = get_user_model()

class CandidateAdminForm(forms.ModelForm):
    # Add form fields for user creation
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    faculty = forms.ModelChoiceField(
        queryset=Faculty.objects.all(),
        required=False,
        empty_label="(No faculty)"
    )

    class Meta:
        model = Candidate
        fields = ['election', 'position_type', 'manifesto', 'photo', 'approved']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.user:  # If editing existing candidate
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            if hasattr(self.instance.user, 'faculty'):
                self.fields['faculty'].initial = self.instance.user.faculty

@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'is_active', 'has_ended', 'total_candidates', 'total_votes', 'actions_buttons')
    list_filter = ('is_active', 'start_date', 'end_date')
    search_fields = ('title', 'description')
    date_hierarchy = 'start_date'
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Election Information', {
            'fields': ('title', 'description')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date')
        }),
        ('Status', {
            'fields': ('is_active',)
        })
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _total_candidates=Count('candidate', distinct=True),
            _total_votes=Count('vote', distinct=True)
        )
        return queryset

    def status_badge(self, obj):
        now = timezone.now()
        if not obj.is_active:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">Inactive</span>'
            )
        elif obj.start_date > now:
            return format_html(
                '<span style="background-color: #ffc107; color: black; padding: 3px 10px; border-radius: 3px;">Pending</span>'
            )
        elif obj.end_date < now:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">Completed</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #007bff; color: white; padding: 3px 10px; border-radius: 3px;">Active</span>'
            )
    status_badge.short_description = 'Status'

    def total_candidates(self, obj):
        return obj._total_candidates
    total_candidates.admin_order_field = '_total_candidates'

    def total_votes(self, obj):
        return obj._total_votes
    total_votes.admin_order_field = '_total_votes'

    def actions_buttons(self, obj):
        buttons = []
        
        # View Results button
        results_url = reverse('admin:elections_electionresult_changelist')
        buttons.append(f'<a class="button" href="{results_url}?election__id__exact={obj.id}">View Results</a>')
        
        # Manage Candidates button
        candidates_url = reverse('admin:elections_candidate_changelist')
        buttons.append(f'<a class="button" href="{candidates_url}?election__id__exact={obj.id}">Manage Candidates</a>')
        
        return format_html('&nbsp;'.join(buttons))
    actions_buttons.short_description = 'Actions'

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    form = CandidateAdminForm
    list_display = ('get_full_name', 'election', 'position_type', 'approved', 'vote_count')
    list_filter = ('approved', 'position_type', 'election')
    search_fields = ('user__first_name', 'user__last_name', 'user__email')
    
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}" if obj.user else ""
    get_full_name.short_description = 'Name'

    def save_model(self, request, obj, form, change):
        if not change:  # Creating new candidate
            # Create or get user
            user_data = {
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'email': form.cleaned_data['email'],
                'role': 'candidate'
            }
            
            # Try to get existing user or create new one
            user, created = User.objects.get_or_create(
                email=form.cleaned_data['email'],
                defaults=user_data
            )
            
            if not created:
                # Update existing user
                for key, value in user_data.items():
                    setattr(user, key, value)
                user.save()
            
            # Set faculty if provided
            faculty = form.cleaned_data.get('faculty')
            if faculty and hasattr(User, 'faculty'):
                user.faculty = faculty
                user.save()
            
            obj.user = user
        
        super().save_model(request, obj, form, change)

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('voter', 'election', 'timestamp')
    list_filter = ('election', 'timestamp')
    search_fields = ('voter__email', 'election__title')

@admin.register(ElectionResult)
class ElectionResultAdmin(admin.ModelAdmin):
    list_display = ('election', 'total_voters', 'total_votes_cast', 'generated_at')
    list_filter = ('generated_at',)
    search_fields = ('election__title',)
