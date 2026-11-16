import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api } from "./api";
import type { User } from "./types";

type AuthValue = {
  user: User | null; loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, displayName: string, password: string) => Promise<void>;
  logout: () => Promise<void>; refresh: () => Promise<void>;
};
const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const refresh = async () => {
    try { setUser(await api<User>("/api/auth/me")); } catch { setUser(null); } finally { setLoading(false); }
  };
  useEffect(() => { void refresh(); }, []);
  const value = useMemo<AuthValue>(() => ({
    user, loading, refresh,
    login: async (email, password) => setUser(await api<User>("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) })),
    register: async (email, display_name, password) => setUser(await api<User>("/api/auth/register", { method: "POST", body: JSON.stringify({ email, display_name, password }) })),
    logout: async () => { await api("/api/auth/logout", { method: "POST" }); setUser(null); sessionStorage.clear(); },
  }), [user, loading]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}

