from django.urls import path
from . import views

app_name = 'elections'

urlpatterns = [
    path('', views.ElectionListView.as_view(), name='list'),
    path('create/', views.ElectionCreateView.as_view(), name='create'),
    path('register-candidate/', views.register_as_candidate, name='register_candidate'),
    path('<int:pk>/', views.ElectionDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ElectionUpdateView.as_view(), name='edit'),
    path('<int:pk>/toggle/', views.toggle_election_status, name='toggle_status'),
    path('<int:pk>/end/', views.end_election, name='end_election'),
    path('<int:pk>/results/', views.election_results, name='election_results'),
    path('<int:pk>/vote/', views.vote_view, name='election_vote'),
]
