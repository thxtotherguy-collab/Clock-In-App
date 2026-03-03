/* eslint-disable no-restricted-globals */

const CACHE_NAME = 'wfm-worker-v1';
const OFFLINE_URL = '/offline.html';

// Assets to cache immediately
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/offline.html',
  '/manifest.json',
  '/icon-192.png',
  '/icon-512.png'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] Caching static assets');
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});

// Fetch event - network first, fallback to cache
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // API calls - network only, queue if offline
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request).catch(() => {
        // Return offline indicator for API calls
        return new Response(
          JSON.stringify({ offline: true, error: 'Network unavailable' }),
          { headers: { 'Content-Type': 'application/json' } }
        );
      })
    );
    return;
  }

  // Static assets - cache first, network fallback
  event.respondWith(
    caches.match(request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(request).then((response) => {
        // Cache successful responses
        if (response.status === 200) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, responseClone);
          });
        }
        return response;
      }).catch(() => {
        // Return offline page for navigation requests
        if (request.mode === 'navigate') {
          return caches.match(OFFLINE_URL);
        }
        return new Response('Offline', { status: 503 });
      });
    })
  );
});

// Background sync for offline clock entries
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-clock-entries') {
    event.waitUntil(syncClockEntries());
  }
  if (event.tag === 'sync-gps-logs') {
    event.waitUntil(syncGPSLogs());
  }
});

async function syncClockEntries() {
  try {
    const db = await openIndexedDB();
    const entries = await getAllPendingEntries(db);
    
    if (entries.length === 0) return;

    const token = await getStoredToken();
    if (!token) return;

    const response = await fetch('/api/attendance/sync', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(entries)
    });

    if (response.ok) {
      const result = await response.json();
      // Mark synced entries
      for (const synced of result.synced) {
        await markEntrySynced(db, synced.offline_id);
      }
    }
  } catch (error) {
    console.error('[SW] Sync failed:', error);
  }
}

async function syncGPSLogs() {
  try {
    const db = await openIndexedDB();
    const logs = await getAllPendingGPSLogs(db);
    
    if (logs.length === 0) return;

    const token = await getStoredToken();
    if (!token) return;

    const response = await fetch('/api/gps/batch', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ logs })
    });

    if (response.ok) {
      await clearSyncedGPSLogs(db);
    }
  } catch (error) {
    console.error('[SW] GPS sync failed:', error);
  }
}

// IndexedDB helpers
function openIndexedDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('WFMOffline', 1);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('pendingEntries')) {
        db.createObjectStore('pendingEntries', { keyPath: 'offline_id' });
      }
      if (!db.objectStoreNames.contains('pendingGPS')) {
        db.createObjectStore('pendingGPS', { keyPath: 'id', autoIncrement: true });
      }
      if (!db.objectStoreNames.contains('auth')) {
        db.createObjectStore('auth', { keyPath: 'key' });
      }
    };
  });
}

function getAllPendingEntries(db) {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['pendingEntries'], 'readonly');
    const store = transaction.objectStore('pendingEntries');
    const request = store.getAll();
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
  });
}

function getAllPendingGPSLogs(db) {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['pendingGPS'], 'readonly');
    const store = transaction.objectStore('pendingGPS');
    const request = store.getAll();
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
  });
}

function markEntrySynced(db, offlineId) {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['pendingEntries'], 'readwrite');
    const store = transaction.objectStore('pendingEntries');
    const request = store.delete(offlineId);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve();
  });
}

function clearSyncedGPSLogs(db) {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['pendingGPS'], 'readwrite');
    const store = transaction.objectStore('pendingGPS');
    const request = store.clear();
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve();
  });
}

function getStoredToken() {
  return new Promise((resolve) => {
    try {
      const db = indexedDB.open('WFMOffline', 1);
      db.onsuccess = () => {
        const transaction = db.result.transaction(['auth'], 'readonly');
        const store = transaction.objectStore('auth');
        const request = store.get('token');
        request.onsuccess = () => resolve(request.result?.value);
        request.onerror = () => resolve(null);
      };
      db.onerror = () => resolve(null);
    } catch {
      resolve(null);
    }
  });
}

// Push notifications (future)
self.addEventListener('push', (event) => {
  if (event.data) {
    const data = event.data.json();
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: '/icon-192.png',
      badge: '/icon-192.png',
      tag: data.tag || 'wfm-notification'
    });
  }
});
