import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { handlers } from '@/test/handlers';
import { renderWithProviders } from '@/test/test-utils';
import { useSettings } from '@/stores/settings';
import { SettingsDialog } from '../SettingsDialog';

const server = setupServer(...handlers);

beforeEach(() => {
  server.listen();
  useSettings.setState({
    apiUrl: 'http://127.0.0.1:8000',
    authToken: 'test-key',
    currentProjectId: 'proj-1',
    connectionStatus: 'connected',
  });
});

afterEach(() => {
  server.resetHandlers();
  server.close();
});

describe('SettingsDialog', () => {
  it('does not render when open=false', () => {
    renderWithProviders(<SettingsDialog open={false} onClose={() => {}} />);
    expect(screen.queryByText('Settings')).not.toBeInTheDocument();
  });

  it('renders when open=true', () => {
    renderWithProviders(<SettingsDialog open={true} onClose={() => {}} />);
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('shows server URL input with current value', () => {
    renderWithProviders(<SettingsDialog open={true} onClose={() => {}} />);
    const input = screen.getByPlaceholderText('http://localhost:8000');
    expect(input).toHaveValue('http://127.0.0.1:8000');
  });

  it('shows API key input', () => {
    renderWithProviders(<SettingsDialog open={true} onClose={() => {}} />);
    const inputs = screen.getAllByPlaceholderText('Optional');
    expect(inputs.length).toBeGreaterThanOrEqual(1);
  });

  it('shows Save and Cancel buttons', () => {
    renderWithProviders(<SettingsDialog open={true} onClose={() => {}} />);
    expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
  });

  it('Cancel calls onClose', async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(<SettingsDialog open={true} onClose={onClose} />);

    await user.click(screen.getByRole('button', { name: /cancel/i }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('Save calls setApiUrl and setAuthToken', async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(<SettingsDialog open={true} onClose={onClose} />);

    await user.click(screen.getByRole('button', { name: /save/i }));

    await waitFor(() => {
      const state = useSettings.getState();
      expect(state.apiUrl).toBe('http://127.0.0.1:8000');
      expect(state.authToken).toBe('test-key');
    });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('Test Connection button makes API call', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SettingsDialog open={true} onClose={() => {}} />);

    await user.click(screen.getByRole('button', { name: /test connection/i }));

    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
    });
  });

  it('shows error after failed test connection', async () => {
    server.use(
      http.post('http://127.0.0.1:8000/api/v1/chat', () => {
        return HttpResponse.json({ detail: 'Internal error' }, { status: 500 });
      })
    );

    const user = userEvent.setup();
    renderWithProviders(<SettingsDialog open={true} onClose={() => {}} />);

    await user.click(screen.getByRole('button', { name: /test connection/i }));

    await waitFor(() => {
      expect(screen.getByText('Failed')).toBeInTheDocument();
    });
  });
});
