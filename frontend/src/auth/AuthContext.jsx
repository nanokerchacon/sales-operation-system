import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { clearStoredToken, getStoredToken, setStoredToken } from "./tokenStorage";
import { authApi } from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isActive = true;

    async function loadSession() {
      const token = getStoredToken();
      if (!token) {
        if (isActive) {
          setLoading(false);
        }
        return;
      }

      try {
        const session = await authApi.me();
        if (!isActive) {
          return;
        }
        setUser(session.user);
      } catch {
        clearStoredToken();
        if (isActive) {
          setUser(null);
        }
      } finally {
        if (isActive) {
          setLoading(false);
        }
      }
    }

    loadSession();

    return () => {
      isActive = false;
    };
  }, []);

  async function login(email, password) {
    const response = await authApi.login({ email, password });
    setStoredToken(response.access_token);
    setUser(response.user);
    return response.user;
  }

  function logout() {
    clearStoredToken();
    setUser(null);
  }

  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      login,
      logout,
    }),
    [user, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
