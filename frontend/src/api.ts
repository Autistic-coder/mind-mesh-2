const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");
let csrfToken = "";

function cookie(name: string) {
  return document.cookie.split("; ").find((item) => item.startsWith(`${name}=`))?.split("=").slice(1).join("=") || "";
}

export class ApiError extends Error {
  constructor(public status: number, message: string, public detail?: unknown) {
    super(message);
  }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const method = options.method || "GET";
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData) && options.body) headers.set("Content-Type", "application/json");
  if (!["GET", "HEAD", "OPTIONS"].includes(method) && !path.startsWith("/api/auth/login") && !path.startsWith("/api/auth/register")) {
    if (!csrfToken) {
      const response = await fetch(`${API_URL}/api/auth/csrf`, { credentials: "include" });
      if (!response.ok) throw new ApiError(response.status, "Secure session validation failed");
      csrfToken = (await response.json()).csrf_token;
    }
    headers.set("X-CSRF-Token", csrfToken || decodeURIComponent(cookie("mindmesh_csrf")));
  }
  const response = await fetch(`${API_URL}${path}`, { ...options, headers, credentials: "include" });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: "Request failed" }));
    const detail = body.detail;
    const message = typeof detail === "string" ? detail : detail?.message || "Request failed";
    throw new ApiError(response.status, message, detail);
  }
  if (response.status === 204) { if (path === "/api/auth/logout") csrfToken = ""; return undefined as T; }
  return response.json() as Promise<T>;
}

export async function download(path: string, filename: string) {
  const response = await fetch(`${API_URL}${path}`, { credentials: "include" });
  if (!response.ok) throw new ApiError(response.status, "Download failed");
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a"); anchor.href = url; anchor.download = filename; anchor.click();
  URL.revokeObjectURL(url);
}

