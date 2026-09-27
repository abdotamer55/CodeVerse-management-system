/**
 * CodeVerse PWA Service Worker
 * Handles caching strategy for offline support and fast loads
 */

const CACHE_NAME = 'codeverse-v1';
const STATIC_CACHE = 'codeverse-static-v1';
const DYNAMIC_CACHE = 'codeverse-dynamic-v1';

// Core assets to pre-cache on install (app shell)
const PRECACHE_URLS = [
  '/',
  '/student/dashboard',
  '/student/exams',
  '/student/results',
  '/student/notifications',
  '/static/css/variables.css',
  '/static/css/global.css',
  '/static/css/components.css',
  '/static/css/layout.css',
  '/static/css/pages.css',
  '/static/css/responsive.css',
  '/static/js/components.js',
  '/static/js/navigation.js',
  '/static/js/ui.js',
  '/static/js/forms.js',
  '/static/js/main.js',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png',
];

// Routes that should always be fetched from network (dynamic data)
const NETWORK_ONLY_PATTERNS = [
  /\/student\/exams\/\d+\/submit/,
  /\/student\/exams\/\d+\/start/,
  /\/student\/notifications\/\d+\/read/,
  /\/admin\//,
  /\/auth\//,
];

// ─── Install: Pre-cache app shell ─────────────────────────────────────────────
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => {
      console.log('[SW] Pre-caching app shell');
      return cache.addAll(PRECACHE_URLS).catch((err) => {
        console.warn('[SW] Pre-cache failed for some URLs:', err);
      });
    }).then(() => self.skipWaiting())
  );
});

// ─── Activate: Clean old caches ───────────────────────────────────────────────
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys
          .filter((key) => key !== STATIC_CACHE && key !== DYNAMIC_CACHE)
          .map((key) => {
            console.log('[SW] Deleting old cache:', key);
            return caches.delete(key);
          })
      );
    }).then(() => self.clients.claim())
  );
});

// ─── Fetch: Stale-while-revalidate strategy ───────────────────────────────────
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests (POST/PUT/DELETE always go to network)
  if (request.method !== 'GET') return;

  // Skip cross-origin requests
  if (url.origin !== location.origin) return;

  // Network-only for critical dynamic routes
  const isNetworkOnly = NETWORK_ONLY_PATTERNS.some((pattern) => pattern.test(url.pathname));
  if (isNetworkOnly) {
    event.respondWith(fetch(request));
    return;
  }

  // Static assets: Cache-first
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(request).then((cached) => {
        return cached || fetch(request).then((response) => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(STATIC_CACHE).then((cache) => cache.put(request, clone));
          }
          return response;
        });
      })
    );
    return;
  }

  // HTML pages: Network-first with cache fallback
  event.respondWith(
    fetch(request)
      .then((response) => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(DYNAMIC_CACHE).then((cache) => cache.put(request, clone));
        }
        return response;
      })
      .catch(() => {
        return caches.match(request).then((cached) => {
          if (cached) return cached;
          // Return offline page for navigation requests
          if (request.destination === 'document') {
            return caches.match('/student/dashboard') || new Response(
              `<!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="utf-8">
              <meta name="viewport" content="width=device-width, initial-scale=1">
              <title>غير متصل | كودفيرس</title>
              <style>
                body{font-family:Cairo,sans-serif;background:#070c17;color:#e2e8f0;
                display:flex;align-items:center;justify-content:center;min-height:100vh;
                flex-direction:column;gap:1rem;text-align:center;padding:2rem}
                .icon{font-size:64px;margin-bottom:1rem}
                h1{font-size:1.5rem;color:#6366f1}
                p{color:#94a3b8;max-width:320px}
                button{background:#6366f1;color:#fff;border:none;padding:.75rem 2rem;
                border-radius:10px;font-family:inherit;font-size:1rem;cursor:pointer;margin-top:1rem}
              </style></head><body>
              <div class="icon">📡</div>
              <h1>لا يوجد اتصال بالإنترنت</h1>
              <p>يرجى التحقق من اتصالك بالإنترنت والمحاولة مجدداً.</p>
              <button onclick="location.reload()">إعادة المحاولة</button>
              </body></html>`,
              { headers: { 'Content-Type': 'text/html; charset=utf-8' } }
            );
          }
        });
      })
  );
});

// ─── Background Sync (للإرسال لاحقاً عند الاتصال) ───────────────────────────
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-notifications') {
    event.waitUntil(syncNotifications());
  }
});

async function syncNotifications() {
  console.log('[SW] Syncing notifications in background');
}

// ─── Push Notifications (مستقبلاً) ───────────────────────────────────────────
self.addEventListener('push', (event) => {
  if (!event.data) return;
  const data = event.data.json();
  event.waitUntil(
    self.registration.showNotification(data.title || 'كودفيرس', {
      body: data.body || '',
      icon: '/static/icons/icon-192x192.png',
      badge: '/static/icons/icon-72x72.png',
      dir: 'rtl',
      lang: 'ar',
      tag: data.tag || 'codeverse-notif',
      vibrate: [200, 100, 200],
      data: { url: data.url || '/student/notifications' },
    })
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data?.url || '/student/dashboard')
  );
});
