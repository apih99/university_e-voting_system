"""
voting_system URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import HomeView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('admin/', admin.site.urls),
    # First include allauth URLs
    path('accounts/', include('allauth.urls')),
    # Then include our custom accounts URLs
    path('accounts/', include('accounts.urls')),
    path('elections/', include('elections.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
