from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('profile/', views.profile_view, name='profile'),
    path('profile/candidate/', views.CandidateProfileView.as_view(), name='candidate_profile'),
    path('user/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
]
