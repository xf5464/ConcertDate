const CACHE = 'concertdate-pwa-app-v1.3.0';
const STATIC_FILES = [
  './manifest.webmanifest',
  './assets/data-version-loader-9b3e6f21.js',
  './assets/app-v1.2.0.js',
  './assets/styles-91563071.css',
  './assets/calendar-interactions-8c2fd1b4.js',
  './assets/calendar-interactions-f3a7c2d1.css',
  './assets/multi-filter-9c1d2e77.css',
  './assets/theater-colors-v1.2.0.css',
  './assets/theater-legend-v1.2.1.css',
  './assets/theater-legend-v1.2.1.js',
  './assets/concert-list-v1.2.2.css',
  './assets/concert-list-v1.2.7.css',
  './assets/filter-heights-v1.2.8.css',
  './assets/concert-list-v1.2.4.js',
  './assets/quick-top-b13e7a44.css',
  './assets/quick-top-91d4b2a6.js',
  './assets/apple-touch-icon-piratecat-v1.png',
  './assets/icon-180-piratecat-v1.png'
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(STATIC_FILES)));
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(
    keys
      .filter(key => key.startsWith('concertdate-pwa-') && key !== CACHE)
      .map(key => caches.delete(key))
  )));
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);

  if (url.pathname.endsWith('/data/version.json')) {
    event.respondWith(fetch(event.request, { cache: 'no-store' }));
    return;
  }

  if (url.pathname.endsWith('/data/concerts.json')) {
    event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
    return;
  }

  const isPageNavigation = event.request.mode === 'navigate' || url.pathname.endsWith('/index.html') || url.pathname.endsWith('/ConcertDate/');
  if (isPageNavigation) {
    event.respondWith(
      fetch(event.request, { cache: 'no-store' })
        .then(response => {
          const copy = response.clone();
          caches.open(CACHE).then(cache => cache.put('./index.html', copy));
          return response;
        })
        .catch(async () => (await caches.match('./index.html')) || caches.match('./'))
    );
    return;
  }

  event.respondWith(caches.match(event.request).then(cached => cached || fetch(event.request)));
});
