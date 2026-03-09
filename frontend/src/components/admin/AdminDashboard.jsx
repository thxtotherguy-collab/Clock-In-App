/**
 * Admin Dashboard - Main Overview Page
 * Clean, professional, data-focused design
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Users, Clock, AlertTriangle, Calendar, Download, 
  Building2, ChevronDown, RefreshCw, CheckCircle, XCircle,
  TrendingUp, UserCheck, UserX, Timer
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

export default function AdminDashboard({ user, token, onLogout, onNavigate, embedded }) {
  const [overview, setOverview] = useState(null);
  const [liveWorkers, setLiveWorkers] = useState([]);
  const [branches, setBranches] = useState([]);
  const [selectedBranch, setSelectedBranch] = useState('');
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      // Fetch overview
      const overviewUrl = new URL(`${API_URL}/api/admin/dashboard/overview`);
      if (selectedBranch) overviewUrl.searchParams.set('branch_id', selectedBranch);
      if (selectedDate) overviewUrl.searchParams.set('date', selectedDate);
      
      const overviewRes = await fetch(overviewUrl, { headers });
      if (overviewRes.ok) {
        setOverview(await overviewRes.json());
      }

      // Fetch live workers
      const liveUrl = new URL(`${API_URL}/api/admin/dashboard/live-status`);
      if (selectedBranch) liveUrl.searchParams.set('branch_id', selectedBranch);
      
      const liveRes = await fetch(liveUrl, { headers });
      if (liveRes.ok) {
        const data = await liveRes.json();
        setLiveWorkers(data.workers || []);
      }

      // Fetch branches (for super admin)
      if (user?.role === 'SUPER_ADMIN' || user?.role === 'COMPANY_ADMIN') {
        const branchRes = await fetch(`${API_URL}/api/admin/branches/list`, { headers });
        if (branchRes.ok) {
          const data = await branchRes.json();
          setBranches(data.branches || []);
        }
      }

    } catch (err) {
      setError('Failed to load dashboard data');
      console.error('[AdminDashboard] Error:', err);
    } finally {
      setLoading(false);
    }
  }, [token, selectedBranch, selectedDate, user?.role]);

  useEffect(() => {
    fetchData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleExport = async (type) => {
    try {
      const headers = { 'Authorization': `Bearer ${token}` };
      let url = `${API_URL}/api/exports/${type}/csv`;
      
      if (selectedBranch) url += `?branch_id=${selectedBranch}`;
      
      const response = await fetch(url, { headers });
      if (response.ok) {
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `${type}_${selectedDate}.csv`;
        a.click();
      }
    } catch (err) {
      console.error('[Export] Error:', err);
    }
  };

  if (loading && !overview) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900" data-testid="admin-dashboard">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-white">Dashboard</h1>
            <p className="text-sm text-slate-400">
              {user?.role === 'BRANCH_ADMIN' ? 'Branch Overview' : 'System Overview'}
            </p>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={fetchData}
              className="p-2 text-slate-400 hover:text-white transition-colors"
              data-testid="refresh-button"
            >
              <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
            </button>
            <button
              onClick={onLogout}
              className="text-sm text-slate-400 hover:text-white"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>

      <div className="p-6 max-w-7xl mx-auto">
        {/* Filters */}
        <div className="flex flex-wrap gap-4 mb-6">
          {/* Branch Filter (for admins) */}
          {branches.length > 0 && (
            <div className="relative">
              <select
                value={selectedBranch}
                onChange={(e) => setSelectedBranch(e.target.value)}
                className="appearance-none bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 pr-10 text-white text-sm focus:outline-none focus:border-blue-500"
                data-testid="branch-filter"
              >
                <option value="">All Branches</option>
                {branches.map(b => (
                  <option key={b.id} value={b.id}>{b.name}</option>
                ))}
              </select>
              <ChevronDown size={16} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
            </div>
          )}

          {/* Date Filter */}
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
            data-testid="date-filter"
          />

          {/* Export Buttons */}
          <div className="flex gap-2 ml-auto">
            <button
              onClick={() => handleExport('attendance-report')}
              className="flex items-center gap-2 bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-sm text-white hover:bg-slate-700 transition-colors"
              data-testid="export-attendance"
            >
              <Download size={16} />
              Attendance
            </button>
            <button
              onClick={() => handleExport('payroll')}
              className="flex items-center gap-2 bg-blue-600 rounded-lg px-4 py-2 text-sm text-white hover:bg-blue-700 transition-colors"
              data-testid="export-payroll"
            >
              <Download size={16} />
              Payroll Export
            </button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {/* Currently Working */}
          <div className="bg-slate-800 rounded-xl p-5 border border-slate-700" data-testid="stat-working">
            <div className="flex items-center justify-between mb-3">
              <UserCheck size={20} className="text-green-500" />
              <span className="text-xs text-green-500 bg-green-500/10 px-2 py-1 rounded">Live</span>
            </div>
            <div className="text-3xl font-bold text-white">{overview?.currently_working || 0}</div>
            <div className="text-sm text-slate-400 mt-1">Currently Working</div>
          </div>

          {/* Late Staff */}
          <div className="bg-slate-800 rounded-xl p-5 border border-slate-700" data-testid="stat-late">
            <div className="flex items-center justify-between mb-3">
              <AlertTriangle size={20} className="text-amber-500" />
            </div>
            <div className="text-3xl font-bold text-white">{overview?.late_staff || 0}</div>
            <div className="text-sm text-slate-400 mt-1">Late Today</div>
          </div>

          {/* Absent */}
          <div className="bg-slate-800 rounded-xl p-5 border border-slate-700" data-testid="stat-absent">
            <div className="flex items-center justify-between mb-3">
              <UserX size={20} className="text-red-500" />
            </div>
            <div className="text-3xl font-bold text-white">{overview?.absent_staff || 0}</div>
            <div className="text-sm text-slate-400 mt-1">Absent</div>
          </div>

          {/* Total Hours */}
          <div className="bg-slate-800 rounded-xl p-5 border border-slate-700" data-testid="stat-hours">
            <div className="flex items-center justify-between mb-3">
              <Timer size={20} className="text-blue-500" />
            </div>
            <div className="text-3xl font-bold text-white">{overview?.total_hours_today || 0}h</div>
            <div className="text-sm text-slate-400 mt-1">Total Hours Today</div>
          </div>
        </div>

        {/* Quick Stats Row */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-slate-800/50 rounded-lg p-4 text-center">
            <div className="text-2xl font-semibold text-white">{overview?.total_workers || 0}</div>
            <div className="text-xs text-slate-400">Total Workers</div>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4 text-center">
            <div className="text-2xl font-semibold text-white">{overview?.total_clocked_in || 0}</div>
            <div className="text-xs text-slate-400">Clocked In Today</div>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4 text-center">
            <div className="text-2xl font-semibold text-white">{overview?.avg_hours_per_worker || 0}h</div>
            <div className="text-xs text-slate-400">Avg Hours/Worker</div>
          </div>
        </div>

        {/* Live Workers Table */}
        <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-700 flex items-center justify-between">
            <h2 className="font-semibold text-white flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              Currently Working ({liveWorkers.length})
            </h2>
            <button
              onClick={() => onNavigate && onNavigate('time-entries')}
              className="text-sm text-blue-400 hover:text-blue-300"
            >
              View All Entries
            </button>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full" data-testid="live-workers-table">
              <thead>
                <tr className="text-left text-xs text-slate-400 uppercase tracking-wider">
                  <th className="px-5 py-3 font-medium">Employee</th>
                  <th className="px-5 py-3 font-medium">Clock In</th>
                  <th className="px-5 py-3 font-medium">Elapsed</th>
                  <th className="px-5 py-3 font-medium">Location</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {liveWorkers.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-5 py-8 text-center text-slate-400">
                      No workers currently clocked in
                    </td>
                  </tr>
                ) : (
                  liveWorkers.map((worker) => (
                    <tr key={worker.entry_id} className="hover:bg-slate-700/30">
                      <td className="px-5 py-4">
                        <div className="font-medium text-white">{worker.user_name}</div>
                        <div className="text-xs text-slate-400">{worker.employee_id || 'No ID'}</div>
                      </td>
                      <td className="px-5 py-4 text-slate-300">
                        {worker.clock_in_time ? new Date(worker.clock_in_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '-'}
                      </td>
                      <td className="px-5 py-4">
                        <span className="text-green-400 font-mono">
                          {worker.elapsed_hours?.toFixed(2) || 0}h
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        {worker.gps ? (
                          <span className="text-xs text-slate-400">
                            {worker.gps.latitude?.toFixed(4)}, {worker.gps.longitude?.toFixed(4)}
                          </span>
                        ) : (
                          <span className="text-xs text-slate-500">No GPS</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Navigation Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <button
            onClick={() => onNavigate && onNavigate('time-entries')}
            className="bg-slate-800 border border-slate-700 rounded-xl p-5 text-left hover:border-blue-500 transition-colors group"
            data-testid="nav-timeentries"
          >
            <Clock size={24} className="text-blue-400 mb-3" />
            <div className="font-medium text-white group-hover:text-blue-400">Time Entries</div>
            <div className="text-xs text-slate-400 mt-1">View & edit entries</div>
          </button>

          <button
            onClick={() => onNavigate && onNavigate('approvals')}
            className="bg-slate-800 border border-slate-700 rounded-xl p-5 text-left hover:border-green-500 transition-colors group"
            data-testid="nav-approvals"
          >
            <CheckCircle size={24} className="text-green-400 mb-3" />
            <div className="font-medium text-white group-hover:text-green-400">Approvals</div>
            <div className="text-xs text-slate-400 mt-1">Review timesheets</div>
          </button>

          <button
            onClick={() => onNavigate && onNavigate('users')}
            className="bg-slate-800 border border-slate-700 rounded-xl p-5 text-left hover:border-purple-500 transition-colors group"
            data-testid="nav-users"
          >
            <Users size={24} className="text-purple-400 mb-3" />
            <div className="font-medium text-white group-hover:text-purple-400">Workers</div>
            <div className="text-xs text-slate-400 mt-1">Manage employees</div>
          </button>

          <button
            onClick={() => onNavigate && onNavigate('branches')}
            className="bg-slate-800 border border-slate-700 rounded-xl p-5 text-left hover:border-amber-500 transition-colors group"
            data-testid="nav-branches"
          >
            <Building2 size={24} className="text-amber-400 mb-3" />
            <div className="font-medium text-white group-hover:text-amber-400">Branches</div>
            <div className="text-xs text-slate-400 mt-1">Locations & geofence</div>
          </button>
        </div>
      </div>
    </div>
  );
}
