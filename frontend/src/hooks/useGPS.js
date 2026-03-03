/**
 * GPS capture hook with optimized battery usage
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { gpsAPI } from '../services/api';
import { saveGPSLog } from '../services/offline';

export function useGPS(options = {}) {
  const {
    trackingInterval = 300000, // 5 minutes default
    enableHighAccuracy = true,
    timeout = 30000,
    maximumAge = 60000,
    onError = null
  } = options;

  const [position, setPosition] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isTracking, setIsTracking] = useState(false);
  const watchIdRef = useRef(null);
  const intervalRef = useRef(null);

  // Get current position once
  const getCurrentPosition = useCallback(() => {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        const err = new Error('Geolocation not supported');
        setError(err.message);
        reject(err);
        return;
      }

      setLoading(true);
      setError(null);

      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const gpsData = {
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude,
            accuracy_meters: pos.coords.accuracy,
            altitude_meters: pos.coords.altitude,
            speed_mps: pos.coords.speed,
            heading: pos.coords.heading,
            captured_at: new Date().toISOString()
          };
          setPosition(gpsData);
          setLoading(false);
          resolve(gpsData);
        },
        (err) => {
          const errorMsg = getGPSErrorMessage(err);
          setError(errorMsg);
          setLoading(false);
          if (onError) onError(errorMsg);
          reject(new Error(errorMsg));
        },
        {
          enableHighAccuracy,
          timeout,
          maximumAge
        }
      );
    });
  }, [enableHighAccuracy, timeout, maximumAge, onError]);

  // Start continuous tracking
  const startTracking = useCallback(async () => {
    if (!navigator.geolocation) {
      setError('Geolocation not supported');
      return;
    }

    setIsTracking(true);
    setError(null);

    // Get initial position
    try {
      await getCurrentPosition();
    } catch (err) {
      console.warn('[GPS] Initial position failed:', err);
    }

    // Set up interval for periodic updates (battery optimized)
    intervalRef.current = setInterval(async () => {
      try {
        const pos = await getCurrentPosition();
        
        // Log to server or save offline
        try {
          await gpsAPI.logPosition(pos);
        } catch (apiErr) {
          if (!navigator.onLine) {
            await saveGPSLog(pos);
          }
        }
      } catch (err) {
        console.warn('[GPS] Tracking update failed:', err);
      }
    }, trackingInterval);

  }, [getCurrentPosition, trackingInterval]);

  // Stop tracking
  const stopTracking = useCallback(() => {
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }
    
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    
    setIsTracking(false);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopTracking();
    };
  }, [stopTracking]);

  return {
    position,
    error,
    loading,
    isTracking,
    getCurrentPosition,
    startTracking,
    stopTracking
  };
}

// Helper to get user-friendly error messages
function getGPSErrorMessage(error) {
  switch (error.code) {
    case error.PERMISSION_DENIED:
      return 'Location permission denied. Please enable in settings.';
    case error.POSITION_UNAVAILABLE:
      return 'Location unavailable. Please try again.';
    case error.TIMEOUT:
      return 'Location request timed out. Please try again.';
    default:
      return 'Unable to get location.';
  }
}

export default useGPS;
