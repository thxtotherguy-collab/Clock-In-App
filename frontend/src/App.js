/**
 * Workforce Management - Main App Component
 * Role-based routing: Workers -> WorkerDashboard, Admins -> AdminLayout
 */
import React, { useState, useEffect } from 'react';
import LoginScreen from './components/LoginScreen';
import WorkerDashboard from './components/WorkerDashboard';
import AdminLayout from './components/admin/AdminLayout';
import AdminDashboard from './components/admin/AdminDashboard';
import TimeEntriesManager from './components/admin/TimeEntriesManager';
import ApprovalsManager from './components/admin/ApprovalsManager';
import UsersManager from './components/admin/UsersManager';
import BranchesManager from './components/admin/BranchesManager';
import ExportsPage from './components/admin/ExportsPage';
import AuditLogsViewer from './components/admin/AuditLogsViewer';
import { authAPI } from './services/api';
import { initOfflineDB, saveAuthToken, clearAuthToken } from './services/offline';
import './App.css';

const ADMIN_ROLES = ['SUPER_ADMIN', 'BRANCH_ADMIN', 'TEAM_LEADER'];

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showInstallPrompt, setShowInstallPrompt] = useState(false);
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [adminPage, setAdminPage] = useState('dashboard');

  // Initialize app
  useEffect(() => {
    initApp();
    registerServiceWorker();
    setupInstallPrompt();
  }, []);

  const initApp = async () => {
    try {
      // Initialize offline DB
      await initOfflineDB();

      // Check for existing session
      const token = localStorage.getItem('wfm_token');
      const savedUser = localStorage.getItem('wfm_user');

      if (token && savedUser) {
        try {
          // Verify token is still valid
          const response = await authAPI.getMe();
          setUser(response.user);
          await saveAuthToken(token);
        } catch (err) {
          // Token invalid, try to use saved user for offline
          if (!navigator.onLine && savedUser) {
            setUser(JSON.parse(savedUser));
          } else {
            // Clear invalid session
            localStorage.removeItem('wfm_token');
            localStorage.removeItem('wfm_refresh');
            localStorage.removeItem('wfm_user');
            await clearAuthToken();
          }
        }
      }
    } catch (err) {
      console.error('[App] Init error:', err);
    } finally {
      setLoading(false);
    }
  };

  const registerServiceWorker = async () => {
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.register('/service-worker.js');
        console.log('[App] Service Worker registered:', registration.scope);
        window.registration = registration;
      } catch (err) {
        console.log('[App] Service Worker registration failed:', err);
      }
    }
  };

  const setupInstallPrompt = () => {
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      // Show install prompt after delay
      setTimeout(() => setShowInstallPrompt(true), 5000);
    });
  };

  const handleInstall = async () => {
    if (!deferredPrompt) return;

    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    console.log('[App] Install prompt outcome:', outcome);
    setDeferredPrompt(null);
    setShowInstallPrompt(false);
  };

  const handleLogin = async (userData, token) => {
    setUser(userData);
    await saveAuthToken(token);
    // Reset admin page on login
    setAdminPage('dashboard');
  };

  const handleLogout = async () => {
    localStorage.removeItem('wfm_token');
    localStorage.removeItem('wfm_refresh');
    localStorage.removeItem('wfm_user');
    await clearAuthToken();
    setUser(null);
    setAdminPage('dashboard');
  };

  const isAdminUser = user && ADMIN_ROLES.includes(user.role);
  const token = localStorage.getItem('wfm_token');

  // Loading screen
  if (loading) {
    return (
      <div className="min-h-screen bg-[#0A0F1C] flex items-center justify-center">
        <div className="text-center">
          <div className="spinner mx-auto mb-4"></div>
          <p className="text-gray-400 text-sm">Loading...</p>
        </div>
      </div>
    );
  }

  // Render admin page content
  const renderAdminContent = () => {
    switch (adminPage) {
      case 'dashboard':
        return (
          <AdminDashboard
            user={user}
            token={token}
            onLogout={handleLogout}
            onNavigate={setAdminPage}
            embedded
          />
        );
      case 'time-entries':
        return (
          <TimeEntriesManager
            token={token}
            user={user}
            onBack={() => setAdminPage('dashboard')}
            embedded
          />
        );
      case 'approvals':
        return <ApprovalsManager token={token} user={user} />;
      case 'users':
        return (
          <UsersManager
            token={token}
            user={user}
            onBack={() => setAdminPage('dashboard')}
            embedded
          />
        );
      case 'branches':
        return <BranchesManager token={token} user={user} />;
      case 'exports':
        return <ExportsPage token={token} user={user} />;
      case 'audit-logs':
        return <AuditLogsViewer token={token} user={user} />;
      default:
        return (
          <AdminDashboard
            user={user}
            token={token}
            onLogout={handleLogout}
            onNavigate={setAdminPage}
            embedded
          />
        );
    }
  };

  return (
    <div className="App">
      {/* Main Content */}
      {user ? (
        isAdminUser ? (
          <AdminLayout
            user={user}
            token={token}
            onLogout={handleLogout}
            activePage={adminPage}
            onNavigate={setAdminPage}
          >
            {renderAdminContent()}
          </AdminLayout>
        ) : (
          <WorkerDashboard user={user} onLogout={handleLogout} />
        )
      ) : (
        <LoginScreen onLogin={handleLogin} />
      )}

      {/* PWA Install Prompt */}
      {showInstallPrompt && (
        <div className="install-prompt" data-testid="install-prompt">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="font-semibold text-white">Install Workforce Clock</p>
              <p className="text-sm text-gray-400">Add to home screen for offline access</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setShowInstallPrompt(false)}
                className="px-4 py-2 text-sm text-gray-400"
              >
                Later
              </button>
              <button
                onClick={handleInstall}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium"
                data-testid="install-button"
              >
                Install
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
