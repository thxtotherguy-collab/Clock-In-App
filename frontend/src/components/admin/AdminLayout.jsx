/**
 * Admin Layout - Sidebar navigation + content area
 * Clean, professional, data-focused design
 */
import React, { useState } from 'react';
import {
  LayoutDashboard, Clock, CheckCircle, Users, Building2,
  Download, FileText, Menu, X, LogOut, ChevronRight, Shield, Mail
} from 'lucide-react';

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, description: 'Overview & stats' },
  { id: 'time-entries', label: 'Time Entries', icon: Clock, description: 'View & edit entries' },
  { id: 'approvals', label: 'Approvals', icon: CheckCircle, description: 'Review timesheets' },
  { id: 'users', label: 'Workers', icon: Users, description: 'Manage employees' },
  { id: 'branches', label: 'Branches', icon: Building2, description: 'Locations & geofence', adminOnly: true },
  { id: 'reports', label: 'Reports', icon: Mail, description: 'Automated emails' },
  { id: 'exports', label: 'Exports', icon: Download, description: 'CSV & Excel reports' },
  { id: 'audit-logs', label: 'Audit Logs', icon: FileText, description: 'System activity', adminOnly: true },
];

export default function AdminLayout({ user, token, onLogout, children, activePage, onNavigate }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const isSuperAdmin = user?.role === 'SUPER_ADMIN';

  const filteredNav = NAV_ITEMS.filter(item => {
    if (item.adminOnly && !isSuperAdmin) return false;
    return true;
  });

  return (
    <div className="min-h-screen bg-slate-900 flex" data-testid="admin-layout">
      {/* Sidebar - Desktop */}
      <aside className="hidden lg:flex lg:flex-col lg:w-64 bg-slate-800 border-r border-slate-700 fixed inset-y-0 left-0 z-30">
        {/* Logo/Brand */}
        <div className="h-16 flex items-center px-6 border-b border-slate-700">
          <Shield size={24} className="text-blue-500 mr-3" />
          <div>
            <h2 className="text-sm font-bold text-white">Workforce</h2>
            <p className="text-[10px] text-slate-400 uppercase tracking-wider">Admin Panel</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
          {filteredNav.map((item) => {
            const Icon = item.icon;
            const isActive = activePage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150 group ${
                  isActive
                    ? 'bg-blue-600/15 text-blue-400 border border-blue-500/20'
                    : 'text-slate-400 hover:text-white hover:bg-slate-700/50 border border-transparent'
                }`}
                data-testid={`nav-${item.id}`}
              >
                <Icon size={18} className={isActive ? 'text-blue-400' : 'text-slate-500 group-hover:text-slate-300'} />
                <div className="text-left">
                  <div className={`font-medium ${isActive ? 'text-blue-400' : ''}`}>{item.label}</div>
                </div>
              </button>
            );
          })}
        </nav>

        {/* User Info */}
        <div className="border-t border-slate-700 p-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-blue-600/20 flex items-center justify-center">
              <span className="text-xs font-bold text-blue-400">
                {user?.first_name?.[0]}{user?.last_name?.[0]}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">
                {user?.first_name} {user?.last_name}
              </p>
              <p className="text-xs text-slate-400 truncate">
                {user?.role?.replace('_', ' ')}
              </p>
            </div>
            <button
              onClick={onLogout}
              className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
              title="Sign Out"
              data-testid="logout-button"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-40 bg-slate-800 border-b border-slate-700 h-14 flex items-center px-4">
        <button
          onClick={() => setSidebarOpen(true)}
          className="p-2 text-slate-400 hover:text-white"
        >
          <Menu size={20} />
        </button>
        <div className="flex items-center ml-3">
          <Shield size={18} className="text-blue-500 mr-2" />
          <span className="font-semibold text-white text-sm">Workforce Admin</span>
        </div>
        <button
          onClick={onLogout}
          className="ml-auto p-2 text-slate-400 hover:text-red-400"
        >
          <LogOut size={18} />
        </button>
      </div>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div className="lg:hidden fixed inset-0 z-50">
          <div className="absolute inset-0 bg-black/60" onClick={() => setSidebarOpen(false)} />
          <aside className="absolute left-0 top-0 bottom-0 w-72 bg-slate-800 border-r border-slate-700">
            <div className="h-14 flex items-center justify-between px-4 border-b border-slate-700">
              <div className="flex items-center">
                <Shield size={20} className="text-blue-500 mr-2" />
                <span className="font-semibold text-white">Admin Panel</span>
              </div>
              <button onClick={() => setSidebarOpen(false)} className="p-2 text-slate-400">
                <X size={18} />
              </button>
            </div>
            <nav className="py-4 px-3 space-y-1">
              {filteredNav.map((item) => {
                const Icon = item.icon;
                const isActive = activePage === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => { onNavigate(item.id); setSidebarOpen(false); }}
                    className={`w-full flex items-center gap-3 px-3 py-3 rounded-lg text-sm transition-all ${
                      isActive
                        ? 'bg-blue-600/15 text-blue-400'
                        : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
                    }`}
                  >
                    <Icon size={18} />
                    <span className="font-medium">{item.label}</span>
                  </button>
                );
              })}
            </nav>
          </aside>
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 lg:ml-64 min-h-screen">
        <div className="pt-14 lg:pt-0">
          {children}
        </div>
      </main>
    </div>
  );
}
