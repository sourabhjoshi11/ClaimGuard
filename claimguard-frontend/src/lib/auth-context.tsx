import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { getStoredAuth, setStoredAuth, type AuthTokens, api } from "./api";

interface AuthContextValue {
  auth: AuthTokens | null;
  isAuthenticated: boolean;
  login: (identifier: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [auth, setAuth] = useState<AuthTokens | null>(null);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setAuth(getStoredAuth());
    setHydrated(true);
  }, []);

  const login = async (identifier: string, password: string) => {
    const data = await api.login({ identifier, password });
    const next: AuthTokens = {
      access: data.access,
      refresh: data.refresh,
      user: data.user ?? { username: identifier },
    };
    setStoredAuth(next);
    setAuth(next);
  };

  const register = async (username: string, email: string, password: string) => {
    await api.register({ username, email, password });
    await login(username, password);
  };

  const logout = () => {
    setStoredAuth(null);
    setAuth(null);
  };

  if (!hydrated) return null;

  return (
    <AuthContext.Provider
      value={{ auth, isAuthenticated: !!auth, login, register, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
