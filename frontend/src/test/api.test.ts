import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  request,
  get,
  post,
  del,
  clearToken,
  setToken,
  getToken,
} from '@/lib/api';

describe('api client', () => {
  const originalFetch = globalThis.fetch;
  const originalLocation = window.location;

  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn((url: string, options?: RequestInit) => Promise.resolve(new Response()))
    );
    Object.defineProperty(window, 'location', {
      value: { href: '', assign: vi.fn(), replace: vi.fn() },
      writable: true,
    });
    clearToken();
  });

  afterEach(() => {
    vi.stubGlobal('fetch', originalFetch);
    Object.defineProperty(window, 'location', { value: originalLocation, writable: true });
    vi.clearAllMocks();
  });

  describe('envelope handling', () => {
    it('returns data when status is success', async () => {
      const data = { id: '1', name: 'Test' };
      vi.mocked(fetch).mockResolvedValueOnce(
        new Response(JSON.stringify({ status: 'success', data, message: 'OK' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );

      const result = await request<typeof data>('/test', { method: 'GET' }, false);
      expect(result).toEqual(data);
    });

    it('rejects with ApiError when status is error', async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            status: 'error',
            data: null,
            message: 'Validation failed',
            error_code: 'VALIDATION_ERROR',
            details: { field_errors: { email: ['Invalid'] } },
          }),
          { status: 400, headers: { 'Content-Type': 'application/json' } }
        )
      );

      await expect(request('/test', { method: 'GET' }, false)).rejects.toMatchObject({
        message: 'Validation failed',
        error_code: 'VALIDATION_ERROR',
        details: { field_errors: { email: ['Invalid'] } },
      });
    });
  });

  describe('token storage', () => {
    it('getToken returns null when no token', () => {
      expect(getToken()).toBeNull();
    });

    it('setToken and getToken round-trip', () => {
      setToken('abc');
      expect(getToken()).toBe('abc');
      clearToken();
      expect(getToken()).toBeNull();
    });
  });

  describe('401 auth error handling', () => {
    it('clears token and redirects to /login on 401 with TOKEN_EXPIRED for protected request', async () => {
      setToken('old-token');
      vi.mocked(fetch).mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            status: 'error',
            data: null,
            message: 'Expired',
            error_code: 'TOKEN_EXPIRED',
          }),
          { status: 401, headers: { 'Content-Type': 'application/json' } }
        )
      );

      await expect(request('/protected', { method: 'GET' }, true)).rejects.toMatchObject({
        message: 'Expired',
        error_code: 'TOKEN_EXPIRED',
      });
      expect(getToken()).toBeNull();
      expect(window.location.href).toBe('/login');
    });

    it('does not redirect for public request (requireAuth false) on 401', async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            status: 'error',
            data: null,
            message: 'Bad credentials',
            error_code: 'INVALID_CREDENTIALS',
          }),
          { status: 401, headers: { 'Content-Type': 'application/json' } }
        )
      );

      await expect(
        request('/auth/login', { method: 'POST', body: {} }, false)
      ).rejects.toMatchObject({ error_code: 'INVALID_CREDENTIALS' });
      expect(window.location.href).toBe('');
    });
  });

  describe('get, post, del', () => {
    it('get sends GET request', async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        new Response(JSON.stringify({ status: 'success', data: { x: 1 } }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );
      const result = await get<{ x: number }>('/path', true);
      expect(result).toEqual({ x: 1 });
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/path'),
        expect.objectContaining({ method: 'GET' })
      );
    });

    it('post sends JSON body', async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        new Response(JSON.stringify({ status: 'success', data: {} }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );
      await post('/path', { email: 'a@b.com' }, false);
      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ email: 'a@b.com' }),
          headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
        })
      );
    });

    it('del sends DELETE request with auth', async () => {
      setToken('t');
      vi.mocked(fetch).mockResolvedValueOnce(
        new Response(JSON.stringify({ status: 'success', data: null }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );
      await del('/contacts/1');
      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          method: 'DELETE',
          headers: expect.objectContaining({ Authorization: 'Bearer t' }),
        })
      );
    });
  });
});
