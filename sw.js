// Service worker de FINANZAS_LM.
// El nombre del caché lleva la versión de la app: al publicar una versión nueva
// cambia el nombre, se descarta el caché viejo y el teléfono deja de quedarse
// pegado en una versión anterior.
const VERSION = 'v28';
const CACHE = 'finanzas-' + VERSION;

// Lo mínimo para que la app abra sin señal.
const SHELL = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icon-192.png',
  './icon-512.png',
  './icon-maskable-512.png',
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(ks => Promise.all(
        ks.filter(k => k.startsWith('finanzas-') && k !== CACHE)
          .map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('message', e => {
  if (e.data === 'skip-waiting') self.skipWaiting();
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);

  // Los datos NUNCA se cachean: el Apps Script siempre va a la red.
  // Si se cachearan, la app mostraría saldos viejos sin avisar.
  if (url.hostname === 'script.google.com' || url.hostname.endsWith('.googleusercontent.com')) return;

  // Documento: red primero, para que una versión nueva entre de inmediato.
  // Sin señal, cae al caché.
  if (req.mode === 'navigate' || url.pathname.endsWith('/') || url.pathname.endsWith('index.html')) {
    e.respondWith(
      fetch(req)
        .then(r => {
          const copia = r.clone();
          caches.open(CACHE).then(c => c.put('./index.html', copia)).catch(() => {});
          return r;
        })
        .catch(() => caches.match('./index.html').then(r => r || caches.match('./')))
    );
    return;
  }

  // Librerías de CDN (Chart.js, pdf.js) y estáticos propios: caché primero,
  // con reposición en segundo plano.
  e.respondWith(
    caches.match(req).then(hit => {
      const red = fetch(req).then(r => {
        if (r && (r.ok || r.type === 'opaque')) {
          const copia = r.clone();
          caches.open(CACHE).then(c => c.put(req, copia)).catch(() => {});
        }
        return r;
      }).catch(() => hit);
      return hit || red;
    })
  );
});
