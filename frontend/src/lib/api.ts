/**
 * Central API client for GiftGenius backend.
 * Uses envelope responses: { status, data, message?, error_code?, details? }.
 * Handles 401 token errors for protected routes only.
 */

import { API_PATHS, AUTH_ERROR_CODES, TOKEN_STORAGE_KEY } from './constants';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_V1 = `${API_BASE}/api/v1`;

/** Backend response envelope (success or error). */
export interface ApiEnvelope<T = unknown> {
  status: 'success' | 'error';
  data: T | null;
  message?: string;
  error_code?: string;
  details?: { field_errors?: Record<string, string[]> };
}

/** Rejection payload when status === 'error'. */
export interface ApiError {
  message: string;
  error_code?: string;
  details?: ApiEnvelope['details'];
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

function redirectToLogin(): void {
  clearToken();
  window.location.href = '/login';
}

/**
 * Performs a request and parses the envelope. On success returns data; on error rejects with ApiError.
 * For protected routes (requireAuth: true), 401 with token-related error codes clears token and redirects to /login.
 *
 * @param path - Path relative to /api/v1 (e.g. '/auth/login').
 * @param options - Fetch options; body should be object for JSON (will be stringified).
 * @param requireAuth - If true, add Bearer token and handle 401 with auth error codes by redirecting to login.
 * @returns Promise resolving to envelope.data on success.
 */
export async function request<T>(
  path: string,
  options: RequestInit & { body?: object } = {},
  requireAuth = false
): Promise<T> {
  const { body, ...rest } = options;
  const headers: HeadersInit = {
    ...(options.headers as Record<string, string>),
  };
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
  }
  if (requireAuth) {
    const token = getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  const url = `${API_V1}${path}`;
  const res = await fetch(url, {
    ...rest,
    headers,
    body: body !== undefined ? JSON.stringify(body) : options.body,
  });

  let json: ApiEnvelope<T>;
  try {
    json = (await res.json()) as ApiEnvelope<T>;
  } catch {
    throw { message: 'Invalid response from server', error_code: undefined, details: undefined } as ApiError;
  }

  if (json.status === 'success') {
    return json.data as T;
  }

  const status = res.status;
  const errorCode = json.error_code;

  if (status === 401 && requireAuth && errorCode && AUTH_ERROR_CODES.includes(errorCode as (typeof AUTH_ERROR_CODES)[number])) {
    redirectToLogin();
  }

  const err: ApiError = {
    message: json.message ?? 'Request failed',
    error_code: errorCode,
    details: json.details,
  };
  return Promise.reject(err);
}

/** GET request (protected). */
export function get<T>(path: string, requireAuth = true): Promise<T> {
  return request<T>(path, { method: 'GET' }, requireAuth);
}

/** POST request. */
export function post<T>(path: string, body: object, requireAuth = false): Promise<T> {
  return request<T>(path, { method: 'POST', body }, requireAuth);
}

/** DELETE request (protected). */
export function del<T>(path: string): Promise<T> {
  return request<T>(path, { method: 'DELETE' }, true);
}

// Re-export path helpers for callers
export { API_PATHS };
