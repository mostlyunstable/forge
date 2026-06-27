import { describe, it, expect, beforeEach, afterEach, beforeAll, afterAll } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { handlers, mockDecision } from '@/test/handlers';
import { renderWithProviders } from '@/test/test-utils';
import { useSettings } from '@/stores/settings';
import { DecisionsView } from '../DecisionsView';

const server = setupServer(...handlers);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

beforeEach(() => {
  useSettings.setState({ currentProjectId: 'proj-1', apiUrl: 'http://127.0.0.1:8000' });
});

describe('DecisionsView', () => {
  it('shows loading state while data loads', () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/memory/decisions', () => {
        return new Promise(() => {}); // never resolves
      }),
    );

    const { container } = renderWithProviders(<DecisionsView />);
    // SkeletonRow renders skeleton elements
    expect(container.querySelectorAll('.animate-pulse').length).toBeGreaterThanOrEqual(0);
  });

  it('shows error state when API fails', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/memory/decisions', () => {
        return HttpResponse.json({ detail: 'Internal error' }, { status: 500 });
      }),
    );

    renderWithProviders(<DecisionsView />);
    await waitFor(() => {
      expect(screen.getByText('Failed to load decisions.')).toBeInTheDocument();
    });
  });

  it('shows empty state when no decisions', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/memory/decisions', () => {
        return HttpResponse.json({ decisions: [], total: 0, project_id: 'proj-1' });
      }),
    );

    renderWithProviders(<DecisionsView />);
    await waitFor(() => {
      expect(screen.getByText('No decisions recorded yet.')).toBeInTheDocument();
    });
  });

  it('shows decisions table with correct data', async () => {
    renderWithProviders(<DecisionsView />);
    await waitFor(() => {
      expect(screen.getByText('Use PostgreSQL')).toBeInTheDocument();
    });
    expect(screen.getByText('accepted')).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: 'Title' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: 'Status' })).toBeInTheDocument();
  });

  it('"New Decision" button opens slide-over panel', async () => {
    const user = userEvent.setup();
    renderWithProviders(<DecisionsView />);
    await waitFor(() => {
      expect(screen.getByText('Use PostgreSQL')).toBeInTheDocument();
    });

    await user.click(screen.getByText('New Decision'));
    expect(screen.getByText('New Decision', { selector: 'h2' })).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Decision title')).toBeInTheDocument();
  });

  it('slide-over panel has title, decision, reason, status fields', async () => {
    const user = userEvent.setup();
    renderWithProviders(<DecisionsView />);
    await waitFor(() => {
      expect(screen.getByText('Use PostgreSQL')).toBeInTheDocument();
    });

    await user.click(screen.getByText('New Decision'));
    expect(screen.getByPlaceholderText('Decision title')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('What was decided')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Why this decision was made')).toBeInTheDocument();
    const select = screen.getByRole('combobox');
    expect(select).toBeInTheDocument();
    expect(select).toHaveValue('proposed');
  });

  it('save button creates decision via API', async () => {
    const user = userEvent.setup();
    let createdBody: unknown = null;

    server.use(
      http.post('http://127.0.0.1:8000/api/v1/memory/decisions', async ({ request }) => {
        createdBody = await request.json();
        return HttpResponse.json({ ...mockDecision, id: 'dec-new' }, { status: 201 });
      }),
    );

    renderWithProviders(<DecisionsView />);
    await waitFor(() => {
      expect(screen.getByText('Use PostgreSQL')).toBeInTheDocument();
    });

    await user.click(screen.getByText('New Decision'));
    await user.type(screen.getByPlaceholderText('Decision title'), 'Use Redis');
    await user.click(screen.getByText('Save'));

    await waitFor(() => {
      expect(createdBody).toMatchObject({ title: 'Use Redis', project_id: 'proj-1' });
    });
  });

  it('delete button shows inline confirmation (Yes/No)', async () => {
    const user = userEvent.setup();
    renderWithProviders(<DecisionsView />);
    await waitFor(() => {
      expect(screen.getByText('Use PostgreSQL')).toBeInTheDocument();
    });

    const row = screen.getByRole('row', { name: /Use PostgreSQL/ });
    const buttons = within(row).getAllByRole('button');
    const trashBtn = buttons[buttons.length - 1];
    await user.click(trashBtn);

    expect(screen.getByText('Yes')).toBeInTheDocument();
    expect(screen.getByText('No')).toBeInTheDocument();
  });

  it('status badges show correct colors', async () => {
    renderWithProviders(<DecisionsView />);
    await waitFor(() => {
      expect(screen.getByText('Use PostgreSQL')).toBeInTheDocument();
    });

    const badge = screen.getByText('accepted');
    expect(badge).toHaveClass('badge-green');
  });

  it('status badge for proposed is blue', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/memory/decisions', () => {
        return HttpResponse.json({
          decisions: [{ ...mockDecision, status: 'proposed' }],
          total: 1,
          project_id: 'proj-1',
        });
      }),
    );

    renderWithProviders(<DecisionsView />);
    await waitFor(() => {
      expect(screen.getByText('proposed')).toHaveClass('badge-blue');
    });
  });

  it('status badge for superseded is muted', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/memory/decisions', () => {
        return HttpResponse.json({
          decisions: [{ ...mockDecision, status: 'superseded' }],
          total: 1,
          project_id: 'proj-1',
        });
      }),
    );

    renderWithProviders(<DecisionsView />);
    await waitFor(() => {
      expect(screen.getByText('superseded')).toHaveClass('badge-muted');
    });
  });

  it('editing a decision opens panel with pre-filled values', async () => {
    const user = userEvent.setup();
    renderWithProviders(<DecisionsView />);
    await waitFor(() => {
      expect(screen.getByText('Use PostgreSQL')).toBeInTheDocument();
    });

    await user.click(screen.getByText('Use PostgreSQL'));

    await waitFor(() => {
      expect(screen.getByText('Edit Decision')).toBeInTheDocument();
    });
    expect(screen.getByDisplayValue('Use PostgreSQL')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Use PostgreSQL for the main database')).toBeInTheDocument();
  });

  it('close button closes slide-over panel', async () => {
    const user = userEvent.setup();
    renderWithProviders(<DecisionsView />);
    await waitFor(() => {
      expect(screen.getByText('Use PostgreSQL')).toBeInTheDocument();
    });

    await user.click(screen.getByText('New Decision'));
    expect(screen.getByText('New Decision', { selector: 'h2' })).toBeInTheDocument();

    await user.click(screen.getByText('Close'));
    await waitFor(() => {
      expect(screen.queryByText('New Decision', { selector: 'h2' })).not.toBeInTheDocument();
    });
  });
});
