/**
 * Central API client for GiftGenius backend.
 * Uses envelope responses: { status, data, message?, error_code?, details? }.
 */

import { API_PATHS } from './constants';

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

/**
 * Performs a request and parses the envelope. On success returns data; on error rejects with ApiError.
 *
 * @param path - Path relative to /api/v1.
 * @param options - Fetch options; body should be object for JSON (will be stringified).
 * @returns Promise resolving to envelope.data on success.
 */
export async function request<T>(
  path: string,
  options: RequestInit & { body?: object } = {}
): Promise<T> {
  const { body, ...rest } = options;
  const headers: HeadersInit = {
    ...(options.headers as Record<string, string>),
  };
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
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

  const errorCode = json.error_code;

  const err: ApiError = {
    message: json.message ?? 'Request failed',
    error_code: errorCode,
    details: json.details,
  };
  return Promise.reject(err);
}

/** GET request. */
export function get<T>(path: string): Promise<T> {
  return request<T>(path, { method: 'GET' });
}

/** POST request. */
export function post<T>(path: string, body: object): Promise<T> {
  return request<T>(path, { method: 'POST', body });
}

/** PUT request. */
export function put<T>(path: string, body: object): Promise<T> {
  return request<T>(path, { method: 'PUT', body });
}

/** DELETE request. */
export function del<T>(path: string): Promise<T> {
  return request<T>(path, { method: 'DELETE' });
}

// Re-export path helpers for callers
export { API_PATHS };
