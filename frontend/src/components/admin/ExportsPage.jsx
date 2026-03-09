/**
 * Exports Page - CSV and Excel download center
 * Clean export interface with format options
 */
import React, { useState, useEffect } from 'react';
import {
  Download, FileSpreadsheet, FileText, Calendar, Building2,
  CheckCircle, Loader2
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

export default function ExportsPage({ token, user }) {
  const [branches, setBranches] = useState([]);
  const [selectedBranch, setSelectedBranch] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [downloading, setDownloading] = useState(null);
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    // Default date range: last 14 days
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 14);
    setStartDate(start.toISOString().split('T')[0]);
    setEndDate(end.toISOString().split('T')[0]);

    // Fetch branches
    if (user?.role === 'SUPER_ADMIN') {
      fetch(`${API_URL}/api/admin/branches/list`, {
        headers: { 'Authorization': `Bearer ${token}` }
      }).then(r => r.ok ? r.json() : null)
        .then(data => data && setBranches(data.branches || []));
    }
  }, [token, user?.role]);

  const handleExport = async (type, format) => {
    const key = `${type}-${format}`;
    setDownloading(key);
    setSuccess(null);

    try {
      const params = new URLSearchParams();
      if (selectedBranch) params.set('branch_id', selectedBranch);
      if (startDate) params.set('start_date', startDate);
      if (endDate) params.set('end_date', endDate);

      const url = `${API_URL}/api/exports/${type}/${format}?${params}`;

      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        const ext = format === 'excel' ? 'xlsx' : 'csv';
        a.download = `${type}_${startDate}_to_${endDate}.${ext}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(downloadUrl);
        setSuccess(key);
        setTimeout(() => setSuccess(null), 3000);
      } else {
        const err = await response.json().catch(() => null);
        alert(err?.detail || 'Export failed');
      }
    } catch (err) {
      console.error('[Export] Error:', err);
      alert('Export failed. Please try again.');
    } finally {
      setDownloading(null);
    }
  };

  const ExportCard = ({ title, description, icon: Icon, type, formats }) => (
    <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
      <div className="p-6">
        <div className="flex items-start gap-4 mb-4">
          <div className="p-3 bg-blue-500/10 rounded-xl">
            <Icon size={24} className="text-blue-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">{title}</h3>
            <p className="text-sm text-slate-400 mt-1">{description}</p>
          </div>
        </div>

        <div className="flex gap-3">
          {formats.map(({ format, label, icon: FormatIcon }) => {
            const key = `${type}-${format}`;
            const isDownloading = downloading === key;
            const isSuccess = success === key;

            return (
              <button
                key={format}
                onClick={() => handleExport(type, format)}
                disabled={isDownloading}
                className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
                  isSuccess
                    ? 'bg-green-600/20 text-green-400 border border-green-500/30'
                    : format === 'excel'
                      ? 'bg-green-600 text-white hover:bg-green-700'
                      : 'bg-slate-700 text-white hover:bg-slate-600 border border-slate-600'
                } disabled:opacity-50`}
              >
                {isDownloading ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : isSuccess ? (
                  <CheckCircle size={16} />
                ) : (
                  <FormatIcon size={16} />
                )}
                {isSuccess ? 'Downloaded!' : label}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-900" data-testid="exports-page">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 px-6 py-4">
        <div>
          <h1 className="text-xl font-semibold text-white">Export Center</h1>
          <p className="text-sm text-slate-400">Download reports in CSV or Excel format</p>
        </div>
      </header>

      <div className="p-6 max-w-4xl mx-auto">
        {/* Filters */}
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-5 mb-6">
          <h3 className="text-sm font-medium text-slate-300 mb-4">Export Parameters</h3>
          <div className="flex flex-wrap gap-4">
            {/* Date Range */}
            <div className="flex items-center gap-3">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Start Date</label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
                />
              </div>
              <span className="text-slate-400 mt-5">to</span>
              <div>
                <label className="block text-xs text-slate-400 mb-1">End Date</label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
                />
              </div>
            </div>

            {/* Branch Filter */}
            {branches.length > 0 && (
              <div>
                <label className="block text-xs text-slate-400 mb-1">Branch</label>
                <select
                  value={selectedBranch}
                  onChange={(e) => setSelectedBranch(e.target.value)}
                  className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
                >
                  <option value="">All Branches</option>
                  {branches.map(b => (
                    <option key={b.id} value={b.id}>{b.name}</option>
                  ))}
                </select>
              </div>
            )}
          </div>
        </div>

        {/* Export Cards */}
        <div className="space-y-4">
          <ExportCard
            title="Payroll Report"
            description="Aggregated by employee — includes regular hours, overtime, rate tier. Ready for payroll processing."
            icon={FileSpreadsheet}
            type="payroll"
            formats={[
              { format: 'csv', label: 'CSV', icon: FileText },
              { format: 'excel', label: 'Excel (.xlsx)', icon: FileSpreadsheet }
            ]}
          />

          <ExportCard
            title="Timesheet Report"
            description="Detailed daily entries — clock in/out times, breaks, status. For record keeping and auditing."
            icon={FileText}
            type="timesheet"
            formats={[
              { format: 'csv', label: 'CSV', icon: FileText },
              { format: 'excel', label: 'Excel (.xlsx)', icon: FileSpreadsheet }
            ]}
          />

          <ExportCard
            title="Attendance Report"
            description="Daily attendance snapshot — present/absent status, late arrivals, overtime. Single date report."
            icon={Calendar}
            type="attendance-report"
            formats={[
              { format: 'csv', label: 'CSV', icon: FileText }
            ]}
          />
        </div>
      </div>
    </div>
  );
}
