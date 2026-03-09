/**
 * Approvals Manager - Dedicated approval queue view
 * Focused on pending time entry approvals
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  CheckCircle, XCircle, Clock, AlertTriangle, Filter,
  Check, X, ChevronDown, Eye
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

export default function ApprovalsManager({ token, user }) {
  const [entries, setEntries] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [selectedEntries, setSelectedEntries] = useState([]);
  const [processingId, setProcessingId] = useState(null);
  const [branches, setBranches] = useState([]);
  const [selectedBranch, setSelectedBranch] = useState('');
  const [stats, setStats] = useState({ pending: 0, approved: 0, rejected: 0 });

  const fetchPending = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      params.set('page', page);
      params.set('page_size', 20);
      if (selectedBranch) params.set('branch_id', selectedBranch);

      const response = await fetch(`${API_URL}/api/admin/time-entries/pending-approval?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setEntries(data.entries || []);
        setTotal(data.total || 0);
        setStats(prev => ({ ...prev, pending: data.total || 0 }));
      }
    } catch (err) {
      console.error('[Approvals] Fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [token, page, selectedBranch]);

  useEffect(() => {
    fetchPending();
    // Fetch branches for filter
    if (user?.role === 'SUPER_ADMIN') {
      fetch(`${API_URL}/api/admin/branches/list`, {
        headers: { 'Authorization': `Bearer ${token}` }
      }).then(r => r.ok ? r.json() : null)
        .then(data => data && setBranches(data.branches || []));
    }
  }, [fetchPending, token, user?.role]);

  const handleApprove = async (entryId, action) => {
    setProcessingId(entryId);
    try {
      const response = await fetch(`${API_URL}/api/admin/time-entries/${entryId}/approve`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action })
      });

      if (response.ok) {
        fetchPending();
      }
    } catch (err) {
      console.error('[Approvals] Action error:', err);
    } finally {
      setProcessingId(null);
    }
  };

  const handleBulkAction = async (action) => {
    if (selectedEntries.length === 0) return;

    try {
      const response = await fetch(`${API_URL}/api/admin/time-entries/bulk-approve`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          entry_ids: selectedEntries,
          action
        })
      });

      if (response.ok) {
        setSelectedEntries([]);
        fetchPending();
      }
    } catch (err) {
      console.error('[Approvals] Bulk action error:', err);
    }
  };

  const toggleSelect = (id) => {
    setSelectedEntries(prev =>
      prev.includes(id) ? prev.filter(e => e !== id) : [...prev, id]
    );
  };

  const toggleSelectAll = () => {
    if (selectedEntries.length === entries.length) {
      setSelectedEntries([]);
    } else {
      setSelectedEntries(entries.map(e => e.id));
    }
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return '-';
    try {
      return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '-';
    }
  };

  return (
    <div className="min-h-screen bg-slate-900" data-testid="approvals-manager">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-white">Timesheet Approvals</h1>
            <p className="text-sm text-slate-400">{total} entries pending review</p>
          </div>
        </div>
      </header>

      <div className="p-6 max-w-7xl mx-auto">
        {/* Stats Cards */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <Clock size={20} className="text-amber-400" />
              <div>
                <div className="text-2xl font-bold text-white">{total}</div>
                <div className="text-xs text-amber-400">Pending Review</div>
              </div>
            </div>
          </div>
          <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <CheckCircle size={20} className="text-green-400" />
              <div>
                <div className="text-2xl font-bold text-white">{stats.approved}</div>
                <div className="text-xs text-green-400">Approved Today</div>
              </div>
            </div>
          </div>
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <XCircle size={20} className="text-red-400" />
              <div>
                <div className="text-2xl font-bold text-white">{stats.rejected}</div>
                <div className="text-xs text-red-400">Rejected Today</div>
              </div>
            </div>
          </div>
        </div>

        {/* Filters */}
        {branches.length > 0 && (
          <div className="mb-4">
            <select
              value={selectedBranch}
              onChange={(e) => setSelectedBranch(e.target.value)}
              className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-sm text-white"
            >
              <option value="">All Branches</option>
              {branches.map(b => (
                <option key={b.id} value={b.id}>{b.name}</option>
              ))}
            </select>
          </div>
        )}

        {/* Bulk Actions */}
        {selectedEntries.length > 0 && (
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 mb-4 flex items-center justify-between">
            <span className="text-blue-400 font-medium">{selectedEntries.length} entries selected</span>
            <div className="flex gap-2">
              <button
                onClick={() => handleBulkAction('approve')}
                className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-green-700 transition-colors"
              >
                <Check size={16} />
                Approve All
              </button>
              <button
                onClick={() => handleBulkAction('reject')}
                className="flex items-center gap-2 bg-red-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-red-700 transition-colors"
              >
                <X size={16} />
                Reject All
              </button>
            </div>
          </div>
        )}

        {/* Entries Table */}
        <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full" data-testid="approvals-table">
              <thead>
                <tr className="text-left text-xs text-slate-400 uppercase tracking-wider bg-slate-800/50">
                  <th className="px-4 py-3">
                    <input
                      type="checkbox"
                      checked={selectedEntries.length === entries.length && entries.length > 0}
                      onChange={toggleSelectAll}
                      className="rounded border-slate-600"
                    />
                  </th>
                  <th className="px-4 py-3 font-medium">Employee</th>
                  <th className="px-4 py-3 font-medium">Date</th>
                  <th className="px-4 py-3 font-medium">Clock In</th>
                  <th className="px-4 py-3 font-medium">Clock Out</th>
                  <th className="px-4 py-3 font-medium">Hours</th>
                  <th className="px-4 py-3 font-medium">OT</th>
                  <th className="px-4 py-3 font-medium">Flags</th>
                  <th className="px-4 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {loading ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-12 text-center text-slate-400">Loading...</td>
                  </tr>
                ) : entries.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-12 text-center">
                      <CheckCircle size={40} className="mx-auto text-green-500/40 mb-3" />
                      <p className="text-slate-400">All caught up! No pending approvals.</p>
                    </td>
                  </tr>
                ) : (
                  entries.map((entry) => (
                    <tr key={entry.id} className="hover:bg-slate-700/30 transition-colors">
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={selectedEntries.includes(entry.id)}
                          onChange={() => toggleSelect(entry.id)}
                          className="rounded border-slate-600"
                        />
                      </td>
                      <td className="px-4 py-3">
                        <div className="font-medium text-white">{entry.user_name || 'Unknown'}</div>
                        <div className="text-xs text-slate-400">{entry.employee_id || '-'}</div>
                      </td>
                      <td className="px-4 py-3 text-slate-300 text-sm">{entry.date}</td>
                      <td className="px-4 py-3 text-slate-300 text-sm">
                        {formatTime(entry.clock_in?.timestamp)}
                      </td>
                      <td className="px-4 py-3 text-slate-300 text-sm">
                        {formatTime(entry.clock_out?.timestamp)}
                      </td>
                      <td className="px-4 py-3 text-white font-medium">
                        {(entry.total_hours || 0).toFixed(2)}h
                      </td>
                      <td className="px-4 py-3">
                        {(entry.overtime_hours || 0) > 0 ? (
                          <span className="text-amber-400 text-sm">{entry.overtime_hours.toFixed(2)}h</span>
                        ) : (
                          <span className="text-slate-500 text-sm">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-1">
                          {entry.is_manual_entry && (
                            <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded">Edited</span>
                          )}
                          {entry.flags?.late_clock_in && (
                            <span className="text-xs bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded">Late</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => handleApprove(entry.id, 'approve')}
                            disabled={processingId === entry.id}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600/20 text-green-400 hover:bg-green-600 hover:text-white rounded-lg text-xs font-medium transition-colors disabled:opacity-50"
                          >
                            <Check size={14} />
                            Approve
                          </button>
                          <button
                            onClick={() => handleApprove(entry.id, 'reject')}
                            disabled={processingId === entry.id}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-red-600/20 text-red-400 hover:bg-red-600 hover:text-white rounded-lg text-xs font-medium transition-colors disabled:opacity-50"
                          >
                            <X size={14} />
                            Reject
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {entries.length > 0 && (
            <div className="px-4 py-3 border-t border-slate-700 flex items-center justify-between">
              <div className="text-sm text-slate-400">
                Page {page} - Showing {entries.length} of {total}
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
                  disabled={entries.length < 20}
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
