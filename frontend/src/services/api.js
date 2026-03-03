/**
 * API service with offline support
 */
import axios from 'axios';
import {
  savePendingEntry,
  getPendingEntries,
  markEntrySynced,
  generateOfflineId,
  saveGPSLog,
  getPendingGPSLogs,
  clearGPSLogs,
  requestSync
} from './offline';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('wfm_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response && !navigator.onLine) {
      // Network error while offline
      error.isOffline = true;
    }
    return Promise.reject(error);
  }
);

// Auth APIs
export const authAPI = {
  login: async (email, password) => {
    const response = await api.post('/api/auth/login', { email, password });
    return response.data;
  },
  
  register: async (data) => {
    const response = await api.post('/api/auth/register', data);
    return response.data;
  },
  
  getMe: async () => {
    const response = await api.get('/api/auth/me');
    return response.data;
  },
  
  refresh: async (refreshToken) => {
    const response = await api.post('/api/auth/refresh', { refresh_token: refreshToken });
    return response.data;
  }
};

// Attendance APIs with offline support
export const attendanceAPI = {
  clockIn: async (data = {}) => {
    const offlineId = generateOfflineId();
    const timestamp = new Date().toISOString();
    
    try {
      if (!navigator.onLine) {
        throw { isOffline: true };
      }
      
      const response = await api.post('/api/attendance/clock-in', {
        ...data,
        offline_id: offlineId
      });
      return { ...response.data, synced: true };
    } catch (error) {
      if (error.isOffline || !navigator.onLine) {
        // Save for offline sync
        const entry = {
          offline_id: offlineId,
          type: 'clock_in',
          date: timestamp.split('T')[0],
          clock_in: {
            timestamp,
            local_time: new Date().toLocaleString(),
            gps: data.gps,
            method: data.method || 'mobile_app'
          },
          job_site_id: data.job_site_id,
          status: 'pending'
        };
        
        await savePendingEntry(entry);
        await requestSync('sync-clock-entries');
        
        return { ...entry, synced: false, offline: true };
      }
      throw error;
    }
  },
  
  clockOut: async (data = {}) => {
    const offlineId = generateOfflineId();
    const timestamp = new Date().toISOString();
    
    try {
      if (!navigator.onLine) {
        throw { isOffline: true };
      }
      
      const response = await api.post('/api/attendance/clock-out', {
        ...data,
        offline_id: offlineId
      });
      return { ...response.data, synced: true };
    } catch (error) {
      if (error.isOffline || !navigator.onLine) {
        // Get pending clock-in entry
        const pendingEntries = await getPendingEntries();
        const activeEntry = pendingEntries.find(e => e.type === 'clock_in' && !e.clock_out);
        
        if (activeEntry) {
          // Update with clock out
          activeEntry.clock_out = {
            timestamp,
            local_time: new Date().toLocaleString(),
            gps: data.gps,
            method: data.method || 'mobile_app'
          };
          activeEntry.break_minutes = data.break_minutes || 0;
          activeEntry.status = 'completed';
          
          // Calculate hours
          const clockIn = new Date(activeEntry.clock_in.timestamp);
          const clockOut = new Date(timestamp);
          const hours = (clockOut - clockIn) / 3600000 - (data.break_minutes || 0) / 60;
          activeEntry.total_hours = Math.max(0, hours.toFixed(2));
          
          await savePendingEntry(activeEntry);
          await requestSync('sync-clock-entries');
          
          return { ...activeEntry, synced: false, offline: true };
        }
        
        throw new Error('No active clock-in found');
      }
      throw error;
    }
  },
  
  getTodayStatus: async () => {
    try {
      if (!navigator.onLine) {
        // Return cached/offline state
        const pendingEntries = await getPendingEntries();
        const today = new Date().toISOString().split('T')[0];
        const todayEntries = pendingEntries.filter(e => e.date === today);
        const activeEntry = todayEntries.find(e => e.clock_in && !e.clock_out);
        
        return {
          is_clocked_in: !!activeEntry,
          current_entry: activeEntry,
          total_hours_today: todayEntries.reduce((sum, e) => sum + (parseFloat(e.total_hours) || 0), 0),
          entries_today: todayEntries.length,
          offline: true
        };
      }
      
      const response = await api.get('/api/attendance/today');
      return response.data;
    } catch (error) {
      // Fallback to offline data
      const pendingEntries = await getPendingEntries();
      const today = new Date().toISOString().split('T')[0];
      const todayEntries = pendingEntries.filter(e => e.date === today);
      const activeEntry = todayEntries.find(e => e.clock_in && !e.clock_out);
      
      return {
        is_clocked_in: !!activeEntry,
        current_entry: activeEntry,
        total_hours_today: todayEntries.reduce((sum, e) => sum + (parseFloat(e.total_hours) || 0), 0),
        entries_today: todayEntries.length,
        offline: true
      };
    }
  },
  
  getWeekSummary: async () => {
    const response = await api.get('/api/attendance/week-summary');
    return response.data;
  },
  
  getHistory: async (params = {}) => {
    const response = await api.get('/api/attendance/history', { params });
    return response.data;
  },
  
  syncOfflineEntries: async () => {
    const pendingEntries = await getPendingEntries();
    if (pendingEntries.length === 0) return { synced: 0, conflicts: 0 };
    
    try {
      const response = await api.post('/api/attendance/sync', pendingEntries);
      
      // Mark synced entries
      for (const synced of response.data.synced) {
        await markEntrySynced(synced.offline_id);
      }
      
      return response.data;
    } catch (error) {
      console.error('[API] Sync failed:', error);
      throw error;
    }
  }
};

// GPS APIs with offline support
export const gpsAPI = {
  logPosition: async (data) => {
    try {
      if (!navigator.onLine) {
        throw { isOffline: true };
      }
      
      const response = await api.post('/api/gps/log', data);
      return response.data;
    } catch (error) {
      if (error.isOffline || !navigator.onLine) {
        await saveGPSLog(data);
        await requestSync('sync-gps-logs');
        return { logged: true, offline: true };
      }
      throw error;
    }
  },
  
  batchUpload: async () => {
    const logs = await getPendingGPSLogs();
    if (logs.length === 0) return { uploaded: 0 };
    
    try {
      const response = await api.post('/api/gps/batch', { logs });
      await clearGPSLogs();
      return response.data;
    } catch (error) {
      console.error('[API] GPS batch upload failed:', error);
      throw error;
    }
  }
};

export default api;
