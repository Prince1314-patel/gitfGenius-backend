import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { DatabasePage } from '@/pages/DatabasePage';

describe('DatabasePage', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve(
          new Response(
            JSON.stringify({
              status: 'success',
              data: {
                database_url: 'postgres',
                counts: { users: 1, contacts: 2, memories: 3 },
                ai: { provider: 'openrouter', model: 'openrouter/free', configured: true },
                users: [],
                contacts: [{ id: 'c1', name: 'Asha', relationship_type: 'Friend', birthday: null, created_at: '2026-01-01T00:00:00', memory_count: 1 }],
                memories: [{ id: 'm1', content: 'Likes books', created_at: '2026-01-01T00:00:00' }],
              },
            }),
            { status: 200, headers: { 'Content-Type': 'application/json' } }
          )
        )
      )
    );
  });

  it('shows database counts and recent rows', async () => {
    render(<DatabasePage />);

    await waitFor(() => expect(screen.getByText('postgres database')).toBeInTheDocument());
    expect(screen.getByText('Asha')).toBeInTheDocument();
    expect(screen.getByText('Likes books')).toBeInTheDocument();
    expect(screen.getByText('openrouter/free')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });
});
