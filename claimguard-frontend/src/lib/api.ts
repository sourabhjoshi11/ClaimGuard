const STORAGE_KEY = "claimguard_auth";
const BACKEND_KEY = "claimguard_backend";
const DEFAULT_BACKEND = import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:8000";

export interface AuthTokens {
  access: string;
  refresh: string;
  user: { username: string; email?: string };
}

export function getBackendUrl(): string {
  if (typeof window === "undefined") return DEFAULT_BACKEND;
  return localStorage.getItem(BACKEND_KEY) || DEFAULT_BACKEND;
}

export function setBackendUrl(url: string) {
  localStorage.setItem(BACKEND_KEY, url.replace(/\/$/, ""));
}

export function resolveMediaUrl(url: string | null | undefined): string {
  if (!url) return "";
  if (/^(https?:)?\/\//i.test(url) || url.startsWith("data:") || url.startsWith("blob:")) {
    return url;
  }

  const backend = getBackendUrl().replace(/\/$/, "");
  const path = url.startsWith("/") ? url : `/${url}`;
  return `${backend}${path}`;
}

export function getStoredAuth(): AuthTokens | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthTokens;
  } catch {
    return null;
  }
}

export function setStoredAuth(auth: AuthTokens | null) {
  if (auth) localStorage.setItem(STORAGE_KEY, JSON.stringify(auth));
  else localStorage.removeItem(STORAGE_KEY);
}

async function refreshAccess(refresh: string): Promise<string | null> {
  try {
    const res = await fetch(`${getBackendUrl()}/api/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
    });
    if (!res.ok) return null;
    const data = await res.json();
    return data.access ?? null;
  } catch {
    return null;
  }
}

export interface ApiOptions {
  method?: string;
  body?: unknown;
  formData?: FormData;
  auth?: boolean;
}

function formatApiError(data: unknown, status: number): string {
  if (!data || typeof data !== "object") return `Request failed (${status})`;

  if ("error" in data && typeof data.error === "string") return data.error;
  if ("detail" in data && typeof data.detail === "string") return data.detail;

  const fieldMessages = Object.entries(data)
    .flatMap(([field, value]) => {
      if (Array.isArray(value)) return value.map((item) => `${field}: ${String(item)}`);
      if (typeof value === "string") return [`${field}: ${value}`];
      return [];
    })
    .filter(Boolean);

  return fieldMessages[0] || `Request failed (${status})`;
}

export async function apiRequest<T = unknown>(path: string, opts: ApiOptions = {}): Promise<T> {
  const { method = "GET", body, formData, auth = true } = opts;
  const url = `${getBackendUrl()}${path}`;
  const headers: Record<string, string> = {};
  let stored = getStoredAuth();

  if (auth && stored?.access) headers["Authorization"] = `Bearer ${stored.access}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";

  const init: RequestInit = {
    method,
    headers,
    body: formData ? formData : body !== undefined ? JSON.stringify(body) : undefined,
  };

  let res = await fetch(url, init);

  if (res.status === 401 && auth && stored?.refresh) {
    const newAccess = await refreshAccess(stored.refresh);
    if (newAccess) {
      stored = { ...stored, access: newAccess };
      setStoredAuth(stored);
      headers["Authorization"] = `Bearer ${newAccess}`;
      res = await fetch(url, { ...init, headers });
    }
  }

  const text = await res.text();
  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }

  if (!res.ok) {
    throw new Error(formatApiError(data, res.status));
  }

  return data as T;
}

// Endpoint helpers
export interface Claim {
  id: number;
  image_url: string;
  status: string;
  created_at?: string;
  media_type?: string;
  workflow_result?: WorkflowResult | null;
}

export interface Anomaly {
  item: string;
  issue: string;
  severity: string;
  estimated_cost?: number;
}

export interface WorkflowResult {
  status: string;
  anomalies?: Anomaly[];
  anamolies?: Anomaly[];
  total_claim_value: number;
}

export interface UploadResponse {
  msg: string;
  image_url: string;
  claim_id: number;
  media_type: string;
  workflow_result: WorkflowResult;
}

export function getWorkflowAnomalies(workflow?: WorkflowResult | null): Anomaly[] {
  return workflow?.anomalies ?? workflow?.anamolies ?? [];
}

export const api = {
  register: (payload: { username: string; email: string; password: string }) =>
    apiRequest("/api/users/register/", { method: "POST", body: payload, auth: false }),

  login: (payload: { identifier: string; password: string }) => {
    const isEmail = payload.identifier.includes("@");
    const body = isEmail
      ? { email: payload.identifier, password: payload.password }
      : { username: payload.identifier, password: payload.password };
    return apiRequest<{ access: string; refresh: string; user?: { username: string; email?: string } }>(
      "/api/login/",
      { method: "POST", body, auth: false },
    );
  },

  listClaims: () => apiRequest<Claim[] | { results?: Claim[]; claims?: Claim[] }>("/api/claims/uploads/"),

  uploadClaim: (formData: FormData) =>
    apiRequest<UploadResponse>("/api/claims/uploads/", { method: "POST", formData }),

  getClaim: (id: string | number) =>
    apiRequest<Claim & { workflow_result?: WorkflowResult }>(`/api/claims/uploads/${id}/`),
};
