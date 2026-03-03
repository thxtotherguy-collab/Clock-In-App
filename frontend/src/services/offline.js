/**
 * Offline storage service using IndexedDB
 * Handles pending clock entries and GPS logs when offline
 */

const DB_NAME = 'WFMOffline';
const DB_VERSION = 1;

let dbInstance = null;

export async function initOfflineDB() {
  if (dbInstance) return dbInstance;
  
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    
    request.onerror = () => {
      console.error('[OfflineDB] Failed to open:', request.error);
      reject(request.error);
    };
    
    request.onsuccess = () => {
      dbInstance = request.result;
      console.log('[OfflineDB] Database opened');
      resolve(dbInstance);
    };
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      
      // Pending time entries
      if (!db.objectStoreNames.contains('pendingEntries')) {
        const store = db.createObjectStore('pendingEntries', { keyPath: 'offline_id' });
        store.createIndex('date', 'date', { unique: false });
        store.createIndex('synced', 'synced', { unique: false });
      }
      
      // Pending GPS logs
      if (!db.objectStoreNames.contains('pendingGPS')) {
        db.createObjectStore('pendingGPS', { keyPath: 'id', autoIncrement: true });
      }
      
      // Auth token storage
      if (!db.objectStoreNames.contains('auth')) {
        db.createObjectStore('auth', { keyPath: 'key' });
      }
      
      // Current state cache
      if (!db.objectStoreNames.contains('state')) {
        db.createObjectStore('state', { keyPath: 'key' });
      }
    };
  });
}

// Generate unique offline ID
export function generateOfflineId() {
  return `offline_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// Save pending clock entry
export async function savePendingEntry(entry) {
  const db = await initOfflineDB();
  
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['pendingEntries'], 'readwrite');
    const store = transaction.objectStore('pendingEntries');
    
    const entryWithMeta = {
      ...entry,
      offline_id: entry.offline_id || generateOfflineId(),
      synced: false,
      created_at: new Date().toISOString()
    };
    
    const request = store.put(entryWithMeta);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(entryWithMeta);
  });
}

// Get all pending entries
export async function getPendingEntries() {
  const db = await initOfflineDB();
  
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['pendingEntries'], 'readonly');
    const store = transaction.objectStore('pendingEntries');
    const index = store.index('synced');
    
    try {
      // Use IDBKeyRange for better compatibility
      const request = index.getAll(IDBKeyRange.only(false));
      
      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result || []);
    } catch (error) {
      // Fallback to cursor if getAll with range fails
      const results = [];
      const cursorRequest = index.openCursor(IDBKeyRange.only(false));
      
      cursorRequest.onerror = () => reject(cursorRequest.error);
      cursorRequest.onsuccess = () => {
        const cursor = cursorRequest.result;
        if (cursor) {
          results.push(cursor.value);
          cursor.continue();
        } else {
          resolve(results);
        }
      };
    }
  });
}

// Mark entry as synced
export async function markEntrySynced(offlineId) {
  const db = await initOfflineDB();
  
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['pendingEntries'], 'readwrite');
    const store = transaction.objectStore('pendingEntries');
    const request = store.delete(offlineId);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve();
  });
}

// Save GPS log
export async function saveGPSLog(log) {
  const db = await initOfflineDB();
  
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['pendingGPS'], 'readwrite');
    const store = transaction.objectStore('pendingGPS');
    
    const request = store.add({
      ...log,
      is_offline_captured: true,
      created_at: new Date().toISOString()
    });
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
  });
}

// Get all pending GPS logs
export async function getPendingGPSLogs() {
  const db = await initOfflineDB();
  
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['pendingGPS'], 'readonly');
    const store = transaction.objectStore('pendingGPS');
    const request = store.getAll();
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result || []);
  });
}

// Clear synced GPS logs
export async function clearGPSLogs() {
  const db = await initOfflineDB();
  
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['pendingGPS'], 'readwrite');
    const store = transaction.objectStore('pendingGPS');
    const request = store.clear();
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve();
  });
}

// Save auth token
export async function saveAuthToken(token) {
  const db = await initOfflineDB();
  
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['auth'], 'readwrite');
    const store = transaction.objectStore('auth');
    const request = store.put({ key: 'token', value: token });
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve();
  });
}

// Get auth token
export async function getAuthToken() {
  const db = await initOfflineDB();
  
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['auth'], 'readonly');
    const store = transaction.objectStore('auth');
    const request = store.get('token');
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result?.value);
  });
}

// Clear auth token
export async function clearAuthToken() {
  const db = await initOfflineDB();
  
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['auth'], 'readwrite');
    const store = transaction.objectStore('auth');
    const request = store.delete('token');
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve();
  });
}

// Save current state
export async function saveState(key, value) {
  const db = await initOfflineDB();
  
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['state'], 'readwrite');
    const store = transaction.objectStore('state');
    const request = store.put({ key, value, updated_at: new Date().toISOString() });
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve();
  });
}

// Get saved state
export async function getState(key) {
  const db = await initOfflineDB();
  
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['state'], 'readonly');
    const store = transaction.objectStore('state');
    const request = store.get(key);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result?.value);
  });
}

// Get pending sync count
export async function getPendingSyncCount() {
  const entries = await getPendingEntries();
  const gpsLogs = await getPendingGPSLogs();
  return entries.length + gpsLogs.length;
}

// Request background sync
export async function requestSync(tag = 'sync-clock-entries') {
  if ('serviceWorker' in navigator && 'sync' in window.registration) {
    try {
      await navigator.serviceWorker.ready;
      await window.registration.sync.register(tag);
      console.log(`[OfflineDB] Sync registered: ${tag}`);
    } catch (error) {
      console.log('[OfflineDB] Background sync not supported');
    }
  }
}
