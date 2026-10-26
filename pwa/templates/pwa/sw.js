{% load static %}// Only static assets and the anonymous offline page are cached. Pages are
// user-specific (and admin pages hold everyone's feedback), so navigations always
// go to the network and are never stored, which keeps one user's data from being
// shown to the next person on a shared device.
const CACHE_NAME = 'feedback-static-{{ cache_version }}';
const OFFLINE_URL = '{% url "pwa:offline" %}';
const STATIC_PREFIX = '{% get_static_prefix %}';
const PRECACHE_URLS = [
  OFFLINE_URL,
  '{% static "css/app.css" %}',
  '{% static "pwa/pwa.js" %}',
  '{% static "icons/icon-48x48.png" %}',
  '{% static "icons/icon-144x144.png" %}',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (request.mode === 'navigate') {
    event.respondWith(fetch(request).catch(() => caches.match(OFFLINE_URL)));
    return;
  }

  if (url.pathname.startsWith(STATIC_PREFIX)) {
    // Stale-while-revalidate: serve from cache, refresh the copy in the background.
    event.respondWith(
      caches.open(CACHE_NAME).then((cache) =>
        cache.match(request).then((cached) => {
          const network = fetch(request).then((response) => {
            if (response.ok) cache.put(request, response.clone());
            return response;
          });
          if (cached) {
            event.waitUntil(network.catch(() => {}));
            return cached;
          }
          return network;
        })
      )
    );
  }
});
