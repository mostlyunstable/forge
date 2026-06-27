import { describe, it, expect, beforeAll, afterEach, afterAll, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { handlers } from '@/test/handlers';
import { renderWithProviders } from '@/test/test-utils';
import { useSettings } from '@/stores/settings';
import { DashboardView } from '../DashboardView';

const server = setupServer(...handlers);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

beforeEach(() => {
  useSettings.setState({ currentProjectId: 'proj-1', apiUrl: 'http://127.0.0.1:8000' });
});

describe('DashboardView', () => {
  it('shows stat cards with correct data', async () => {
    renderWithProviders(<DashboardView />);

    await waitFor(() => {
      expect(screen.getByText('Total Memories')).toBeInTheDocument();
    });

    expect(screen.getByText('Open Bugs')).toBeInTheDocument();
    expect(screen.getByText('Decisions Made')).toBeInTheDocument();

    // decisions=1, openBugs=1 (unresolved bug), total=2
    const statCards = screen.getAllByText(/^\d+$/);
    const values = statCards.map((el) => el.textContent);
    expect(values).toContain('2');
    expect(values).toContain('1');
  });

  it('shows activity feed with decisions data', async () => {
    renderWithProviders(<DashboardView />);

    await waitFor(() => {
      expect(screen.getByText('Use PostgreSQL')).toBeInTheDocument();
    });

    expect(screen.getByText('Recent Activity')).toBeInTheDocument();
  });

  it('shows risk score from index status', async () => {
    renderWithProviders(<DashboardView />);

    await waitFor(() => {
      expect(screen.getByText('10')).toBeInTheDocument();
    });

    expect(screen.getByText('Files Indexed')).toBeInTheDocument();
    expect(screen.getByText('Idle')).toBeInTheDocument();
  });

  it('shows loading state while data loads', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/projects', () => {
        return new Promise(() => {}); // never resolves
      })
    );

    renderWithProviders(<DashboardView />);

    await waitFor(() => {
      expect(screen.queryByText('Total Memories')).not.toBeInTheDocument();
    });
  });

  it('shows error state when API fails', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/projects', () => {
        return HttpResponse.json({ detail: 'Internal server error' }, { status: 500 });
      })
    );

    renderWithProviders(<DashboardView />);

    await waitFor(() => {
      expect(screen.getByText(/Failed to connect to Forge server/i)).toBeInTheDocument();
    });
  });

  it('shows empty state when no decisions exist', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/memory/decisions', () => {
        return HttpResponse.json({ decisions: [], total: 0, project_id: 'proj-1' });
      })
    );

    renderWithProviders(<DashboardView />);

    await waitFor(() => {
      expect(screen.getByText(/No activity yet/)).toBeInTheDocument();
    });
  });
});
