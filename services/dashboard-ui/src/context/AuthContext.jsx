import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for stored user and token on mount
    const storedUser = localStorage.getItem('user');
    const storedToken = localStorage.getItem('oauth_token');
    
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        localStorage.removeItem('user');
      }
    }
    
    if (storedToken) {
      setToken(storedToken);
    }
    
    setLoading(false);
  }, []);

  const login = (userData, accessToken = null) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
    
    if (accessToken) {
      setToken(accessToken);
      localStorage.setItem('oauth_token', accessToken);
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('user');
    localStorage.removeItem('oauth_token');
  };

  const value = {
    user,
    token,
    loading,
    login,
    logout,
    isAuthenticated: !!user
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
