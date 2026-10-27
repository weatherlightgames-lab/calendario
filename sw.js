// Service worker mínimo: abre sempre a versão mais recente (rede primeiro) e mostra a última guardada se não houver rede.
const C = 'wl-v1';
self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET' || new URL(e.request.url).origin !== location.origin) return;
  e.respondWith(fetch(e.request).then(r => { const c = r.clone(); caches.open(C).then(k => k.put(e.request, c)); return r; })
    .catch(() => caches.match(e.request)));
});
