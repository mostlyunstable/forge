import { describe, it, expect, beforeEach, beforeAll, afterEach, afterAll } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { handlers } from '@/test/handlers';
import { renderWithProviders } from '@/test/test-utils';
import { useSettings } from '@/stores/settings';
import { LoginView } from '../LoginView';

const server = setupServer(...handlers);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

beforeEach(() => {
  useSettings.setState({
    apiUrl: 'http://127.0.0.1:8000',
    authToken: null,
    currentProjectId: null,
    connectionStatus: 'disconnected',
  });
});

describe('LoginView', () => {
  it('shows server URL input', () => {
    renderWithProviders(<LoginView />);
    const input = screen.getByPlaceholderText('http://localhost:8000');
    expect(input).toBeInTheDocument();
    expect(input).toHaveValue('http://127.0.0.1:8000');
  });

  it('shows API key input', () => {
    renderWithProviders(<LoginView />);
    const input = screen.getByPlaceholderText('Optional');
    expect(input).toBeInTheDocument();
    expect(input).toHaveValue('');
  });

  it('shows connect button', () => {
    renderWithProviders(<LoginView />);
    expect(screen.getByRole('button', { name: /connect/i })).toBeInTheDocument();
  });

  it('successful connection stores token and calls setAuthToken', async () => {
    const user = userEvent.setup();
    renderWithProviders(<LoginView />);

    await user.click(screen.getByRole('button', { name: /connect/i }));

    await waitFor(() => {
      const state = useSettings.getState();
      expect(state.authToken).toBe('dev-token');
      expect(state.apiUrl).toBe('http://127.0.0.1:8000');
    });
  });

  it('shows error on failed connection', async () => {
    server.use(
      http.post('http://127.0.0.1:8000/api/v1/chat', () => {
        return HttpResponse.error();
      })
    );

    renderWithProviders(<LoginView />);
    await userEvent.click(screen.getByRole('button', { name: /connect/i }));

    await waitFor(() => {
      expect(screen.getByText(/failed to fetch/i)).toBeInTheDocument();
    });
  });

  it('shows loading state during connection test', async () => {
    server.use(
      http.post('http://127.0.0.1:8000/api/v1/chat', async () => {
        await new Promise((r) => setTimeout(r, 500));
        return HttpResponse.json({ response: 'ok', sources: [], project_id: 'proj-1' });
      })
    );

    const user = userEvent.setup();
    renderWithProviders(<LoginView />);

    await user.click(screen.getByRole('button', { name: /connect/i }));

    await waitFor(() => {
      expect(screen.getByText('Connecting...')).toBeInTheDocument();
    });
  });
});
