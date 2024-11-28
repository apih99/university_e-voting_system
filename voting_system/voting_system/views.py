from django.views.generic import TemplateView
from elections.models import Election
from django.utils import timezone
from django.db.models import Count

class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        
        # Get active elections
        context['active_elections'] = Election.objects.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        ).order_by('end_date')[:5]
        
        # Get completed elections with vote counts
        completed_elections = Election.objects.filter(
            end_date__lt=now
        ).annotate(
            total_votes=Count('vote')
        ).order_by('-end_date')[:5]
        
        context['completed_elections'] = completed_elections
        return context
