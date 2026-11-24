import type { FieldIssue, Receipt, Status, Ticket } from "./types";

const BASE = import.meta.env.VITE_API_URL ?? "";
const TOKEN_KEY = "desk_token";

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string, public fields: FieldIssue[] = []) {
    super(message);
  }
}

export const getToken = () => sessionStorage.getItem(TOKEN_KEY);
export const setToken = (t: string) => sessionStorage.setItem(TOKEN_KEY, t);
export const clearToken = () => sessionStorage.removeItem(TOKEN_KEY);

async function request<T>(path: string, init: RequestInit = {}, auth = true): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  const token = getToken();
  if (auth && token) headers.set("Authorization", `Bearer ${token}`);

  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(0, "network_error", "Cannot reach the server. Check your connection and try again.");
  }
  const text = await res.text();
  let data: any = null;
  try { data = text ? JSON.parse(text) : null; } catch { /* non-JSON error page */ }

  if (!res.ok) {
    const e = data?.error;
    throw new ApiError(res.status, e?.code ?? `http_${res.status}`, e?.message ?? `Request failed (${res.status}).`, e?.fields ?? []);
  }
  return data as T;
}

export const api = {
  submitTicket: (body: { name: string; email: string; message: string }) =>
    request<Receipt>("/api/tickets", { method: "POST", body: JSON.stringify(body) }, false),
  login: (username: string, password: string) =>
    request<{ access_token: string }>("/api/auth/login", { method: "POST", body: JSON.stringify({ username, password }) }, false),
  listTickets: (p: { category?: string; status?: string }) => {
    const q = new URLSearchParams();
    if (p.category) q.set("category", p.category);
    if (p.status) q.set("status", p.status);
    const qs = q.toString();
    return request<Ticket[]>(`/api/tickets${qs ? `?${qs}` : ""}`);
  },
  getTicket: (id: number) => request<Ticket>(`/api/tickets/${id}`),
  categories: () => request<string[]>("/api/categories"),
  updateStatus: (id: number, status: Status) =>
    request<Ticket>(`/api/tickets/${id}`, { method: "PATCH", body: JSON.stringify({ status }) }),
};
