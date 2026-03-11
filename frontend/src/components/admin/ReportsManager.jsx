/**
 * Reports Manager - Send Report Now + Report Config + History
 * Admin interface for automated reporting system
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Send, Settings, Clock, Mail, CheckCircle, AlertTriangle,
  Loader2, Eye, Plus, X, RefreshCw, Calendar, Building2
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

export default function ReportsManager({ token, user }) {
  const [config, setConfig] = useState(null);
  const [history, setHistory] = useState([]);
  const [emailLogs, setEmailLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [sendResult, setSendResult] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const [branches, setBranches] = useState([]);
  const [selectedBranch, setSelectedBranch] = useState('');
  const [showConfig, setShowConfig] = useState(false);
  const [otConfig, setOtConfig] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  // Fetch all data
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const headers = { 'Authorization': `Bearer ${token}` };

      const [configRes, historyRes, emailRes, branchRes, otRes] = await Promise.all([
        fetch(`${API_URL}/api/reports/config`, { headers }),
        fetch(`${API_URL}/api/reports/history?page_size=10`, { headers }),
        fetch(`${API_URL}/api/reports/email-logs?page_size=10`, { headers }),
        fetch(`${API_URL}/api/admin/branches/list`, { headers }),
        fetch(`${API_URL}/api/reports/overtime-config`, { headers })
      ]);

      if (configRes.ok) setConfig(await configRes.json());
      if (historyRes.ok) { const d = await historyRes.json(); setHistory(d.runs || []); }
      if (emailRes.ok) { const d = await emailRes.json(); setEmailLogs(d.logs || []); }
      if (branchRes.ok) { const d = await branchRes.json(); setBranches(d.branches || []); }
      if (otRes.ok) setOtConfig(await otRes.json());
    } catch (err) {
      console.error('[Reports] Fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => { fetchData(); }, [fetchData]);

  // Send Report Now
  const handleSendNow = async () => {
    setSending(true);
    setSendResult(null);
    try {
      const response = await fetch(`${API_URL}/api/reports/send-now`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ branch_id: selectedBranch || null })
      });
      const data = await response.json();
      if (response.ok) {
        setSendResult({ type: 'success', data });
        fetchData(); // Refresh history
      } else {
        setSendResult({ type: 'error', message: data.detail || 'Failed to send' });
      }
    } catch (err) {
      setSendResult({ type: 'error', message: err.message });
    } finally {
      setSending(false);
    }
  };

  // Preview Report
  const handlePreview = async () => {
    try {
      const params = new URLSearchParams();
      if (selectedBranch) params.set('branch_id', selectedBranch);
      const response = await fetch(`${API_URL}/api/reports/preview?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        setPreviewData(await response.json());
        setShowPreview(true);
      }
    } catch (err) {
      console.error('[Reports] Preview error:', err);
    }
  };

  // Update Config
  const handleConfigUpdate = async (updates) => {
    try {
      const response = await fetch(`${API_URL}/api/reports/config`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updates)
      });
      if (response.ok) {
        fetchData();
      }
    } catch (err) {
      console.error('[Reports] Config update error:', err);
    }
  };

  const formatDateTime = (ts) => {
    if (!ts) return '-';
    try { return new Date(ts).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }); }
    catch { return ts; }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <Loader2 size={24} className="animate-spin text-blue-400" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900" data-testid="reports-manager">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-white">Automated Reports</h1>
            <p className="text-sm text-slate-400">
              Daily email reports &bull; {config?.enabled ? 'Active' : 'Disabled'} &bull; 
              Email sending: <span className="text-amber-400 font-medium">MOCKED</span> (logged to DB)
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={handlePreview}
              className="flex items-center gap-2 px-4 py-2 bg-slate-700 text-white rounded-lg text-sm hover:bg-slate-600 transition-colors"
            >
              <Eye size={16} />
              Preview Report
            </button>
            <button
              onClick={handleSendNow}
              disabled={sending}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50 transition-colors"
              data-testid="send-now-button"
            >
              {sending ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
              {sending ? 'Sending...' : 'Send Report Now'}
            </button>
          </div>
        </div>
      </header>

      <div className="p-6 max-w-7xl mx-auto">
        {/* Send Result */}
        {sendResult && (
          <div className={`mb-6 p-4 rounded-xl border ${
            sendResult.type === 'success' 
              ? 'bg-green-500/10 border-green-500/30 text-green-400'
              : 'bg-red-500/10 border-red-500/30 text-red-400'
          }`}>
            <div className="flex items-center gap-3">
              {sendResult.type === 'success' ? <CheckCircle size={20} /> : <AlertTriangle size={20} />}
              <div>
                {sendResult.type === 'success' ? (
                  <span className="font-medium">
                    Report sent! {sendResult.data?.emails_sent} email(s) logged (mocked)
                  </span>
                ) : (
                  <span className="font-medium">{sendResult.message}</span>
                )}
              </div>
              <button onClick={() => setSendResult(null)} className="ml-auto"><X size={16} /></button>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-1 mb-6 bg-slate-800 rounded-lg p-1 border border-slate-700 w-fit">
          {['overview', 'config', 'overtime', 'history'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === tab ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-slate-800 rounded-xl border border-slate-700 p-5">
                <div className="flex items-center gap-3 mb-2">
                  <Mail size={20} className="text-blue-400" />
                  <span className="text-sm text-slate-400">Status</span>
                </div>
                <div className="text-lg font-semibold text-white">
                  {config?.enabled ? 'Active' : 'Disabled'}
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  Scheduled at {config?.schedule_hour || 18}:{String(config?.schedule_minute || 0).padStart(2, '0')} UTC
                </div>
              </div>
              <div className="bg-slate-800 rounded-xl border border-slate-700 p-5">
                <div className="flex items-center gap-3 mb-2">
                  <Send size={20} className="text-green-400" />
                  <span className="text-sm text-slate-400">Emails Sent</span>
                </div>
                <div className="text-lg font-semibold text-white">{emailLogs.length}</div>
                <div className="text-xs text-slate-500 mt-1">Recent sends (mocked)</div>
              </div>
              <div className="bg-slate-800 rounded-xl border border-slate-700 p-5">
                <div className="flex items-center gap-3 mb-2">
                  <Building2 size={20} className="text-purple-400" />
                  <span className="text-sm text-slate-400">Branches</span>
                </div>
                <div className="text-lg font-semibold text-white">{branches.length}</div>
                <div className="text-xs text-slate-500 mt-1">
                  {config?.send_per_branch ? 'Per-branch reports' : 'Combined report'}
                </div>
              </div>
              <div className="bg-slate-800 rounded-xl border border-slate-700 p-5">
                <div className="flex items-center gap-3 mb-2">
                  <Clock size={20} className="text-amber-400" />
                  <span className="text-sm text-slate-400">Last Run</span>
                </div>
                <div className="text-lg font-semibold text-white">
                  {history.length > 0 ? formatDateTime(history[0]?.run_at) : 'Never'}
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  {history.length > 0 ? history[0]?.trigger : '-'}
                </div>
              </div>
            </div>

            {/* Branch select for Send Now */}
            <div className="bg-slate-800 rounded-xl border border-slate-700 p-5">
              <h3 className="text-sm font-medium text-slate-300 mb-3">Send Report For</h3>
              <div className="flex gap-3 items-end">
                <div className="flex-1">
                  <select
                    value={selectedBranch}
                    onChange={(e) => setSelectedBranch(e.target.value)}
                    className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white"
                  >
                    <option value="">All Branches</option>
                    {branches.map(b => (
                      <option key={b.id} value={b.id}>{b.name}</option>
                    ))}
                  </select>
                </div>
                <button
                  onClick={handleSendNow}
                  disabled={sending}
                  className="flex items-center gap-2 px-5 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {sending ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
                  Send Now
                </button>
              </div>
            </div>

            {/* Recent Email Logs */}
            <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
              <div className="px-5 py-4 border-b border-slate-700 flex items-center justify-between">
                <h3 className="font-medium text-white">Recent Email Logs</h3>
                <button onClick={fetchData} className="text-slate-400 hover:text-white">
                  <RefreshCw size={16} />
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-xs text-slate-400 uppercase bg-slate-800/50">
                      <th className="px-4 py-3 font-medium">Sent At</th>
                      <th className="px-4 py-3 font-medium">To</th>
                      <th className="px-4 py-3 font-medium">Subject</th>
                      <th className="px-4 py-3 font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-700">
                    {emailLogs.length === 0 ? (
                      <tr>
                        <td colSpan={4} className="px-4 py-8 text-center text-slate-400">
                          No emails sent yet. Click "Send Report Now" to test.
                        </td>
                      </tr>
                    ) : (
                      emailLogs.map((log) => (
                        <tr key={log.id} className="hover:bg-slate-700/30">
                          <td className="px-4 py-3 text-sm text-slate-300">{formatDateTime(log.sent_at)}</td>
                          <td className="px-4 py-3 text-sm text-white">{(log.to || []).join(', ').substring(0, 40)}</td>
                          <td className="px-4 py-3 text-sm text-slate-300">{(log.subject || '').substring(0, 50)}</td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-1 rounded-full text-xs ${
                              log.status === 'mocked' 
                                ? 'bg-amber-500/20 text-amber-400' 
                                : 'bg-green-500/20 text-green-400'
                            }`}>
                              {log.status}
                            </span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Config Tab */}
        {activeTab === 'config' && config && (
          <ReportConfigEditor config={config} branches={branches} onUpdate={handleConfigUpdate} />
        )}

        {/* Overtime Tab */}
        {activeTab === 'overtime' && otConfig && (
          <OvertimeConfigView config={otConfig} token={token} onUpdate={fetchData} />
        )}

        {/* History Tab */}
        {activeTab === 'history' && (
          <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-700">
              <h3 className="font-medium text-white">Report Run History</h3>
            </div>
            <div className="divide-y divide-slate-700">
              {history.length === 0 ? (
                <div className="px-4 py-8 text-center text-slate-400">No report runs yet</div>
              ) : (
                history.map((run) => (
                  <div key={run.id} className="px-5 py-4 hover:bg-slate-700/30">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded text-xs ${
                            run.trigger === 'scheduled' ? 'bg-blue-500/20 text-blue-400' : 'bg-purple-500/20 text-purple-400'
                          }`}>{run.trigger}</span>
                          <span className={`px-2 py-0.5 rounded text-xs ${
                            run.status === 'completed' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                          }`}>{run.status}</span>
                        </div>
                        <div className="text-sm text-slate-300 mt-1">
                          {run.emails_sent} email(s) sent &bull; {run.branches_processed || '-'} branches
                        </div>
                      </div>
                      <div className="text-sm text-slate-400">{formatDateTime(run.run_at)}</div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Preview Modal */}
        {showPreview && previewData && (
          <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
            <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-3xl max-h-[85vh] overflow-y-auto">
              <div className="px-6 py-4 border-b border-slate-700 flex items-center justify-between sticky top-0 bg-slate-800">
                <h3 className="text-lg font-semibold text-white">Report Preview</h3>
                <button onClick={() => setShowPreview(false)} className="text-slate-400 hover:text-white">
                  <X size={20} />
                </button>
              </div>
              <div className="p-6">
                {/* Summary */}
                <div className="grid grid-cols-4 gap-3 mb-6">
                  <div className="bg-blue-500/10 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-blue-400">{previewData.summary?.clocked_in || 0}</div>
                    <div className="text-xs text-slate-400">Clocked In</div>
                  </div>
                  <div className="bg-amber-500/10 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-amber-400">{previewData.summary?.late_arrivals || 0}</div>
                    <div className="text-xs text-slate-400">Late</div>
                  </div>
                  <div className="bg-red-500/10 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-red-400">{previewData.summary?.absentees || 0}</div>
                    <div className="text-xs text-slate-400">Absent</div>
                  </div>
                  <div className="bg-green-500/10 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-green-400">{previewData.summary?.total_hours || 0}h</div>
                    <div className="text-xs text-slate-400">Total Hours</div>
                  </div>
                </div>

                {/* Worker Hours */}
                <h4 className="text-sm font-medium text-slate-300 mb-2">Worker Hours</h4>
                <div className="bg-slate-700/30 rounded-lg overflow-hidden mb-4">
                  {(previewData.worker_hours || []).length === 0 ? (
                    <div className="p-4 text-center text-slate-400 text-sm">No workers clocked in</div>
                  ) : (
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-xs text-slate-400 uppercase">
                          <th className="px-3 py-2 text-left">Employee</th>
                          <th className="px-3 py-2 text-left">Branch</th>
                          <th className="px-3 py-2 text-right">Hours</th>
                          <th className="px-3 py-2 text-right">OT</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-700">
                        {previewData.worker_hours.map((w, i) => (
                          <tr key={i}>
                            <td className="px-3 py-2 text-white">{w.name}</td>
                            <td className="px-3 py-2 text-slate-400">{w.branch}</td>
                            <td className="px-3 py-2 text-right text-white font-medium">{w.hours}h</td>
                            <td className="px-3 py-2 text-right text-amber-400">{w.overtime_hours > 0 ? `${w.overtime_hours}h` : '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>

                {/* Absentees */}
                {(previewData.absentees || []).length > 0 && (
                  <>
                    <h4 className="text-sm font-medium text-red-400 mb-2">Absentees ({previewData.absentees.length})</h4>
                    <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-3 mb-4">
                      <div className="flex flex-wrap gap-2">
                        {previewData.absentees.map((a, i) => (
                          <span key={i} className="bg-red-500/10 text-red-400 px-2 py-1 rounded text-xs">
                            {a.name}
                          </span>
                        ))}
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Report Config Editor
function ReportConfigEditor({ config, branches, onUpdate }) {
  const [form, setForm] = useState({
    global_recipients: (config.global_recipients || []).join(', '),
    hr_cc: (config.hr_cc || []).join(', '),
    finance_cc: (config.finance_cc || []).join(', '),
    enabled: config.enabled ?? true,
    send_per_branch: config.send_per_branch ?? true,
    schedule_hour: config.schedule_hour || 18,
    schedule_minute: config.schedule_minute || 0
  });
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    const parseEmails = (str) => str.split(',').map(e => e.trim()).filter(Boolean);
    await onUpdate({
      global_recipients: parseEmails(form.global_recipients),
      hr_cc: parseEmails(form.hr_cc),
      finance_cc: parseEmails(form.finance_cc),
      enabled: form.enabled,
      send_per_branch: form.send_per_branch,
      schedule_hour: form.schedule_hour,
      schedule_minute: form.schedule_minute
    });
    setSaving(false);
  };

  return (
    <div className="space-y-6">
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Report Configuration</h3>

        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={form.enabled}
                onChange={(e) => setForm({ ...form, enabled: e.target.checked })}
                className="sr-only peer"
              />
              <div className="w-9 h-5 bg-slate-600 rounded-full peer peer-checked:bg-blue-600 peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all"></div>
            </label>
            <span className="text-white text-sm">Enable automated daily reports</span>
          </div>

          <div className="flex items-center gap-3">
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={form.send_per_branch}
                onChange={(e) => setForm({ ...form, send_per_branch: e.target.checked })}
                className="sr-only peer"
              />
              <div className="w-9 h-5 bg-slate-600 rounded-full peer peer-checked:bg-blue-600 peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all"></div>
            </label>
            <span className="text-white text-sm">Send separate report per branch</span>
          </div>

          <div className="border-t border-slate-700 pt-4">
            <h4 className="text-sm font-medium text-slate-300 mb-3">Schedule</h4>
            <div className="flex gap-3 items-center">
              <span className="text-sm text-slate-400">Send at</span>
              <input
                type="number"
                min={0} max={23}
                value={form.schedule_hour}
                onChange={(e) => setForm({ ...form, schedule_hour: parseInt(e.target.value) || 18 })}
                className="w-16 bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-center"
              />
              <span className="text-slate-400">:</span>
              <input
                type="number"
                min={0} max={59}
                value={form.schedule_minute}
                onChange={(e) => setForm({ ...form, schedule_minute: parseInt(e.target.value) || 0 })}
                className="w-16 bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-center"
              />
              <span className="text-sm text-slate-400">UTC daily</span>
            </div>
          </div>

          <div className="border-t border-slate-700 pt-4">
            <h4 className="text-sm font-medium text-slate-300 mb-3">Recipients</h4>

            <div className="space-y-3">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Global Recipients (comma-separated emails)</label>
                <input
                  type="text"
                  value={form.global_recipients}
                  onChange={(e) => setForm({ ...form, global_recipients: e.target.value })}
                  placeholder="admin@company.com, hr@company.com"
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">HR CC (comma-separated)</label>
                <input
                  type="text"
                  value={form.hr_cc}
                  onChange={(e) => setForm({ ...form, hr_cc: e.target.value })}
                  placeholder="hr@company.com"
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Finance CC (comma-separated)</label>
                <input
                  type="text"
                  value={form.finance_cc}
                  onChange={(e) => setForm({ ...form, finance_cc: e.target.value })}
                  placeholder="finance@company.com"
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm"
                />
              </div>
            </div>
          </div>

          <div className="pt-4">
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-5 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Configuration'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Overtime Config View
function OvertimeConfigView({ config, token, onUpdate }) {
  const rules = config?.rules || {};

  return (
    <div className="space-y-6">
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-white">{config?.name || 'Overtime Configuration'}</h3>
            <p className="text-sm text-slate-400">
              Code: {config?.code || '-'} &bull; Effective: {config?.effective_date || '-'}
            </p>
          </div>
          <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-xs">
            {config?.status || 'active'}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-slate-700/30 rounded-lg p-4">
            <h4 className="text-sm font-medium text-blue-400 mb-3">Daily Thresholds</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-400">5-day work week</span>
                <span className="text-white font-medium">{rules.daily_threshold_5day || 9}hrs/day</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">6-day work week</span>
                <span className="text-white font-medium">{rules.daily_threshold_6day || 8}hrs/day</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Max daily hours</span>
                <span className="text-white font-medium">{rules.max_daily_hours || 12}hrs</span>
              </div>
            </div>
          </div>

          <div className="bg-slate-700/30 rounded-lg p-4">
            <h4 className="text-sm font-medium text-blue-400 mb-3">Weekly Thresholds</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-400">Weekly threshold</span>
                <span className="text-white font-medium">{rules.weekly_threshold || 45}hrs/week</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Max weekly overtime</span>
                <span className="text-white font-medium">{rules.max_weekly_overtime || 10}hrs</span>
              </div>
            </div>
          </div>
        </div>

        {/* Tiers */}
        <div className="mt-4">
          <h4 className="text-sm font-medium text-slate-300 mb-3">Rate Tiers</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            {Object.entries(config?.tiers || {}).map(([key, tier]) => (
              <div key={key} className="bg-slate-700/50 rounded-lg p-3">
                <div className="text-xs text-slate-400 uppercase mb-1">{key.replace('_', ' ')}</div>
                <div className="text-lg font-bold text-white">{tier.multiplier}x</div>
                <div className="text-xs text-slate-400 mt-1">{tier.description}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
          <p className="text-sm text-blue-400">
            <strong>SA BCEA Compliance:</strong> Standard overtime at 1.5x after 9hrs/day (5-day) or 
            8hrs/day (6-day). Weekly max 45hrs normal, 10hrs OT. Sunday &amp; public holidays at 2x rate.
          </p>
        </div>
      </div>
    </div>
  );
}
