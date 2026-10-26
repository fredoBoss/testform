import json

from django.conf import settings
from django.contrib.staticfiles import finders
from django.templatetags.static import static
from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class PWATests(TestCase):
    def test_service_worker_is_served_from_site_root(self):
        # A service worker only controls pages at or below its own path.
        self.assertEqual(reverse('pwa:service-worker'), '/sw.js')

        response = self.client.get('/sw.js')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response['Content-Type'].startswith('application/javascript'))
        self.assertIn('no-cache', response['Cache-Control'])

    def test_manifest_is_valid(self):
        response = self.client.get(reverse('pwa:manifest'))

        manifest = json.loads(response.content)
        self.assertEqual(manifest['start_url'], '/')
        self.assertEqual(manifest['scope'], '/')
        # Chrome needs at least a 192px and a 512px icon to offer installation.
        self.assertLessEqual({'192x192', '512x512'}, {icon['sizes'] for icon in manifest['icons']})
        for icon in manifest['icons']:
            with self.subTest(icon=icon['src']):
                self.assertIsNotNone(finders.find(icon['src'].removeprefix(settings.STATIC_URL)))

    def test_precached_assets_exist(self):
        response = self.client.get('/sw.js')
        for path in ['css/app.css', 'pwa/pwa.js', 'icons/icon-48x48.png', 'icons/icon-144x144.png']:
            with self.subTest(path=path):
                self.assertContains(response, static(path))
                self.assertIsNotNone(finders.find(path))

    def test_offline_page_has_no_user_specific_content(self):
        # The service worker caches this page, so it must not capture whoever installed it.
        self.client.force_login(User.objects.create_user('carol', 'carol@example.com', 'pw'))

        response = self.client.get(reverse('pwa:offline'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'carol')
