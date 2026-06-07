const DEFAULT_BASE = "http://127.0.0.1:8000/api/v1";

export function getApiBase(): string {
  if (typeof window === "undefined") return DEFAULT_BASE;
  return localStorage.getItem("lms_api_base") || DEFAULT_BASE;
}
export function setApiBase(v: string) {
  localStorage.setItem("lms_api_base", v.replace(/\/$/, ""));
}

export function getAccess() {
  return typeof window === "undefined" ? null : localStorage.getItem("lms_access");
}
export function getRefresh() {
  return typeof window === "undefined" ? null : localStorage.getItem("lms_refresh");
}
export function setTokens(access?: string | null, refresh?: string | null) {
  if (typeof window === "undefined") return;
  if (access !== undefined) {
    if (access) localStorage.setItem("lms_access", access);
    else localStorage.removeItem("lms_access");
  }
  if (refresh !== undefined) {
    if (refresh) localStorage.setItem("lms_refresh", refresh);
    else localStorage.removeItem("lms_refresh");
  }
}

export class ApiError extends Error {
  status: number;
  data: any;
  constructor(status: number, data: any, message: string) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

function formatErr(data: any, status: number): string {
  if (!data) return `Request failed (${status})`;
  if (typeof data === "string") return data;
  if (data.detail) return String(data.detail);
  try {
    const parts: string[] = [];
    for (const [k, v] of Object.entries(data)) {
      parts.push(`${k}: ${Array.isArray(v) ? v.join(", ") : v}`);
    }
    return parts.join(" • ") || `Request failed (${status})`;
  } catch {
    return `Request failed (${status})`;
  }
}

async function doFetch(path: string, init: RequestInit & { auth?: boolean; isForm?: boolean } = {}) {
  const { auth = true, isForm = false, headers, ...rest } = init;
  const h: Record<string, string> = { Accept: "application/json", ...(headers as any) };
  if (!isForm && rest.body && !h["Content-Type"]) h["Content-Type"] = "application/json";
  if (auth) {
    const t = getAccess();
    if (t) h["Authorization"] = `Bearer ${t}`;
  }
  const url = path.startsWith("http") ? path : `${getApiBase()}${path}`;
  return fetch(url, { ...rest, headers: h });
}

async function refreshToken(): Promise<boolean> {
  const r = getRefresh();
  if (!r) return false;
  const res = await fetch(`${getApiBase()}/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh: r }),
  });
  if (!res.ok) return false;
  const data = await res.json();
  if (data.access) {
    setTokens(data.access, data.refresh ?? undefined);
    return true;
  }
  return false;
}

export async function api<T = any>(path: string, init: RequestInit & { auth?: boolean; isForm?: boolean } = {}): Promise<T> {
  let res = await doFetch(path, init);
  if (res.status === 401 && init.auth !== false) {
    if (await refreshToken()) {
      res = await doFetch(path, init);
    }
  }
  const text = await res.text();
  let data: any = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = text; }
  if (!res.ok) throw new ApiError(res.status, data, formatErr(data, res.status));
  return data as T;
}

// Convenience helpers
export const apiGet = <T = any>(p: string) => api<T>(p, { method: "GET" });
export const apiPost = <T = any>(p: string, body?: any, opts: any = {}) =>
  api<T>(p, { method: "POST", body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined, isForm: body instanceof FormData, ...opts });
export const apiPatch = <T = any>(p: string, body?: any) =>
  api<T>(p, { method: "PATCH", body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined, isForm: body instanceof FormData });
export const apiDelete = <T = any>(p: string) => api<T>(p, { method: "DELETE" });