import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { getAccess, setTokens } from "./api";
import { lmsApi } from "./lms-api";

const USER_STORAGE_KEY = "lms_user";

export interface UserProfile {
  id?: string | number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  phone_number?: string;
  bio?: string;
  profile_image?: string | null;
  staff_member?: boolean;
  is_staff?: boolean;
  is_superuser?: boolean;
  role?: string;
}

interface AuthCtx {
  user: UserProfile | null;
  loading: boolean;
  isAdmin: boolean;
  login: (username: string, password: string) => Promise<UserProfile | null>;
  register: (data: { username: string; email: string; password: string; first_name?: string; last_name?: string }) => Promise<UserProfile | null>;
  logout: () => void;
  refresh: () => Promise<UserProfile | null>;
}

const Ctx = createContext<AuthCtx | null>(null);

function getStoredUser(): UserProfile | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as UserProfile;
  } catch {
    localStorage.removeItem(USER_STORAGE_KEY);
    return null;
  }
}

function setStoredUser(user: UserProfile | null) {
  if (typeof window === "undefined") return;
  if (user) localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
  else localStorage.removeItem(USER_STORAGE_KEY);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    if (!getAccess()) { setUser(null); setStoredUser(null); setLoading(false); return null; }
    try {
      const cached = getStoredUser();
      const p = await lmsApi.auth.getProfile() as UserProfile;
      const merged: UserProfile = {
        ...cached,
        ...p,
        profile_image: p.profile_image || cached?.profile_image || null,
      };
      setUser(merged);
      setStoredUser(merged);
      return merged;
    } catch {
      const cached = getStoredUser();
      if (cached && getAccess()) {
        setUser(cached);
        return cached;
      }
      setUser(null);
      setStoredUser(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const login = useCallback(async (username: string, password: string) => {
    const res = await lmsApi.auth.login({ username, password });
    const access = res.access || res.access_token;
    const refreshToken = res.refresh || res.refresh_token;
    setTokens(access || null, refreshToken || null);

    // Prefer user payload from login if backend includes role/staff flags there.
    const loginUser = res.user as UserProfile | undefined;
    if (loginUser) {
      setUser(loginUser);
      setStoredUser(loginUser);
      setLoading(false);
      return loginUser;
    }

    return await refresh();
  }, [refresh]);

  const register = useCallback(async (data: any) => {
    await lmsApi.auth.register(data);
    return await login(data.username, data.password);
  }, [login]);

  const logout = useCallback(() => {
    setTokens(null, null);
    setUser(null);
    setStoredUser(null);
  }, []);

  const value = useMemo<AuthCtx>(() => ({
    user, loading, refresh, login, register, logout,
    isAdmin: !!(user?.staff_member || user?.is_staff || user?.is_superuser || user?.role === "admin"),
  }), [user, loading, refresh, login, register, logout]);

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth must be used inside AuthProvider");
  return v;
}