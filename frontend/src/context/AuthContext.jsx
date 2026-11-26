import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

const AuthContext = createContext(null);
const USER_STORAGE_KEY = 'campusconnect_user';

export function AuthProvider({ children }) {
  // Never treat locally cached user as proof of authentication.
  // Initial state is unauthenticated; server verification occurs on mount.
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const checkAuth = useCallback(async () => {
    try {
      const res = await api.get('/auth/me');
      if (res && res.success && res.data) {
        const user = res.data.user || res.data;
        setCurrentUser(user);
        try {
          sessionStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
        } catch {}
        setError(null);
        return user;
      } else {
        setCurrentUser(null);
        try {
          sessionStorage.removeItem(USER_STORAGE_KEY);
          sessionStorage.removeItem('campusconnect_token');
        } catch {}
        return null;
      }
    } catch (err) {
      setCurrentUser(null);
      try {
        sessionStorage.removeItem(USER_STORAGE_KEY);
        sessionStorage.removeItem('campusconnect_token');
      } catch {}
      if (err.status !== 401) {
        setError(err.message || 'Failed to authenticate');
      }
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // Listen for unauthorized events dispatched on any 401 from protected APIs
  useEffect(() => {
    const handleUnauthorized = () => {
      setCurrentUser(null);
      try {
        sessionStorage.removeItem(USER_STORAGE_KEY);
        sessionStorage.removeItem('campusconnect_token');
      } catch {}
    };
    window.addEventListener('campusconnect:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('campusconnect:unauthorized', handleUnauthorized);
  }, []);

  const login = async (identifier, password) => {
    setError(null);
    const res = await api.post('/auth/login', { identifier, password });
    if (res && res.success) {
      const user = res.data?.user || res.data;
      if (user) {
        setCurrentUser(user);
        try {
          sessionStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
        } catch {}
      }
      return res;
    }
    throw new Error(res?.message || 'Login failed');
  };

  const register = async (userData) => {
    setError(null);
    const res = await api.post('/auth/register', userData);
    if (res && res.success) {
      const user = res.data?.user || res.data;
      if (user) {
        setCurrentUser(user);
        try {
          sessionStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
        } catch {}
      }
      return res;
    }
    throw new Error(res?.message || 'Registration failed');
  };

  const logout = async () => {
    try {
      await api.post('/auth/logout');
    } catch {
      // Ignore network errors on logout
    } finally {
      try {
        sessionStorage.removeItem(USER_STORAGE_KEY);
        sessionStorage.removeItem('campusconnect_token');
      } catch {}
      setCurrentUser(null);
    }
  };

  const refreshUser = async () => {
    await checkAuth();
  };

  return (
    <AuthContext.Provider
      value={{
        currentUser,
        isAuthenticated: !!currentUser,
        loading,
        error,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
