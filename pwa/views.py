from django.views.generic import TemplateView

# Bump whenever a precached file in templates/pwa/sw.js changes, so clients drop the old cache.
CACHE_VERSION = 'v5'


class ServiceWorkerView(TemplateView):
    template_name = 'pwa/sw.js'
    content_type = 'application/javascript'
    extra_context = {'cache_version': CACHE_VERSION}


class ManifestView(TemplateView):
    template_name = 'pwa/manifest.webmanifest'
    content_type = 'application/manifest+json'


class OfflineView(TemplateView):
    # Precached by the service worker, so it must render identically for every user.
    template_name = 'pwa/offline.html'
