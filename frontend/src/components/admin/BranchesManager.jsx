/**
 * Branches Management - Admin View
 * CRUD operations for branches with geofence
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Building2, Search, Plus, Edit2, MapPin, Users, Settings,
  ChevronRight, Globe, Clock as ClockIcon
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

export default function BranchesManager({ token, user }) {
  const [branches, setBranches] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingBranch, setEditingBranch] = useState(null);
  const [selectedBranch, setSelectedBranch] = useState(null);

  const fetchBranches = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (search) params.set('search', search);

      const response = await fetch(`${API_URL}/api/admin/branches/list?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setBranches(data.branches || []);
        setTotal(data.total || 0);
      }
    } catch (err) {
      console.error('[Branches] Fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [token, search]);

  useEffect(() => {
    fetchBranches();
  }, [fetchBranches]);

  const handleCreate = async (branchData) => {
    try {
      const response = await fetch(`${API_URL}/api/admin/branches/create`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(branchData)
      });

      if (response.ok) {
        setShowCreateModal(false);
        fetchBranches();
      } else {
        const err = await response.json();
        alert(err.detail || 'Failed to create branch');
      }
    } catch (err) {
      console.error('[Branches] Create error:', err);
    }
  };

  const handleUpdate = async (branchId, updateData) => {
    try {
      const response = await fetch(`${API_URL}/api/admin/branches/${branchId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updateData)
      });

      if (response.ok) {
        setEditingBranch(null);
        fetchBranches();
      } else {
        const err = await response.json();
        alert(err.detail || 'Failed to update branch');
      }
    } catch (err) {
      console.error('[Branches] Update error:', err);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900" data-testid="branches-manager">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-white">Branches</h1>
            <p className="text-sm text-slate-400">{total} locations</p>
          </div>
          {user?.role === 'SUPER_ADMIN' && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700"
              data-testid="add-branch-button"
            >
              <Plus size={16} />
              Add Branch
            </button>
          )}
        </div>
      </header>

      <div className="p-6 max-w-7xl mx-auto">
        {/* Search */}
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-4 mb-6">
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search branches..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-slate-400"
            />
          </div>
        </div>

        {/* Branch Cards Grid */}
        {loading ? (
          <div className="text-center py-12 text-slate-400">Loading...</div>
        ) : branches.length === 0 ? (
          <div className="text-center py-12">
            <Building2 size={48} className="mx-auto text-slate-600 mb-4" />
            <p className="text-slate-400">No branches found</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {branches.map((branch) => (
              <div
                key={branch.id}
                className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden hover:border-slate-600 transition-colors"
              >
                <div className="p-5">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-semibold text-white text-lg">{branch.name}</h3>
                      <span className="text-xs text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded-full">
                        {branch.code}
                      </span>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      branch.status === 'active'
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-red-500/20 text-red-400'
                    }`}>
                      {branch.status}
                    </span>
                  </div>

                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-3 mb-4">
                    <div className="bg-slate-700/50 rounded-lg p-3">
                      <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
                        <Users size={12} />
                        Workers
                      </div>
                      <div className="text-lg font-bold text-white">{branch.worker_count || 0}</div>
                    </div>
                    <div className="bg-slate-700/50 rounded-lg p-3">
                      <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
                        <Globe size={12} />
                        Timezone
                      </div>
                      <div className="text-sm font-medium text-white truncate">{branch.timezone || 'UTC'}</div>
                    </div>
                  </div>

                  {/* Address */}
                  {branch.address && (branch.address.city || branch.address.street) && (
                    <div className="flex items-start gap-2 mb-3 text-sm text-slate-400">
                      <MapPin size={14} className="mt-0.5 flex-shrink-0" />
                      <span>
                        {[branch.address.street, branch.address.city, branch.address.state].filter(Boolean).join(', ')}
                      </span>
                    </div>
                  )}

                  {/* Geofence indicator */}
                  {branch.geofence && (
                    <div className="flex items-center gap-2 text-xs text-green-400 mb-3">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      Geofence Active ({branch.geofence.radius_meters || 150}m radius)
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex gap-2 pt-3 border-t border-slate-700">
                    <button
                      onClick={() => setEditingBranch(branch)}
                      className="flex items-center gap-2 px-3 py-2 text-sm text-slate-300 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
                    >
                      <Edit2 size={14} />
                      Edit
                    </button>
                    <button
                      onClick={() => setSelectedBranch(branch)}
                      className="flex items-center gap-2 px-3 py-2 text-sm text-blue-400 hover:text-blue-300 hover:bg-blue-500/10 rounded-lg transition-colors"
                    >
                      <Settings size={14} />
                      Details
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <BranchFormModal
          onClose={() => setShowCreateModal(false)}
          onSave={handleCreate}
        />
      )}

      {/* Edit Modal */}
      {editingBranch && (
        <BranchFormModal
          branch={editingBranch}
          onClose={() => setEditingBranch(null)}
          onSave={(data) => handleUpdate(editingBranch.id, data)}
        />
      )}

      {/* Detail Modal */}
      {selectedBranch && (
        <BranchDetailModal
          branch={selectedBranch}
          token={token}
          onClose={() => setSelectedBranch(null)}
        />
      )}
    </div>
  );
}

// Branch Form Modal
function BranchFormModal({ branch, onClose, onSave }) {
  const [form, setForm] = useState({
    name: branch?.name || '',
    code: branch?.code || '',
    timezone: branch?.timezone || 'UTC',
    address: {
      street: branch?.address?.street || '',
      city: branch?.address?.city || '',
      state: branch?.address?.state || '',
      zip: branch?.address?.zip || '',
      country: branch?.address?.country || ''
    },
    geofence: {
      center: {
        latitude: branch?.geofence?.center?.latitude || 0,
        longitude: branch?.geofence?.center?.longitude || 0
      },
      radius_meters: branch?.geofence?.radius_meters || 150,
      enabled: branch?.geofence?.enabled ?? true
    },
    settings: {
      work_start_time: branch?.settings?.work_start_time || '09:00',
      work_end_time: branch?.settings?.work_end_time || '17:00',
      late_threshold_minutes: branch?.settings?.late_threshold_minutes || 15,
      overtime_threshold_hours: branch?.settings?.overtime_threshold_hours || 8,
      require_gps_for_clock: branch?.settings?.require_gps_for_clock ?? true
    }
  });
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!form.name || (!branch && !form.code)) {
      alert('Please fill name and code');
      return;
    }
    setSaving(true);
    await onSave(form);
    setSaving(false);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" data-testid="branch-modal">
      <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="px-6 py-4 border-b border-slate-700">
          <h3 className="text-lg font-semibold text-white">
            {branch ? 'Edit Branch' : 'Create Branch'}
          </h3>
        </div>

        <div className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">Branch Name *</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">Branch Code *</label>
              <input
                type="text"
                value={form.code}
                onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white"
                disabled={!!branch}
                placeholder="e.g. BR-001"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm text-slate-400 mb-1">Timezone</label>
            <select
              value={form.timezone}
              onChange={(e) => setForm({ ...form, timezone: e.target.value })}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white"
            >
              <option value="UTC">UTC</option>
              <option value="America/New_York">Eastern (ET)</option>
              <option value="America/Chicago">Central (CT)</option>
              <option value="America/Denver">Mountain (MT)</option>
              <option value="America/Los_Angeles">Pacific (PT)</option>
              <option value="Asia/Kolkata">India (IST)</option>
              <option value="Europe/London">UK (GMT/BST)</option>
              <option value="Asia/Dubai">Dubai (GST)</option>
            </select>
          </div>

          <div className="border-t border-slate-700 pt-4">
            <h4 className="text-sm font-medium text-slate-300 mb-3">Address</h4>
            <div className="space-y-3">
              <input
                type="text"
                value={form.address.street}
                onChange={(e) => setForm({ ...form, address: { ...form.address, street: e.target.value } })}
                placeholder="Street"
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm"
              />
              <div className="grid grid-cols-3 gap-3">
                <input
                  type="text"
                  value={form.address.city}
                  onChange={(e) => setForm({ ...form, address: { ...form.address, city: e.target.value } })}
                  placeholder="City"
                  className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm"
                />
                <input
                  type="text"
                  value={form.address.state}
                  onChange={(e) => setForm({ ...form, address: { ...form.address, state: e.target.value } })}
                  placeholder="State"
                  className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm"
                />
                <input
                  type="text"
                  value={form.address.zip}
                  onChange={(e) => setForm({ ...form, address: { ...form.address, zip: e.target.value } })}
                  placeholder="ZIP"
                  className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm"
                />
              </div>
            </div>
          </div>

          <div className="border-t border-slate-700 pt-4">
            <h4 className="text-sm font-medium text-slate-300 mb-3">Geofence Settings</h4>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Latitude</label>
                <input
                  type="number"
                  step="0.0001"
                  value={form.geofence.center.latitude}
                  onChange={(e) => setForm({ ...form, geofence: { ...form.geofence, center: { ...form.geofence.center, latitude: parseFloat(e.target.value) || 0 } } })}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Longitude</label>
                <input
                  type="number"
                  step="0.0001"
                  value={form.geofence.center.longitude}
                  onChange={(e) => setForm({ ...form, geofence: { ...form.geofence, center: { ...form.geofence.center, longitude: parseFloat(e.target.value) || 0 } } })}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Radius (m)</label>
                <input
                  type="number"
                  value={form.geofence.radius_meters}
                  onChange={(e) => setForm({ ...form, geofence: { ...form.geofence, radius_meters: parseInt(e.target.value) || 150 } })}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm"
                />
              </div>
            </div>
          </div>

          <div className="border-t border-slate-700 pt-4">
            <h4 className="text-sm font-medium text-slate-300 mb-3">Work Settings</h4>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Work Start</label>
                <input
                  type="time"
                  value={form.settings.work_start_time}
                  onChange={(e) => setForm({ ...form, settings: { ...form.settings, work_start_time: e.target.value } })}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Work End</label>
                <input
                  type="time"
                  value={form.settings.work_end_time}
                  onChange={(e) => setForm({ ...form, settings: { ...form.settings, work_end_time: e.target.value } })}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm"
                />
              </div>
            </div>
          </div>
        </div>

        <div className="px-6 py-4 border-t border-slate-700 flex justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 text-slate-400 hover:text-white">
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? 'Saving...' : branch ? 'Update' : 'Create'}
          </button>
        </div>
      </div>
    </div>
  );
}

// Branch Detail Modal
function BranchDetailModal({ branch, token, onClose }) {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        const response = await fetch(
          `${process.env.REACT_APP_BACKEND_URL || ''}/api/admin/branches/${branch.id}`,
          { headers: { 'Authorization': `Bearer ${token}` } }
        );
        if (response.ok) {
          setDetails(await response.json());
        }
      } catch (err) {
        console.error('[Branch] Detail error:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchDetails();
  }, [branch.id, token]);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-md">
        <div className="px-6 py-4 border-b border-slate-700 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">{branch.name}</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <span className="text-xl">&times;</span>
          </button>
        </div>
        <div className="p-6">
          {loading ? (
            <div className="text-center text-slate-400 py-8">Loading...</div>
          ) : details ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-700/50 rounded-lg p-3">
                  <div className="text-xs text-slate-400 mb-1">Workers</div>
                  <div className="text-xl font-bold text-white">{details.stats?.worker_count || 0}</div>
                </div>
                <div className="bg-slate-700/50 rounded-lg p-3">
                  <div className="text-xs text-slate-400 mb-1">Teams</div>
                  <div className="text-xl font-bold text-white">{details.stats?.team_count || 0}</div>
                </div>
              </div>
              <div>
                <h4 className="text-sm text-slate-400 mb-2">Settings</h4>
                <div className="bg-slate-700/30 rounded-lg p-3 space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Work Hours</span>
                    <span className="text-white">
                      {details.branch?.settings?.work_start_time || '09:00'} - {details.branch?.settings?.work_end_time || '17:00'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Late Threshold</span>
                    <span className="text-white">{details.branch?.settings?.late_threshold_minutes || 15} min</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">GPS Required</span>
                    <span className="text-white">{details.branch?.settings?.require_gps_for_clock ? 'Yes' : 'No'}</span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center text-slate-400">Failed to load details</div>
          )}
        </div>
      </div>
    </div>
  );
}
