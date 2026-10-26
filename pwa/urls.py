from django.urls import path
from django.views.decorators.cache import never_cache

from . import views

app_name = 'pwa'

# Mounted at the site root: a service worker's scope is limited to its own path.
urlpatterns = [
    path('sw.js', never_cache(views.ServiceWorkerView.as_view()), name='service-worker'),
    path('manifest.webmanifest', views.ManifestView.as_view(), name='manifest'),
    path('offline/', views.OfflineView.as_view(), name='offline'),
]
