/**
 * Network status hook for online/offline detection
 */
import { useState, useEffect, useCallback } from 'react';
import { attendanceAPI, gpsAPI } from '../services/api';
import { getPendingSyncCount } from '../services/offline';

export function useNetworkStatus() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [pendingSyncCount, setPendingSyncCount] = useState(0);
  const [isSyncing, setIsSyncing] = useState(false);

  // Update pending sync count
  const updatePendingCount = useCallback(async () => {
    try {
      const count = await getPendingSyncCount();
      setPendingSyncCount(count);
    } catch (error) {
      console.error('[Network] Failed to get pending count:', error);
      setPendingSyncCount(0);
    }
  }, []);

  // Sync pending data
  const syncPendingData = useCallback(async () => {
    if (!navigator.onLine || isSyncing) return;
    
    setIsSyncing(true);
    
    try {
      // Sync clock entries
      await attendanceAPI.syncOfflineEntries();
      
      // Sync GPS logs
      await gpsAPI.batchUpload();
      
      // Update count
      await updatePendingCount();
    } catch (error) {
      console.error('[Network] Sync failed:', error);
    } finally {
      setIsSyncing(false);
    }
  }, [isSyncing, updatePendingCount]);

  // Update online status
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      // Use setTimeout to avoid immediate dependency issues
      setTimeout(() => {
        syncPendingData();
      }, 100);
    };
    
    const handleOffline = () => {
      setIsOnline(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Check pending count on mount
    updatePendingCount();

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [updatePendingCount]); // Only depend on updatePendingCount

  return {
    isOnline,
    pendingSyncCount,
    isSyncing,
    syncPendingData,
    updatePendingCount
  };
}

export default useNetworkStatus;
