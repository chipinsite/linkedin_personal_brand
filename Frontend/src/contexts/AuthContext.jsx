import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api, setOnAuthError } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => api.getStoredUser());
  const [isAuthenticated, setIsAuthenticated] = useState(() => api.isAuthenticated());
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Handle auth errors (e.g., token expiration) globally
  const handleAuthError = useCallback(() => {
    setUser(null);
    setIsAuthenticated(false);
  }, []);

  // Set up the auth error callback
  useEffect(() => {
    setOnAuthError(handleAuthError);
    return () => setOnAuthError(null);
  }, [handleAuthError]);

  // Verify token on mount
  useEffect(() => {
    async function verifyAuth() {
      if (!api.isAuthenticated()) {
        setIsLoading(false);
        return;
      }

      try {
        const currentUser = await api.getCurrentUser();
        setUser(currentUser);
        setIsAuthenticated(true);
      } catch {
        // Token is invalid or expired
        api.clearAuth();
        setUser(null);
        setIsAuthenticated(false);
      } finally {
        setIsLoading(false);
      }
    }

    verifyAuth();
  }, []);

  const login = useCallback(async (emailOrUsername, password) => {
    setError(null);
    setIsLoading(true);
    try {
      const { user: loggedInUser } = await api.login(emailOrUsername, password);
      setUser(loggedInUser);
      setIsAuthenticated(true);
      return loggedInUser;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    setIsLoading(true);
    try {
      await api.logout();
    } finally {
      setUser(null);
      setIsAuthenticated(false);
      setIsLoading(false);
    }
  }, []);

  const logoutAll = useCallback(async () => {
    setIsLoading(true);
    try {
      await api.logoutAll();
    } finally {
      setUser(null);
      setIsAuthenticated(false);
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (email, username, password, fullName = null) => {
    setError(null);
    setIsLoading(true);
    try {
      const newUser = await api.register(email, username, password, fullName);
      return newUser;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const changePassword = useCallback(async (currentPassword, newPassword) => {
    setError(null);
    try {
      await api.changePassword(currentPassword, newPassword);
      // After password change, user needs to log in again
      await logout();
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [logout]);

  const refreshUser = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const currentUser = await api.getCurrentUser();
      setUser(currentUser);
    } catch {
      // Ignore errors during refresh
    }
  }, [isAuthenticated]);

  const value = {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
    logoutAll,
    register,
    changePassword,
    refreshUser,
    clearError: () => setError(null),
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
