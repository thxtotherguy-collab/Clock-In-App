/**
 * Login Screen - Mobile Optimized
 */
import React, { useState } from 'react';
import { Clock, Eye, EyeOff, Loader2 } from 'lucide-react';
import { authAPI } from '../services/api';

export default function LoginScreen({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [mode, setMode] = useState('login'); // login | register

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!email || !password) {
      setError('Please fill in all fields');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      let result;
      if (mode === 'login') {
        result = await authAPI.login(email, password);
      } else {
        const [firstName, ...lastParts] = email.split('@')[0].split('.');
        result = await authAPI.register({
          email,
          password,
          first_name: firstName || 'User',
          last_name: lastParts.join(' ') || 'Worker'
        });
      }

      // Save token
      localStorage.setItem('wfm_token', result.access_token);
      localStorage.setItem('wfm_refresh', result.refresh_token);
      localStorage.setItem('wfm_user', JSON.stringify(result.user));

      onLogin(result.user, result.access_token);

    } catch (err) {
      console.error('[Login] Error:', err);
      setError(err.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0A0F1C] flex flex-col items-center justify-center p-6" data-testid="login-screen">
      {/* Logo */}
      <div className="mb-8 text-center">
        <div className="w-20 h-20 bg-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <Clock size={40} className="text-white" />
        </div>
        <h1 className="text-2xl font-bold text-white">Workforce Clock</h1>
        <p className="text-gray-400 text-sm mt-1">Clock in with GPS tracking</p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-4">
        {/* Email */}
        <div>
          <input
            type="email"
            placeholder="Email address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="login-input"
            autoComplete="email"
            autoCapitalize="none"
            data-testid="email-input"
          />
        </div>

        {/* Password */}
        <div className="relative">
          <input
            type={showPassword ? 'text' : 'password'}
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="login-input pr-12"
            autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            data-testid="password-input"
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400"
          >
            {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-lg text-sm" data-testid="login-error">
            {error}
          </div>
        )}

        {/* Submit */}
        <button
          type="submit"
          disabled={loading}
          className="login-button flex items-center justify-center gap-2"
          data-testid="submit-button"
        >
          {loading && <Loader2 size={20} className="animate-spin" />}
          {mode === 'login' ? 'Sign In' : 'Create Account'}
        </button>

        {/* Toggle Mode */}
        <div className="text-center">
          <button
            type="button"
            onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
            className="text-sm text-blue-400"
            data-testid="toggle-mode"
          >
            {mode === 'login' ? "Don't have an account? Register" : 'Already have an account? Sign In'}
          </button>
        </div>
      </form>

      {/* PWA Install Hint */}
      <p className="text-xs text-gray-500 mt-8 text-center max-w-xs">
        Add to home screen for the best experience with offline support
      </p>
    </div>
  );
}
