import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const checkAuth = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.get('/auth/me');
      if (res && res.success && res.data) {
        // Handle user object
        const user = res.data.user || res.data;
        setCurrentUser(user);
        setError(null);
      } else {
        setCurrentUser(null);
      }
    } catch (err) {
      // 401 simply means not logged in
      setCurrentUser(null);
      if (err.status !== 401) {
        setError(err.message || 'Failed to authenticate');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = async (identifier, password) => {
    setError(null);
    const res = await api.post('/auth/login', { identifier, password });
    if (res && res.success) {
      if (res.data?.user || res.data) {
        setCurrentUser(res.data.user || res.data);
      }
      await checkAuth();
      return res;
    }
    throw new Error(res?.message || 'Login failed');
  };

  const register = async (userData) => {
    setError(null);
    const res = await api.post('/auth/register', userData);
    if (res && res.success) {
      if (res.data?.user || res.data) {
        setCurrentUser(res.data.user || res.data);
      }
      await checkAuth();
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
