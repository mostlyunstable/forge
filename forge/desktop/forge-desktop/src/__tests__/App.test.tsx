import { describe, it, expect, vi, beforeAll, afterEach, afterAll, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { useSettings } from '@/stores/settings';
import { useNavigation } from '@/stores/navigation';
import App from '../App';

const server = setupServer(
  http.get('http://127.0.0.1:8000/health', () => HttpResponse.json({ status: 'ok' })),
  http.get('http://127.0.0.1:8000/api/v1/projects', () => HttpResponse.json({ projects: [], total: 0 })),
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

beforeEach(() => {
  const reloadSpy = vi.fn();
  Object.defineProperty(window, 'location', {
    value: { ...window.location, reload: reloadSpy },
    writable: true,
    configurable: true,
  });
});

describe('App', () => {
  it('shows LoginView when no auth token', () => {
    useSettings.setState({ authToken: null });
    render(<App />);
    expect(screen.getByText(/connect/i)).toBeInTheDocument();
  });

  it('shows AppLayout with ViewRouter when auth token present', async () => {
    useSettings.setState({
      authToken: 'test-token',
      currentProjectId: 'proj-1',
      apiUrl: 'http://127.0.0.1:8000',
    });
    render(<App />);
    await waitFor(() => {
      expect(screen.getAllByText('Dashboard').length).toBeGreaterThan(0);
    });
  });

  it('ViewRouter renders correct view based on activeView', async () => {
    useSettings.setState({
      authToken: 'test-token',
      currentProjectId: 'proj-1',
      apiUrl: 'http://127.0.0.1:8000',
    });
    useNavigation.setState({ activeView: 'code' });
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText('Files')).toBeInTheDocument();
    });
  });
});
