import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useAuth } from '@/hooks/useAuth';

describe('useAuth', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve(
          new Response(JSON.stringify({ status: 'success', data: null }), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          })
        )
      )
    );
    localStorage.clear();
  });

  afterEach(() => {
    vi.stubGlobal('fetch', originalFetch);
    vi.clearAllMocks();
  });

  it('logout clears user and token', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          status: 'success',
          data: {
            user: { id: '1', email: 'a@b.com', full_name: 'A', created_at: '2026-01-01T00:00:00' },
            access_token: 'token',
            token_type: 'bearer',
          },
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      )
    );

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      await result.current.login('a@b.com', 'password123');
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user?.email).toBe('a@b.com');
    expect(localStorage.getItem('giftgenius_access_token')).toBe('token');

    act(() => {
      result.current.logout();
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(localStorage.getItem('giftgenius_access_token')).toBeNull();
  });

  it('login stores token and sets user', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          status: 'success',
          data: {
            user: { id: 'u1', email: 'u@example.com', full_name: 'User One', created_at: '2026-01-01T00:00:00' },
            access_token: 'jwt',
            token_type: 'bearer',
          },
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      )
    );

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      await result.current.login('u@example.com', 'pass1234');
    });

    expect(result.current.user).toMatchObject({
      id: 'u1',
      email: 'u@example.com',
      name: 'User One',
    });
    expect(localStorage.getItem('giftgenius_access_token')).toBe('jwt');
  });

  it('signup with full_name stores token and sets user', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          status: 'success',
          data: {
            user: { id: 'u2', email: 'b@b.com', full_name: 'Jane', created_at: '2026-01-01T00:00:00' },
            access_token: 'jwt2',
            token_type: 'bearer',
          },
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      )
    );

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      await result.current.signup('b@b.com', 'password8', 'Jane');
    });

    expect(result.current.user?.name).toBe('Jane');
    expect(localStorage.getItem('giftgenius_access_token')).toBe('jwt2');
  });

  it('sets error and fieldErrors on login validation failure', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          status: 'error',
          data: null,
          message: 'Validation failed',
          error_code: 'VALIDATION_ERROR',
          details: { field_errors: { email: ['Invalid email'], password: ['Too short'] } },
        }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      )
    );

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      try {
        await result.current.login('bad', 'short');
      } catch {
        // expected
      }
    });

    expect(result.current.error).toBe('Validation failed');
    expect(result.current.fieldErrors).toEqual({
      email: ['Invalid email'],
      password: ['Too short'],
    });
  });
});
