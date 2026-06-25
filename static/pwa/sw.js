const CACHE_NAME = 'furniture-cache-v1';
const urlsToCache = [
  '/',
  '/static/pwa/icon-192.png',
  '/static/pwa/icon-512.png'
  // Добавьте сюда другие ресурсы (CSS, JS), если нужно
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});