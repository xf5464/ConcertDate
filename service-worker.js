const CACHE = 'concertdate-pwa-app-v1.1.0';
const STATIC_FILES = [
  './',
  './index.html',
  './manifest.webmanifest',
  './assets/data-version-loader-9b3e6f21.js',
  './assets/app-3d9c71a2.js',
  './assets/styles-91563071.css',
  './assets/calendar-interactions-8c2fd1b4.js',
  './assets/calendar-interactions-f3a7c2d1.css',
  './assets/multi-filter-4a76d8c1.css',
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
