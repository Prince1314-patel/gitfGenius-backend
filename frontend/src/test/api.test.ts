import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  request,
  get,
  post,
  put,
  del,
} from '@/lib/api';

describe('api client', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn((url: string, options?: RequestInit) => Promise.resolve(new Response()))
    );
  });

  afterEach(() => {
    vi.stubGlobal('fetch', originalFetch);
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

      const result = await request<typeof data>('/test', { method: 'GET' });
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

      await expect(request('/test', { method: 'GET' })).rejects.toMatchObject({
        message: 'Validation failed',
        error_code: 'VALIDATION_ERROR',
        details: { field_errors: { email: ['Invalid'] } },
      });
    });
  });

  describe('error handling', () => {
    it('returns 401 envelope errors without redirecting', async () => {
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

      await expect(request('/anything', { method: 'POST', body: {} })).rejects.toMatchObject({
        error_code: 'INVALID_CREDENTIALS',
      });
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
      const result = await get<{ x: number }>('/path');
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
      await post('/path', { email: 'a@b.com' });
      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ email: 'a@b.com' }),
          headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
        })
      );
    });

    it('put sends JSON body', async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        new Response(JSON.stringify({ status: 'success', data: {} }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );
      await put('/path', { name: 'Updated' });
      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify({ name: 'Updated' }),
          headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
        })
      );
    });

    it('del sends DELETE request', async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        new Response(JSON.stringify({ status: 'success', data: null }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );
      await del('/contacts/1');
      const [, init] = vi.mocked(fetch).mock.calls[0];
      expect(init?.headers).not.toHaveProperty('Authorization');
      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });
  });
});
