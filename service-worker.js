const CACHE = 'concertdate-pwa-20260907-filter-state';
const STATIC_FILES = [
  './',
  './index.html',
  './manifest.webmanifest',
  './assets/data-version-loader-35a57b9e.js',
  './assets/app-a14c9f11.js',
  './assets/filter-state-7b6e21c4.js',
  './assets/styles-91563071.css',
  './assets/calendar-interactions-1fce7c87.js',
  './assets/calendar-interactions-f3a7c2d1.css',
  './assets/apple-touch-icon-ba816ddb.png',
  './assets/icon-192-ba816ddb.png'
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

  event.respondWith(caches.match(event.request).then(cached => cached || fetch(event.request)));
});
