import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useContacts } from '@/hooks/useContacts';

describe('useContacts', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve(
          new Response(JSON.stringify({ status: 'success', data: { contacts: [] } }), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          })
        )
      )
    );
    localStorage.setItem('giftgenius_access_token', 'test-token');
  });

  afterEach(() => {
    vi.stubGlobal('fetch', originalFetch);
    vi.clearAllMocks();
  });

  it('fetchContacts loads and maps contacts', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          status: 'success',
          data: {
            contacts: [
              {
                id: 'c1',
                name: 'Alice',
                relationship_type: 'Friend',
                birthday: '1990-05-15',
                created_at: '2026-01-01T00:00:00',
                memory_count: 2,
              },
            ],
          },
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      )
    );

    const { result } = renderHook(() => useContacts());

    await act(async () => {
      await result.current.fetchContacts();
    });

    expect(result.current.contacts).toHaveLength(1);
    expect(result.current.contacts[0]).toMatchObject({
      id: 'c1',
      name: 'Alice',
      relationship: 'Friend',
    });
    expect(result.current.contacts[0].birthday).toBeInstanceOf(Date);
  });

  it('getContact returns contact with memories from cache', async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            status: 'success',
            data: {
              contacts: [
                {
                  id: 'c1',
                  name: 'Bob',
                  relationship_type: 'Colleague',
                  birthday: '1985-01-10',
                  created_at: '2026-01-01T00:00:00',
                },
              ],
            },
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            status: 'success',
            data: {
              memories: [
                { id: 'm1', content: 'Loves coffee', created_at: '2026-01-02T00:00:00' },
              ],
            },
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      );

    const { result } = renderHook(() => useContacts());

    await act(async () => {
      await result.current.fetchContacts();
    });

    let contact = result.current.getContact('c1');
    expect(contact?.memories).toEqual([]);

    await act(async () => {
      await result.current.fetchMemories('c1');
    });

    contact = result.current.getContact('c1');
    expect(contact?.memories).toHaveLength(1);
    expect(contact?.memories[0].content).toBe('Loves coffee');
  });

  it('addContact sends API payload and appends to state', async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ status: 'success', data: { contacts: [] } }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            status: 'success',
            data: {
              id: 'c-new',
              name: 'Eve',
              relationship_type: 'Family',
              birthday: '2000-06-20',
              created_at: '2026-01-01T12:00:00',
            },
          }),
          { status: 201, headers: { 'Content-Type': 'application/json' } }
        )
      );

    const { result } = renderHook(() => useContacts());

    await act(async () => {
      await result.current.fetchContacts();
    });

    await act(async () => {
      await result.current.addContact({
        name: 'Eve',
        relationship: 'Family',
        birthday: new Date('2000-06-20'),
      });
    });

    expect(result.current.contacts).toHaveLength(1);
    expect(result.current.contacts[0].name).toBe('Eve');
    expect(result.current.contacts[0].id).toBe('c-new');
  });

  it('updateContact sends API payload and updates state', async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            status: 'success',
            data: {
              contacts: [
                {
                  id: 'c-edit',
                  name: 'Old',
                  relationship_type: 'Friend',
                  birthday: '2000-01-01',
                  created_at: '2026-01-01T00:00:00',
                },
              ],
            },
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            status: 'success',
            data: {
              id: 'c-edit',
              name: 'New',
              relationship_type: 'Family',
              birthday: '2000-01-01',
              created_at: '2026-01-01T00:00:00',
            },
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      );

    const { result } = renderHook(() => useContacts());

    await act(async () => {
      await result.current.fetchContacts();
      await result.current.updateContact('c-edit', { name: 'New', relationship: 'Family' });
    });

    expect(result.current.contacts[0]).toMatchObject({ id: 'c-edit', name: 'New', relationship: 'Family' });
    expect(fetch).toHaveBeenLastCalledWith(
      expect.stringContaining('/contacts/c-edit'),
      expect.objectContaining({ method: 'PUT' })
    );
  });

  it('deleteContact removes contact and calls API', async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            status: 'success',
            data: {
              contacts: [
                {
                  id: 'c-del',
                  name: 'Del',
                  relationship_type: null,
                  birthday: null,
                  created_at: '2026-01-01T00:00:00',
                },
              ],
            },
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ status: 'success', data: null }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );

    const { result } = renderHook(() => useContacts());

    await act(async () => {
      await result.current.fetchContacts();
    });
    expect(result.current.contacts).toHaveLength(1);

    await act(async () => {
      await result.current.deleteContact('c-del');
    });
    expect(result.current.contacts).toHaveLength(0);
  });

  it('addMemory POSTs and appends to memories cache', async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            status: 'success',
            data: {
              contacts: [
                {
                  id: 'c2',
                  name: 'Charlie',
                  relationship_type: null,
                  birthday: null,
                  created_at: '2026-01-01T00:00:00',
                },
              ],
            },
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            status: 'success',
            data: {
              id: 'mem-new',
              content: 'New note',
              created_at: '2026-01-03T00:00:00',
            },
          }),
          { status: 201, headers: { 'Content-Type': 'application/json' } }
        )
      );

    const { result } = renderHook(() => useContacts());

    await act(async () => {
      await result.current.fetchContacts();
    });

    await act(async () => {
      await result.current.addMemory('c2', 'New note');
    });

    const contact = result.current.getContact('c2');
    expect(contact?.memories).toHaveLength(1);
    expect(contact?.memories[0].content).toBe('New note');
    expect(contact?.memories[0].id).toBe('mem-new');
  });

  it('deleteMemory removes a cached memory', async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            status: 'success',
            data: {
              contacts: [
                {
                  id: 'c2',
                  name: 'Charlie',
                  relationship_type: null,
                  birthday: null,
                  created_at: '2026-01-01T00:00:00',
                },
              ],
            },
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            status: 'success',
            data: {
              memories: [
                { id: 'm-delete', content: 'Remove me', created_at: '2026-01-02T00:00:00' },
              ],
            },
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ status: 'success', data: null }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      );

    const { result } = renderHook(() => useContacts());

    await act(async () => {
      await result.current.fetchContacts();
      await result.current.fetchMemories('c2');
      await result.current.deleteMemory('c2', 'm-delete');
    });

    expect(result.current.getContact('c2')?.memories).toEqual([]);
    expect(fetch).toHaveBeenLastCalledWith(
      expect.stringContaining('/contacts/c2/memories/m-delete'),
      expect.objectContaining({ method: 'DELETE' })
    );
  });

  it('fetchRecommendations stores gift ideas', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(
        JSON.stringify({ status: 'success', data: { recommendations: ['Coffee beans'] } }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      )
    );

    const { result } = renderHook(() => useContacts());

    await act(async () => {
      await result.current.fetchRecommendations('c1');
    });

    expect(result.current.recommendationsByContactId.c1).toEqual(['Coffee beans']);
  });
});
