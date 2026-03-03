/**
 * Worker Dashboard - Mobile-First Clock Interface
 * 
 * Design: Large buttons, max 2 taps to clock, high contrast, outdoor readable
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Clock, MapPin, Wifi, WifiOff, RefreshCw, Building2, Calendar, Timer } from 'lucide-react';
import { attendanceAPI } from '../services/api';
import { useGPS } from '../hooks/useGPS';
import { useNetworkStatus } from '../hooks/useNetworkStatus';
import { initOfflineDB } from '../services/offline';

export default function WorkerDashboard({ user, onLogout }) {
  const [status, setStatus] = useState(null);
  const [weekSummary, setWeekSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [elapsedTime, setElapsedTime] = useState(null);

  const { position, loading: gpsLoading, error: gpsError, getCurrentPosition, startTracking, stopTracking } = useGPS();
  const { isOnline, pendingSyncCount, isSyncing, syncPendingData } = useNetworkStatus();

  // Load initial data
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [todayStatus, weekData] = await Promise.all([
        attendanceAPI.getTodayStatus(),
        attendanceAPI.getWeekSummary().catch(() => null)
      ]);

      setStatus(todayStatus);
      setWeekSummary(weekData);

      // Start GPS tracking if clocked in
      if (todayStatus.is_clocked_in) {
        startTracking();
      }
    } catch (err) {
      console.error('[Dashboard] Load error:', err);
      setError('Failed to load status');
    } finally {
      setLoading(false);
    }
  }, [startTracking]);

  // Initialize
  useEffect(() => {
    initOfflineDB();
    loadData();
  }, [loadData]);

  // Elapsed time timer
  useEffect(() => {
    if (!status?.is_clocked_in || !status?.current_entry?.clock_in?.timestamp) {
      setElapsedTime(null);
      return;
    }

    const clockInTime = new Date(status.current_entry.clock_in.timestamp);
    
    const updateElapsed = () => {
      const now = new Date();
      const diff = now - clockInTime;
      const hours = Math.floor(diff / 3600000);
      const minutes = Math.floor((diff % 3600000) / 60000);
      const seconds = Math.floor((diff % 60000) / 1000);
      setElapsedTime({ hours, minutes, seconds, total: diff / 3600000 });
    };

    updateElapsed();
    const interval = setInterval(updateElapsed, 1000);
    return () => clearInterval(interval);
  }, [status?.is_clocked_in, status?.current_entry?.clock_in?.timestamp]);

  // Handle Clock In
  const handleClockIn = async () => {
    try {
      setActionLoading(true);
      setError(null);

      // Get GPS position first
      let gpsData = position;
      if (!gpsData) {
        try {
          gpsData = await getCurrentPosition();
        } catch (gpsErr) {
          console.warn('[Dashboard] GPS failed:', gpsErr);
        }
      }

      const result = await attendanceAPI.clockIn({
        gps: gpsData ? {
          latitude: gpsData.latitude,
          longitude: gpsData.longitude,
          accuracy_meters: gpsData.accuracy_meters,
          captured_at: gpsData.captured_at || new Date().toISOString()
        } : null,
        method: 'mobile_app'
      });

      // Start GPS tracking
      startTracking();

      // Update status
      setStatus({
        is_clocked_in: true,
        current_entry: result,
        total_hours_today: status?.total_hours_today || 0,
        entries_today: (status?.entries_today || 0) + 1
      });

      setSuccessMessage(result.offline ? 'Clocked In (Offline)' : 'Clocked In!');
      setTimeout(() => setSuccessMessage(null), 3000);

    } catch (err) {
      console.error('[Dashboard] Clock in error:', err);
      setError(err.response?.data?.detail || 'Clock in failed');
    } finally {
      setActionLoading(false);
    }
  };

  // Handle Clock Out
  const handleClockOut = async () => {
    try {
      setActionLoading(true);
      setError(null);

      // Get GPS position
      let gpsData = position;
      if (!gpsData) {
        try {
          gpsData = await getCurrentPosition();
        } catch (gpsErr) {
          console.warn('[Dashboard] GPS failed:', gpsErr);
        }
      }

      const result = await attendanceAPI.clockOut({
        gps: gpsData ? {
          latitude: gpsData.latitude,
          longitude: gpsData.longitude,
          accuracy_meters: gpsData.accuracy_meters,
          captured_at: gpsData.captured_at || new Date().toISOString()
        } : null,
        method: 'mobile_app',
        break_minutes: 0
      });

      // Stop GPS tracking
      stopTracking();

      // Update status
      setStatus({
        is_clocked_in: false,
        current_entry: null,
        total_hours_today: (status?.total_hours_today || 0) + (result.total_hours || 0),
        entries_today: status?.entries_today || 1
      });

      // Reload week summary
      try {
        const weekData = await attendanceAPI.getWeekSummary();
        setWeekSummary(weekData);
      } catch (e) {}

      setSuccessMessage(result.offline ? 'Clocked Out (Offline)' : `Clocked Out! ${result.total_hours?.toFixed(2) || 0}h`);
      setTimeout(() => setSuccessMessage(null), 3000);

    } catch (err) {
      console.error('[Dashboard] Clock out error:', err);
      setError(err.response?.data?.detail || err.message || 'Clock out failed');
    } finally {
      setActionLoading(false);
    }
  };

  // Format time display
  const formatElapsedTime = () => {
    if (!elapsedTime) return '--:--:--';
    const h = String(elapsedTime.hours).padStart(2, '0');
    const m = String(elapsedTime.minutes).padStart(2, '0');
    const s = String(elapsedTime.seconds).padStart(2, '0');
    return `${h}:${m}:${s}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0A0F1C]">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0A0F1C] flex flex-col" data-testid="worker-dashboard">
      {/* Status Bar */}
      <div className="status-bar">
        <div className="flex items-center gap-2">
          <div className={`connection-dot ${!isOnline ? 'offline' : ''}`}></div>
          <span>{isOnline ? 'Online' : 'Offline'}</span>
        </div>
        <span>{new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}</span>
      </div>

      {/* Sync Indicator */}
      {pendingSyncCount > 0 && (
        <div className="sync-indicator" data-testid="sync-indicator">
          <RefreshCw size={12} className={isSyncing ? 'animate-spin' : ''} />
          {pendingSyncCount} pending
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col items-center px-4 py-6">
        {/* User Greeting */}
        <div className="text-center mb-6">
          <h1 className="text-xl font-semibold text-white">
            Hey, {user?.first_name || 'Worker'}
          </h1>
          <div className="flex items-center justify-center gap-4 mt-2">
            {user?.branch_id && (
              <span className="info-pill">
                <Building2 size={14} />
                {user?.branch?.name || 'Branch'}
              </span>
            )}
          </div>
        </div>

        {/* Status Badge */}
        <div className={`status-badge ${status?.is_clocked_in ? 'clocked-in' : 'clocked-out'}`} data-testid="status-badge">
          <div className={`w-2 h-2 rounded-full ${status?.is_clocked_in ? 'bg-green-500 animate-pulse' : 'bg-gray-500'}`}></div>
          {status?.is_clocked_in ? 'Currently Working' : 'Not Clocked In'}
        </div>

        {/* Timer Display (when clocked in) */}
        {status?.is_clocked_in && (
          <div className="mt-6 text-center">
            <div className="timer-display" data-testid="elapsed-timer">
              {formatElapsedTime()}
            </div>
            <p className="text-sm text-gray-400 mt-1">Time elapsed</p>
          </div>
        )}

        {/* GPS Status */}
        <div className={`gps-status mt-4 ${position ? 'active' : gpsError ? 'error' : ''}`} data-testid="gps-status">
          <MapPin size={14} />
          {gpsLoading ? 'Getting location...' : position ? 'Location captured' : gpsError || 'No location'}
        </div>

        {/* MAIN CLOCK BUTTON */}
        <div className="flex-1 flex items-center justify-center py-8">
          <button
            className={`clock-button ${status?.is_clocked_in ? 'clock-out' : 'clock-in'}`}
            onClick={status?.is_clocked_in ? handleClockOut : handleClockIn}
            disabled={actionLoading}
            data-testid={status?.is_clocked_in ? 'clock-out-button' : 'clock-in-button'}
          >
            {actionLoading ? (
              <div className="spinner mx-auto"></div>
            ) : (
              <>
                <Clock size={40} className="mx-auto mb-2" />
                <span>{status?.is_clocked_in ? 'CLOCK OUT' : 'CLOCK IN'}</span>
              </>
            )}
          </button>
        </div>

        {/* Stats Grid */}
        <div className="w-full max-w-md grid grid-cols-2 gap-4 mt-auto">
          {/* Today Hours */}
          <div className="stat-card" data-testid="today-hours">
            <div className="stat-value">
              {(status?.total_hours_today || 0).toFixed(1)}h
            </div>
            <div className="stat-label">Today</div>
          </div>

          {/* Week Hours */}
          <div className="stat-card" data-testid="week-hours">
            <div className="stat-value">
              {(weekSummary?.total_hours || 0).toFixed(1)}h
            </div>
            <div className="stat-label">This Week</div>
          </div>
        </div>

        {/* Extra Stats */}
        <div className="w-full max-w-md flex justify-between mt-4 px-2">
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <Calendar size={14} />
            <span>{weekSummary?.days_worked || 0} days worked</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <Timer size={14} />
            <span>{(weekSummary?.overtime_hours || 0).toFixed(1)}h OT</span>
          </div>
        </div>
      </div>

      {/* Error Toast */}
      {error && (
        <div className="toast error" data-testid="error-toast">
          {error}
        </div>
      )}

      {/* Success Toast */}
      {successMessage && (
        <div className="toast success" data-testid="success-toast">
          {successMessage}
        </div>
      )}

      {/* Bottom Actions */}
      <div className="p-4 border-t border-white/5">
        <div className="flex justify-between items-center max-w-md mx-auto">
          <button 
            onClick={loadData}
            className="text-sm text-gray-400 flex items-center gap-2"
            data-testid="refresh-button"
          >
            <RefreshCw size={14} />
            Refresh
          </button>
          <button 
            onClick={onLogout}
            className="text-sm text-gray-400"
            data-testid="logout-button"
          >
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
}
