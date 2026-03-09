/**
 * Users Management - Admin View
 * Create, edit, assign workers to branches/teams
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  ArrowLeft, Search, Plus, Edit2, Trash2, 
  UserPlus, Building2, Users as UsersIcon
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

export default function UsersManager({ token, user, onBack }) {
  const [users, setUsers] = useState([]);
  const [branches, setBranches] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  
  const [filters, setFilters] = useState({
    branch_id: '',
    role: '',
    status: 'active',
    search: ''
  });

  const fetchUsers = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      params.set('page', page);
      params.set('page_size', 20);
      
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.set(key, value);
      });

      const response = await fetch(`${API_URL}/api/admin/users/list?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setUsers(data.users || []);
        setTotal(data.total || 0);
      }
    } catch (err) {
      console.error('[Users] Fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [token, page, filters]);

  const fetchBranches = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/admin/branches/list`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setBranches(data.branches || []);
      }
    } catch (err) {
      console.error('[Users] Fetch branches error:', err);
    }
  }, [token]);

  useEffect(() => {
    fetchUsers();
    fetchBranches();
  }, [fetchUsers, fetchBranches]);

  const handleCreate = async (userData) => {
    try {
      const response = await fetch(`${API_URL}/api/admin/users/create`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(userData)
      });

      if (response.ok) {
        setShowCreateModal(false);
        fetchUsers();
      }
    } catch (err) {
      console.error('[Users] Create error:', err);
    }
  };

  const handleUpdate = async (userId, userData) => {
    try {
      const response = await fetch(`${API_URL}/api/admin/users/${userId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(userData)
      });

      if (response.ok) {
        setEditingUser(null);
        fetchUsers();
      }
    } catch (err) {
      console.error('[Users] Update error:', err);
    }
  };

  const handleDelete = async (userId) => {
    if (!window.confirm('Deactivate this user?')) return;

    try {
      const response = await fetch(`${API_URL}/api/admin/users/${userId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        fetchUsers();
      }
    } catch (err) {
      console.error('[Users] Delete error:', err);
    }
  };

  const getRoleBadge = (role) => {
    const styles = {
      SUPER_ADMIN: 'bg-purple-500/20 text-purple-400',
      BRANCH_ADMIN: 'bg-blue-500/20 text-blue-400',
      TEAM_LEADER: 'bg-green-500/20 text-green-400',
      WORKER: 'bg-slate-500/20 text-slate-400'
    };
    return styles[role] || styles.WORKER;
  };

  return (
    <div className="min-h-screen bg-slate-900" data-testid="users-manager">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button onClick={onBack} className="text-slate-400 hover:text-white">
              <ArrowLeft size={20} />
            </button>
            <div>
              <h1 className="text-xl font-semibold text-white">Workers</h1>
              <p className="text-sm text-slate-400">{total} employees</p>
            </div>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700"
            data-testid="add-user-button"
          >
            <UserPlus size={16} />
            Add Worker
          </button>
        </div>
      </header>

      <div className="p-6 max-w-7xl mx-auto">
        {/* Filters */}
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-4 mb-6">
          <div className="flex flex-wrap gap-4">
            {/* Search */}
            <div className="relative flex-1 min-w-[200px]">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search by name, email, ID..."
                value={filters.search}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-slate-400"
              />
            </div>

            {/* Branch Filter */}
            {branches.length > 0 && (
              <select
                value={filters.branch_id}
                onChange={(e) => setFilters({ ...filters, branch_id: e.target.value })}
                className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
              >
                <option value="">All Branches</option>
                {branches.map(b => (
                  <option key={b.id} value={b.id}>{b.name}</option>
                ))}
              </select>
            )}

            {/* Role Filter */}
            <select
              value={filters.role}
              onChange={(e) => setFilters({ ...filters, role: e.target.value })}
              className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
            >
              <option value="">All Roles</option>
              <option value="WORKER">Worker</option>
              <option value="TEAM_LEADER">Team Leader</option>
              <option value="BRANCH_ADMIN">Branch Admin</option>
            </select>

            {/* Status Filter */}
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
            >
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="">All</option>
            </select>
          </div>
        </div>

        {/* Table */}
        <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full" data-testid="users-table">
              <thead>
                <tr className="text-left text-xs text-slate-400 uppercase tracking-wider bg-slate-800/50">
                  <th className="px-4 py-3 font-medium">Employee</th>
                  <th className="px-4 py-3 font-medium">Contact</th>
                  <th className="px-4 py-3 font-medium">Role</th>
                  <th className="px-4 py-3 font-medium">Branch</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                      Loading...
                    </td>
                  </tr>
                ) : users.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                      No users found
                    </td>
                  </tr>
                ) : (
                  users.map((u) => (
                    <tr key={u.id} className="hover:bg-slate-700/30">
                      <td className="px-4 py-3">
                        <div className="font-medium text-white">
                          {u.first_name} {u.last_name}
                        </div>
                        <div className="text-xs text-slate-400">ID: {u.employee_id || '-'}</div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-slate-300 text-sm">{u.email}</div>
                        <div className="text-xs text-slate-400">{u.phone || '-'}</div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRoleBadge(u.role)}`}>
                          {u.role}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-300 text-sm">
                        {u.branch_name || '-'}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          u.status === 'active' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                        }`}>
                          {u.status}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => setEditingUser(u)}
                            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded"
                            title="Edit"
                          >
                            <Edit2 size={14} />
                          </button>
                          <button
                            onClick={() => handleDelete(u.id)}
                            className="p-1.5 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded"
                            title="Deactivate"
                          >
                            <Trash2 size={14} />
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
          <div className="px-4 py-3 border-t border-slate-700 flex items-center justify-between">
            <div className="text-sm text-slate-400">
              Showing {users.length} of {total}
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
                disabled={users.length < 20}
                className="px-3 py-1 bg-slate-700 text-white rounded text-sm disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <UserFormModal
          branches={branches}
          onClose={() => setShowCreateModal(false)}
          onSave={handleCreate}
        />
      )}

      {/* Edit Modal */}
      {editingUser && (
        <UserFormModal
          user={editingUser}
          branches={branches}
          onClose={() => setEditingUser(null)}
          onSave={(data) => handleUpdate(editingUser.id, data)}
        />
      )}
    </div>
  );
}

