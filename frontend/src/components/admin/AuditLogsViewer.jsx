/**
 * Audit Logs Viewer - Admin system activity log
 * Shows all system changes with filtering
 */
import React, { useState, useEffect, useCallback } from 'react';
import { FileText, Search, Filter, Clock, User, ChevronDown } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

export default function AuditLogsViewer({ token, user }) {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    action_category: '',
    target_type: '',
    start_date: '',
    end_date: ''
  });

  const fetchLogs = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      params.set('page', page);
      params.set('page_size', 25);

      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.set(key, value);
      });

      const response = await fetch(`${API_URL}/api/admin/audit-logs/list?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setLogs(data.logs || []);
        setTotal(data.total || 0);
      }
    } catch (err) {
      console.error('[AuditLogs] Fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [token, page, filters]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const getActionColor = (action) => {
    if (action?.includes('create')) return 'text-green-400 bg-green-500/10';
    if (action?.includes('delete')) return 'text-red-400 bg-red-500/10';
    if (action?.includes('approve')) return 'text-blue-400 bg-blue-500/10';
    if (action?.includes('reject')) return 'text-amber-400 bg-amber-500/10';
    if (action?.includes('override') || action?.includes('update')) return 'text-purple-400 bg-purple-500/10';
    if (action?.includes('export')) return 'text-cyan-400 bg-cyan-500/10';
    return 'text-slate-400 bg-slate-500/10';
  };

  const formatTimestamp = (ts) => {
    if (!ts) return '-';
    try {
      const d = new Date(ts);
      return d.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    } catch {
      return ts;
    }
  };

  return (
    <div className="min-h-screen bg-slate-900" data-testid="audit-logs-viewer">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 px-6 py-4">
        <div>
          <h1 className="text-xl font-semibold text-white">Audit Logs</h1>
          <p className="text-sm text-slate-400">System activity trail</p>
        </div>
      </header>

      <div className="p-6 max-w-7xl mx-auto">
        {/* Filters */}
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-4 mb-6">
          <div className="flex flex-wrap gap-4">
            <select
              value={filters.action_category}
              onChange={(e) => setFilters({ ...filters, action_category: e.target.value })}
              className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
            >
              <option value="">All Categories</option>
              <option value="time_entry">Time Entries</option>
              <option value="user">Users</option>
              <option value="branch">Branches</option>
              <option value="report">Reports</option>
            </select>

            <select
              value={filters.target_type}
              onChange={(e) => setFilters({ ...filters, target_type: e.target.value })}
              className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
            >
              <option value="">All Types</option>
              <option value="time_entry">Time Entry</option>
              <option value="user">User</option>
              <option value="branch">Branch</option>
              <option value="payroll">Payroll</option>
              <option value="timesheet">Timesheet</option>
            </select>

            <input
              type="date"
              value={filters.start_date}
              onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
              className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
            />
            <span className="text-slate-400 self-center">to</span>
            <input
              type="date"
              value={filters.end_date}
              onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
              className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
            />
          </div>
        </div>

        {/* Logs List */}
        <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full" data-testid="audit-table">
              <thead>
                <tr className="text-left text-xs text-slate-400 uppercase tracking-wider bg-slate-800/50">
                  <th className="px-4 py-3 font-medium">Timestamp</th>
                  <th className="px-4 py-3 font-medium">Actor</th>
                  <th className="px-4 py-3 font-medium">Action</th>
                  <th className="px-4 py-3 font-medium">Target</th>
                  <th className="px-4 py-3 font-medium">Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {loading ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-12 text-center text-slate-400">Loading...</td>
                  </tr>
                ) : logs.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-12 text-center">
                      <FileText size={40} className="mx-auto text-slate-600 mb-3" />
                      <p className="text-slate-400">No audit logs found</p>
                    </td>
                  </tr>
                ) : (
                  logs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-700/30">
                      <td className="px-4 py-3">
                        <div className="text-sm text-slate-300">{formatTimestamp(log.timestamp)}</div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-sm text-white">{log.actor_email}</div>
                        <div className="text-xs text-slate-400">{log.actor_role}</div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getActionColor(log.action)}`}>
                          {log.action}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-sm text-slate-300">{log.target_type}</div>
                        <div className="text-xs text-slate-500 truncate max-w-[200px]">{log.target_ref || log.target_id}</div>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-400">
                        {log.description || '-'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {logs.length > 0 && (
            <div className="px-4 py-3 border-t border-slate-700 flex items-center justify-between">
              <div className="text-sm text-slate-400">
                Page {page} - Showing {logs.length} of {total}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-3 py-1 bg-slate-700 text-white rounded text-sm disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={logs.length < 25}
                  className="px-3 py-1 bg-slate-700 text-white rounded text-sm disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
