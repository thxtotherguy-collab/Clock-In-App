/**
 * Time Entries Management - Admin View
 * Filtering, editing, and approval workflow
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  ArrowLeft, Search, Filter, Edit2, Check, X, 
  ChevronDown, Calendar, Clock, AlertTriangle, Download
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

export default function TimeEntriesManager({ token, user, onBack }) {
  const [entries, setEntries] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [selectedEntries, setSelectedEntries] = useState([]);
  const [editingEntry, setEditingEntry] = useState(null);
  
  // Filters
  const [filters, setFilters] = useState({
    branch_id: '',
    start_date: '',
    end_date: '',
    status: '',
    search: ''
  });

  const fetchEntries = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      params.set('page', page);
      params.set('page_size', 20);
      
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.set(key, value);
      });

      const response = await fetch(`${API_URL}/api/admin/time-entries/list?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setEntries(data.entries || []);
        setTotal(data.total || 0);
      }
    } catch (err) {
      console.error('[TimeEntries] Fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [token, page, filters]);

  useEffect(() => {
    fetchEntries();
  }, [fetchEntries]);

  const handleApprove = async (entryId, action) => {
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
        fetchEntries();
      }
    } catch (err) {
      console.error('[TimeEntries] Approve error:', err);
    }
  };

  const handleBulkApprove = async (action) => {
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
        fetchEntries();
      }
    } catch (err) {
      console.error('[TimeEntries] Bulk approve error:', err);
    }
  };

  const handleEdit = async (entryId, editData) => {
    try {
      const response = await fetch(`${API_URL}/api/admin/time-entries/${entryId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(editData)
      });

      if (response.ok) {
        setEditingEntry(null);
        fetchEntries();
      }
    } catch (err) {
      console.error('[TimeEntries] Edit error:', err);
    }
  };

  const toggleSelectAll = () => {
    if (selectedEntries.length === entries.length) {
      setSelectedEntries([]);
    } else {
      setSelectedEntries(entries.map(e => e.id));
    }
  };

  const toggleSelect = (id) => {
    if (selectedEntries.includes(id)) {
      setSelectedEntries(selectedEntries.filter(e => e !== id));
    } else {
      setSelectedEntries([...selectedEntries, id]);
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

  const getStatusBadge = (status) => {
    const styles = {
      pending: 'bg-slate-600 text-slate-200',
      completed: 'bg-amber-500/20 text-amber-400',
      approved: 'bg-green-500/20 text-green-400',
      rejected: 'bg-red-500/20 text-red-400'
    };
    return styles[status] || styles.pending;
  };

  return (
    <div className="min-h-screen bg-slate-900" data-testid="time-entries-manager">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 px-6 py-4">
        <div className="flex items-center gap-4">
          <button onClick={onBack} className="text-slate-400 hover:text-white">
            <ArrowLeft size={20} />
          </button>
          <div>
            <h1 className="text-xl font-semibold text-white">Time Entries</h1>
            <p className="text-sm text-slate-400">{total} total entries</p>
          </div>
        </div>
      </header>

      <div className="p-6 max-w-7xl mx-auto">
        {/* Filters */}
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-4 mb-6">
          <div className="flex flex-wrap gap-4">
            {/* Date Range */}
            <div className="flex items-center gap-2">
              <input
                type="date"
                value={filters.start_date}
                onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
                className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
                placeholder="Start Date"
              />
              <span className="text-slate-400">to</span>
              <input
                type="date"
                value={filters.end_date}
                onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
                className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
                placeholder="End Date"
              />
            </div>

            {/* Status Filter */}
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
              data-testid="status-filter"
            >
              <option value="">All Status</option>
              <option value="pending">Pending</option>
              <option value="completed">Completed</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
            </select>

            {/* Search */}
            <div className="relative flex-1 min-w-[200px]">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search employee..."
                value={filters.search}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-slate-400"
              />
            </div>
          </div>
        </div>

        {/* Bulk Actions */}
        {selectedEntries.length > 0 && (
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 mb-4 flex items-center justify-between">
            <span className="text-blue-400">{selectedEntries.length} entries selected</span>
            <div className="flex gap-2">
              <button
                onClick={() => handleBulkApprove('approve')}
                className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-green-700"
                data-testid="bulk-approve"
              >
                <Check size={16} />
                Approve All
              </button>
              <button
                onClick={() => handleBulkApprove('reject')}
                className="flex items-center gap-2 bg-red-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-red-700"
                data-testid="bulk-reject"
              >
                <X size={16} />
                Reject All
              </button>
            </div>
          </div>
        )}

        {/* Table */}
        <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full" data-testid="entries-table">
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
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {loading ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-8 text-center text-slate-400">
                      Loading...
                    </td>
                  </tr>
                ) : entries.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-8 text-center text-slate-400">
                      No entries found
                    </td>
                  </tr>
                ) : (
                  entries.map((entry) => (
                    <tr key={entry.id} className="hover:bg-slate-700/30">
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
                      <td className="px-4 py-3 text-slate-300">{entry.date}</td>
                      <td className="px-4 py-3 text-slate-300">
                        {formatTime(entry.clock_in?.timestamp)}
                      </td>
                      <td className="px-4 py-3 text-slate-300">
                        {formatTime(entry.clock_out?.timestamp)}
                      </td>
                      <td className="px-4 py-3 text-white font-medium">
                        {(entry.total_hours || 0).toFixed(2)}h
                      </td>
                      <td className="px-4 py-3">
                        {entry.overtime_hours > 0 ? (
                          <span className="text-amber-400">{entry.overtime_hours.toFixed(2)}h</span>
                        ) : (
                          <span className="text-slate-500">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(entry.status)}`}>
                          {entry.status}
                        </span>
                        {entry.is_manual_entry && (
                          <span className="ml-2 text-xs text-blue-400">(edited)</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => setEditingEntry(entry)}
                            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded"
                            title="Edit"
                          >
                            <Edit2 size={14} />
                          </button>
                          {entry.status === 'completed' && (
                            <>
                              <button
                                onClick={() => handleApprove(entry.id, 'approve')}
                                className="p-1.5 text-green-400 hover:text-green-300 hover:bg-green-500/10 rounded"
                                title="Approve"
                              >
                                <Check size={14} />
                              </button>
                              <button
                                onClick={() => handleApprove(entry.id, 'reject')}
                                className="p-1.5 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded"
                                title="Reject"
                              >
                                <X size={14} />
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="px-4 py-3 border-t border-slate-700 flex items-center justify-between">
            <div className="text-sm text-slate-400">
              Showing {entries.length} of {total}
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
        </div>
      </div>

      {/* Edit Modal */}
      {editingEntry && (
        <EditEntryModal
          entry={editingEntry}
          onClose={() => setEditingEntry(null)}
          onSave={handleEdit}
        />
      )}
    </div>
  );
}

// Edit Modal Component
function EditEntryModal({ entry, onClose, onSave }) {
  const [clockIn, setClockIn] = useState(entry.clock_in?.timestamp?.slice(0, 16) || '');
  const [clockOut, setClockOut] = useState(entry.clock_out?.timestamp?.slice(0, 16) || '');
  const [breakMins, setBreakMins] = useState(entry.break_minutes || 0);
  const [reason, setReason] = useState('');
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!reason.trim()) {
      alert('Please provide a reason for the edit');
      return;
    }

    setSaving(true);
    await onSave(entry.id, {
      clock_in_time: clockIn ? new Date(clockIn).toISOString() : null,
      clock_out_time: clockOut ? new Date(clockOut).toISOString() : null,
      break_minutes: breakMins,
      reason
    });
    setSaving(false);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" data-testid="edit-modal">
      <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-md">
        <div className="px-6 py-4 border-b border-slate-700">
          <h3 className="text-lg font-semibold text-white">Edit Time Entry</h3>
          <p className="text-sm text-slate-400">{entry.user_name} - {entry.date}</p>
        </div>

        <div className="p-6 space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">Clock In</label>
            <input
              type="datetime-local"
              value={clockIn}
              onChange={(e) => setClockIn(e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white"
            />
          </div>

          <div>
            <label className="block text-sm text-slate-400 mb-1">Clock Out</label>
            <input
              type="datetime-local"
              value={clockOut}
              onChange={(e) => setClockOut(e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white"
            />
          </div>

          <div>
            <label className="block text-sm text-slate-400 mb-1">Break (minutes)</label>
            <input
              type="number"
              value={breakMins}
              onChange={(e) => setBreakMins(parseInt(e.target.value) || 0)}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white"
              min="0"
            />
          </div>

          <div>
            <label className="block text-sm text-slate-400 mb-1">Reason for Edit *</label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white h-20 resize-none"
              placeholder="Explain why this entry is being modified..."
            />
          </div>
        </div>

        <div className="px-6 py-4 border-t border-slate-700 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-slate-400 hover:text-white"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving || !reason.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  );
}
