import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from '@/App';

describe('App', () => {
  beforeEach(() => {
    localStorage.clear();
    window.history.pushState({}, '', '/dashboard');
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
  });

  it('shows the app without a login token during development', async () => {
    render(<App />);

    await waitFor(() => expect(screen.getByText('Hi, there')).toBeInTheDocument());
    expect(screen.queryByText('Welcome Back')).not.toBeInTheDocument();
  });
});
