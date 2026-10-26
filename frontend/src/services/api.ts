import type { Tokens } from "../types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";
const TOKEN_KEY = "sentinel-vault.tokens";
const TIMEOUT_MS = 15_000;

export class ApiError extends Error {
  constructor(public status: number, message: string, public body?: unknown) {
    super(message);
  }
}

export function getTokens(): Tokens | null {
  try {
    const value = sessionStorage.getItem(TOKEN_KEY);
    return value ? JSON.parse(value) as Tokens : null;
  } catch { return null; }
}

export function setTokens(tokens: Tokens | null) {
  if (tokens) sessionStorage.setItem(TOKEN_KEY, JSON.stringify(tokens));
  else sessionStorage.removeItem(TOKEN_KEY);
}

async function parseResponse(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") || "";
  return contentType.includes("application/json") ? response.json() : response.text();
}

function detail(body: unknown, fallback: string) {
  if (typeof body === "object" && body && "detail" in body && typeof body.detail === "string") return body.detail;
  if (typeof body === "string" && body) return body;
  return fallback;
}

async function refreshAccessToken(): Promise<string | null> {
  const tokens = getTokens();
  if (!tokens?.refresh) return null;
  const response = await fetch(`${BASE_URL}/auth/token/refresh/`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ refresh: tokens.refresh }),
  });
  if (!response.ok) { setTokens(null); window.dispatchEvent(new Event("sentinel-vault:auth-expired")); return null; }
  const body = await response.json() as Partial<Tokens>;
  if (!body.access) { setTokens(null); window.dispatchEvent(new Event("sentinel-vault:auth-expired")); return null; }
  setTokens({ access: body.access, refresh: body.refresh || tokens.refresh });
  return body.access;
}

export async function api<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), TIMEOUT_MS);
  const headers = new Headers(init.headers);
  const tokens = getTokens();
  if (tokens?.access) headers.set("Authorization", `Bearer ${tokens.access}`);
  try {
    const response = await fetch(`${BASE_URL}${path}`, { ...init, headers, signal: controller.signal });
    if (response.status === 401 && retry && !path.includes("/token/refresh/") && !path.includes("/auth/login/")) {
      const access = await refreshAccessToken();
      if (access) return api<T>(path, init, false);
    }
    const body = response.status === 204 ? null : await parseResponse(response);
    if (!response.ok) throw new ApiError(response.status, detail(body, `Request failed (${response.status})`), body);
    return body as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === "AbortError") throw new ApiError(0, "The server took too long to respond.");
    throw new ApiError(0, "Unable to reach the API. Check that the Django server is running.");
  } finally { window.clearTimeout(timeout); }
}

export async function downloadDocument(id: string, filename: string) {
  const tokens = getTokens();
  const response = await fetch(`${BASE_URL}/documents/${id}/download/`, { headers: tokens ? { Authorization: `Bearer ${tokens.access}` } : {} });
  if (!response.ok) throw new ApiError(response.status, detail(await parseResponse(response), "Download failed."));
  const url = URL.createObjectURL(await response.blob());
  const anchor = document.createElement("a");
  anchor.href = url; anchor.download = filename; anchor.click(); URL.revokeObjectURL(url);
}
