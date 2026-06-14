/* ARIA v3 — Service Worker (Phase 2: Offline-First PWA)
 *
 * Strategy matrix:
 *   Shell assets (HTML, fonts, same-origin) → Cache-first, fallback to network, store on miss
 *   Humanitarian APIs (HDX, ReliefWeb)      → Network-first, fallback to cache; failed writes → IndexedDB outbox
 *   Anthropic AI API                        → Network-only (responses must be fresh); failed calls → outbox
 *
 * Background Sync tag: 'aria-outbox-sync'
 * Update signal:       postMessage({ type: 'SKIP_WAITING' })
 */

'use strict';

const SHELL_CACHE = 'aria-v3-shell-v1';
const DATA_CACHE  = 'aria-v3-data-v1';
const OUTBOX_DB   = 'aria-outbox';
const OUTBOX_STORE = 'requests';

const SHELL_ASSETS = [
  './aria-v3-p2.html',
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap',
];

// Origins that use network-first strategy (humanitarian data APIs)
const DATA_ORIGINS = [
  'data.humdata.org',
  'api.reliefweb.int',
];

// Origins that are always network-only (no caching, but outbox on failure)
const AI_ORIGINS = [
  'api.anthropic.com',
];

/* ── INSTALL ─────────────────────────────────────────────────────────────── */

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(SHELL_CACHE)
      .then(cache => cache.addAll(SHELL_ASSETS))
      .catch(err => console.warn('[ARIA SW] Shell cache partial failure:', err))
  );
});

/* ── ACTIVATE ────────────────────────────────────────────────────────────── */

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys
          .filter(k => k !== SHELL_CACHE && k !== DATA_CACHE)
          .map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

/* ── FETCH ───────────────────────────────────────────────────────────────── */

self.addEventListener('fetch', event => {
  const { request } = event;
  if (request.method !== 'GET' && request.method !== 'POST') return;

  const url = new URL(request.url);

  // AI API — network-only, queue failed POSTs in outbox
  if (AI_ORIGINS.some(o => url.hostname.includes(o))) {
    if (request.method === 'POST') {
      event.respondWith(networkOnlyWithOutbox(request));
    }
    return;
  }

  // Humanitarian data APIs — network-first with cache fallback
  if (DATA_ORIGINS.some(o => url.hostname.includes(o))) {
    event.respondWith(networkFirst(request));
    return;
  }

  // Everything else (shell, fonts, same-origin) — cache-first
  event.respondWith(cacheFirst(request));
});

/* ── STRATEGIES ──────────────────────────────────────────────────────────── */

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;

  try {
    const response = await fetch(request);
    if (response.ok && request.method === 'GET') {
      const cache = await caches.open(SHELL_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    return offlineFallback(request);
  }
}

async function networkFirst(request) {
  try {
    const response = await fetch(request.clone());
    if (response.ok) {
      const cache = await caches.open(DATA_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await caches.match(request);
    if (cached) return cached;
    return new Response(JSON.stringify({ offline: true, cached: false }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

async function networkOnlyWithOutbox(request) {
  try {
    const response = await fetch(request.clone());
    return response;
  } catch (err) {
    await addToOutbox(request.clone());
    return new Response(JSON.stringify({ offline: true, queued: true }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

function offlineFallback(request) {
  if (request.headers.get('Accept')?.includes('text/html')) {
    return caches.match('./aria-v3-p2.html').then(r =>
      r || new Response('<h1>ARIA offline</h1><p>Open the app to cache it first.</p>', {
        headers: { 'Content-Type': 'text/html' },
      })
    );
  }
  return new Response('Offline', { status: 503 });
}

/* ── INDEXEDDB OUTBOX ────────────────────────────────────────────────────── */

function openOutboxDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(OUTBOX_DB, 1);
    req.onupgradeneeded = e => {
      e.target.result.createObjectStore(OUTBOX_STORE, { autoIncrement: true, keyPath: '_id' });
    };
    req.onsuccess = e => resolve(e.target.result);
    req.onerror = e => reject(e.target.error);
  });
}

async function addToOutbox(request) {
  try {
    let body = '';
    try { body = await request.text(); } catch {}
    const db = await openOutboxDB();
    await new Promise((resolve, reject) => {
      const tx = db.transaction(OUTBOX_STORE, 'readwrite');
      tx.objectStore(OUTBOX_STORE).add({
        url: request.url,
        method: request.method,
        headers: [...request.headers.entries()],
        body,
        timestamp: Date.now(),
      });
      tx.oncomplete = resolve;
      tx.onerror = e => reject(e.target.error);
    });
  } catch (err) {
    console.warn('[ARIA SW] Outbox write failed:', err);
  }
}

async function drainOutbox() {
  const db = await openOutboxDB();
  const items = await new Promise((resolve, reject) => {
    const tx = db.transaction(OUTBOX_STORE, 'readonly');
    const req = tx.objectStore(OUTBOX_STORE).getAll();
    req.onsuccess = e => resolve(e.target.result);
    req.onerror = e => reject(e.target.error);
  });

  for (const item of items) {
    try {
      const headers = new Headers(item.headers);
      const resp = await fetch(item.url, {
        method: item.method,
        headers,
        body: item.body || undefined,
      });
      if (resp.ok) {
        await new Promise((resolve, reject) => {
          const tx = db.transaction(OUTBOX_STORE, 'readwrite');
          tx.objectStore(OUTBOX_STORE).delete(item._id);
          tx.oncomplete = resolve;
          tx.onerror = e => reject(e.target.error);
        });
      }
    } catch {
      break; // Stop on first failure; retry on next sync
    }
  }
}

/* ── BACKGROUND SYNC ─────────────────────────────────────────────────────── */

self.addEventListener('sync', event => {
  if (event.tag === 'aria-outbox-sync') {
    event.waitUntil(drainOutbox());
  }
});

/* ── MESSAGE (skip-waiting trigger) ─────────────────────────────────────── */

self.addEventListener('message', event => {
  if (event.data?.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
