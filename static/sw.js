// A very basic service worker to make the app installable.

self.addEventListener('install', (event) => {
  console.log('Service Worker: Installed');
});

self.addEventListener('fetch', (event) => {
  // This is a simple pass-through fetch event listener.
  // It's required for the app to be considered a PWA by some browsers.
  event.respondWith(fetch(event.request));
});