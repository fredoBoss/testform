from django.contrib import admin
from django.urls import include, path

from feedback.views import home

urlpatterns = [
    path('', home, name='home'),
    path('', include('pwa.urls')),
    path('accounts/', include('accounts.urls')),
    path('feedback/', include('feedback.urls')),
    path('admin/', admin.site.urls),
]