// User Form Modal
function UserFormModal({ user, branches, onClose, onSave }) {
  const [form, setForm] = useState({
    email: user?.email || '',
    password: '',
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    phone: user?.phone || '',
    employee_id: user?.employee_id || '',
    role: user?.role || 'WORKER',
    branch_id: user?.branch_id || '',
    hourly_rate_tier: user?.hourly_rate_tier || 'standard',
    overtime_eligible: user?.overtime_eligible ?? true
  });
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!form.first_name || !form.last_name || (!user && !form.email)) {
      alert('Please fill required fields');
      return;
    }

    setSaving(true);
    const data = { ...form };
    if (user) {
      delete data.email;
      delete data.password;
    }
    await onSave(data);
    setSaving(false);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" data-testid="user-modal">
      <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="px-6 py-4 border-b border-slate-700">
          <h3 className="text-lg font-semibold text-white">
            {user ? 'Edit Worker' : 'Add New Worker'}
          </h3>
        </div>

        <div className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">First Name *</label>
              <input
                type="text"
                value={form.first_name}
                onChange={(e) => setForm({ ...form, first_name: e.target.value })}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">Last Name *</label>
              <input
                type="text"
                value={form.last_name}
                onChange={(e) => setForm({ ...form, last_name: e.target.value })}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white"
              />
            </div>
          </div>

          {!user && (
            <>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Email *</label>
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Password *</label>
                <input
                  type="password"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white"
                  placeholder="Min 8 characters"
                />
              </div>
            </>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">Phone</label>
              <input
                type="tel"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">Employee ID</label>
              <input
                type="text"
                value={form.employee_id}
                onChange={(e) => setForm({ ...form, employee_id: e.target.value })}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">Role</label>
              <select
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value })}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white"
              >
                <option value="WORKER">Worker</option>
                <option value="TEAM_LEADER">Team Leader</option>
                <option value="BRANCH_ADMIN">Branch Admin</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">Branch</label>
              <select
                value={form.branch_id}
                onChange={(e) => setForm({ ...form, branch_id: e.target.value })}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white"
              >
                <option value="">Unassigned</option>
                {branches.map(b => (
                  <option key={b.id} value={b.id}>{b.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">Rate Tier</label>
              <select
                value={form.hourly_rate_tier}
                onChange={(e) => setForm({ ...form, hourly_rate_tier: e.target.value })}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white"
              >
                <option value="standard">Standard</option>
                <option value="senior">Senior</option>
                <option value="junior">Junior</option>
              </select>
            </div>
            <div className="flex items-center">
              <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.overtime_eligible}
                  onChange={(e) => setForm({ ...form, overtime_eligible: e.target.checked })}
                  className="rounded border-slate-600"
                />
                Overtime Eligible
              </label>
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
            {saving ? 'Saving...' : user ? 'Update' : 'Create'}
          </button>
        </div>
      </div>
    </div>
  );
}
