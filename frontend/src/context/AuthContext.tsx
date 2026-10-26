import { createContext, useCallback, useContext, useEffect, useState, type PropsWithChildren } from "react";
import { api, getTokens, setTokens } from "../services/api";
import type { Tokens, User } from "../types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const loadProfile = useCallback(async () => {
    if (!getTokens()) return;
    try { setUser(await api<User>("/auth/me/")); } catch { setTokens(null); setUser(null); }
  }, []);

  useEffect(() => {
    const expire = () => setUser(null);
    window.addEventListener("sentinel-vault:auth-expired", expire);
    loadProfile().finally(() => setLoading(false));
    return () => window.removeEventListener("sentinel-vault:auth-expired", expire);
  }, [loadProfile]);

  const login = async (email: string, password: string) => {
    const tokens = await api<Tokens>("/auth/login/", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password }),
    });
    setTokens(tokens);
    setUser(await api<User>("/auth/me/"));
  };

  const logout = async () => {
    const tokens = getTokens();
    try {
      if (tokens?.refresh) await api<void>("/auth/logout/", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ refresh: tokens.refresh }) });
    } finally { setTokens(null); setUser(null); }
  };

  return <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
