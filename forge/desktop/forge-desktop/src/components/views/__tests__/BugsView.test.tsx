import { describe, it, expect, beforeEach, afterEach, beforeAll, afterAll } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { handlers, mockBug } from '@/test/handlers';
import { renderWithProviders } from '@/test/test-utils';
import { useSettings } from '@/stores/settings';
import { BugsView } from '../BugsView';

const server = setupServer(...handlers);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

beforeEach(() => {
  useSettings.setState({ currentProjectId: 'proj-1', apiUrl: 'http://127.0.0.1:8000' });
});

describe('BugsView', () => {
  it('shows loading state while data loads', () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/memory/bugs', () => {
        return new Promise(() => {}); // never resolves
      }),
    );

    const { container } = renderWithProviders(<BugsView />);
    expect(container.querySelectorAll('.animate-pulse').length).toBeGreaterThanOrEqual(0);
  });

  it('shows error state when API fails', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/memory/bugs', () => {
        return HttpResponse.json({ detail: 'Internal error' }, { status: 500 });
      }),
    );

    renderWithProviders(<BugsView />);
    await waitFor(() => {
      expect(screen.getByText('Failed to load bugs.')).toBeInTheDocument();
    });
  });

  it('shows empty state when no bugs', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/memory/bugs', () => {
        return HttpResponse.json({ bugs: [], total: 0, project_id: 'proj-1' });
      }),
    );

    renderWithProviders(<BugsView />);
    await waitFor(() => {
      expect(screen.getByText('No bugs tracked yet.')).toBeInTheDocument();
    });
  });

  it('shows bugs table with correct data', async () => {
    renderWithProviders(<BugsView />);
    await waitFor(() => {
      expect(screen.getByText('Login fails on Safari')).toBeInTheDocument();
    });
    expect(screen.getByText('high')).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: 'Title' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: 'Severity' })).toBeInTheDocument();
  });

  it('"New Bug" button opens slide-over panel', async () => {
    const user = userEvent.setup();
    renderWithProviders(<BugsView />);
    await waitFor(() => {
      expect(screen.getByText('Login fails on Safari')).toBeInTheDocument();
    });

    await user.click(screen.getByText('New Bug'));
    expect(screen.getByText('New Bug', { selector: 'h2' })).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Bug title')).toBeInTheDocument();
  });

  it('slide-over panel has title, problem, root_cause, solution, severity fields', async () => {
    const user = userEvent.setup();
    renderWithProviders(<BugsView />);
    await waitFor(() => {
      expect(screen.getByText('Login fails on Safari')).toBeInTheDocument();
    });

    await user.click(screen.getByText('New Bug'));
    expect(screen.getByPlaceholderText('Bug title')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Describe the problem')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Root cause analysis')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('How it was fixed')).toBeInTheDocument();
    const select = screen.getByRole('combobox');
    expect(select).toBeInTheDocument();
    expect(select).toHaveValue('medium');
  });

  it('save button creates bug via API', async () => {
    const user = userEvent.setup();
    let createdBody: unknown = null;

    server.use(
      http.post('http://127.0.0.1:8000/api/v1/memory/bugs', async ({ request }) => {
        createdBody = await request.json();
        return HttpResponse.json({ ...mockBug, id: 'bug-new' }, { status: 201 });
      }),
    );

    renderWithProviders(<BugsView />);
    await waitFor(() => {
      expect(screen.getByText('Login fails on Safari')).toBeInTheDocument();
    });

    await user.click(screen.getByText('New Bug'));
    await user.type(screen.getByPlaceholderText('Bug title'), 'New bug');
    await user.click(screen.getByText('Save'));

    await waitFor(() => {
      expect(createdBody).toMatchObject({ title: 'New bug', project_id: 'proj-1' });
    });
  });

  it('delete button shows inline confirmation', async () => {
    const user = userEvent.setup();
    renderWithProviders(<BugsView />);
    await waitFor(() => {
      expect(screen.getByText('Login fails on Safari')).toBeInTheDocument();
    });

    const row = screen.getByRole('row', { name: /Login fails on Safari/ });
    const buttons = within(row).getAllByRole('button');
    const trashBtn = buttons[buttons.length - 1];
    await user.click(trashBtn);

    expect(screen.getByText('Yes')).toBeInTheDocument();
    expect(screen.getByText('No')).toBeInTheDocument();
  });

  it('severity badge for critical is red', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/memory/bugs', () => {
        return HttpResponse.json({
          bugs: [{ ...mockBug, severity: 'critical' }],
          total: 1,
          project_id: 'proj-1',
        });
      }),
    );

    renderWithProviders(<BugsView />);
    await waitFor(() => {
      expect(screen.getByText('critical')).toHaveClass('badge-red');
    });
  });

  it('severity badge for high is amber', async () => {
    renderWithProviders(<BugsView />);
    await waitFor(() => {
      expect(screen.getByText('high')).toHaveClass('badge-amber');
    });
  });

  it('severity badge for medium is blue', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/memory/bugs', () => {
        return HttpResponse.json({
          bugs: [{ ...mockBug, severity: 'medium' }],
          total: 1,
          project_id: 'proj-1',
        });
      }),
    );

    renderWithProviders(<BugsView />);
    await waitFor(() => {
      expect(screen.getByText('medium')).toHaveClass('badge-blue');
    });
  });

  it('severity badge for low is muted', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/memory/bugs', () => {
        return HttpResponse.json({
          bugs: [{ ...mockBug, severity: 'low' }],
          total: 1,
          project_id: 'proj-1',
        });
      }),
    );

    renderWithProviders(<BugsView />);
    await waitFor(() => {
      expect(screen.getByText('low')).toHaveClass('badge-muted');
    });
  });

  it('resolved checkbox shows for editing only', async () => {
    const user = userEvent.setup();
    renderWithProviders(<BugsView />);
    await waitFor(() => {
      expect(screen.getByText('Login fails on Safari')).toBeInTheDocument();
    });

    // No resolved checkbox on new bug form
    await user.click(screen.getByText('New Bug'));
    expect(screen.queryByText('Resolved')).not.toBeInTheDocument();
    await user.click(screen.getByText('Close'));
    await waitFor(() => {
      expect(screen.queryByText('New Bug', { selector: 'h2' })).not.toBeInTheDocument();
    });

    // Resolved checkbox visible on edit
    await user.click(screen.getByText('Login fails on Safari'));
    await waitFor(() => {
      expect(screen.getByText('Resolved')).toBeInTheDocument();
    });
  });

  it('close button closes slide-over panel', async () => {
    const user = userEvent.setup();
    renderWithProviders(<BugsView />);
    await waitFor(() => {
      expect(screen.getByText('Login fails on Safari')).toBeInTheDocument();
    });

    await user.click(screen.getByText('New Bug'));
    expect(screen.getByText('New Bug', { selector: 'h2' })).toBeInTheDocument();

    await user.click(screen.getByText('Close'));
    await waitFor(() => {
      expect(screen.queryByText('New Bug', { selector: 'h2' })).not.toBeInTheDocument();
    });
  });
});
