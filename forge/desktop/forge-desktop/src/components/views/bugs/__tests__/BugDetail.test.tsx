import { describe, it, expect, vi, beforeAll, afterEach, afterAll } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { renderWithProviders } from '@/test/test-utils';
import { BugDetail } from '../BugDetail';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

const server = setupServer(
  http.get('http://127.0.0.1:8000/api/v1/memory/bugs/:id', () => {
    return HttpResponse.json({
      id: 'bug-1',
      project_id: 'proj-1',
      title: 'Null pointer in auth',
      problem: 'Auth middleware crashes on missing header',
      root_cause: 'No null check on authorization header',
      solution: 'Add null check before accessing header value',
      affected_files: ['src/auth/middleware.ts', 'src/auth/utils.ts'],
      severity: 'high',
      resolved: false,
      created_at: '2024-01-15T10:00:00Z',
    });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('BugDetail', () => {
  it('renders bug detail with data', async () => {
    renderWithProviders(<BugDetail id="bug-1" onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('Null pointer in auth')).toBeInTheDocument();
    });

    expect(screen.getByText('Auth middleware crashes on missing header')).toBeInTheDocument();
    expect(screen.getByText('No null check on authorization header')).toBeInTheDocument();
    expect(screen.getByText('Add null check before accessing header value')).toBeInTheDocument();
  });

  it('shows severity badge', async () => {
    renderWithProviders(<BugDetail id="bug-1" onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('high')).toBeInTheDocument();
    });

    expect(screen.getByText('Open')).toBeInTheDocument();
  });

  it('shows resolved badge for resolved bug', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/memory/bugs/:id', () => {
        return HttpResponse.json({
          id: 'bug-2',
          project_id: 'proj-1',
          title: 'Fixed bug',
          problem: 'Problem',
          root_cause: '',
          solution: '',
          affected_files: [],
          severity: 'low',
          resolved: true,
          created_at: '2024-01-15T10:00:00Z',
        });
      })
    );

    renderWithProviders(<BugDetail id="bug-2" onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('Resolved')).toBeInTheDocument();
    });
  });

  it('shows affected files', async () => {
    renderWithProviders(<BugDetail id="bug-1" onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('src/auth/middleware.ts')).toBeInTheDocument();
    });

    expect(screen.getByText('src/auth/utils.ts')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/memory/bugs/:id', () => {
        return new Promise(() => {});
      })
    );

    renderWithProviders(<BugDetail id="bug-1" onClose={vi.fn()} />);
    expect(screen.getByText('Bug')).toBeInTheDocument();
  });

  it('shows close button and calls onClose', async () => {
    const onClose = vi.fn();
    renderWithProviders(<BugDetail id="bug-1" onClose={onClose} />);

    await waitFor(() => {
      expect(screen.getByText('Null pointer in auth')).toBeInTheDocument();
    });

    const closeButton = screen.getByRole('button');
    await closeButton.click();
    expect(onClose).toHaveBeenCalled();
  });

  it('shows not found when bug does not exist', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/memory/bugs/:id', () => {
        return new HttpResponse.json({ detail: 'Not found' }, { status: 404 });
      })
    );

    renderWithProviders(<BugDetail id="nonexistent" onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('Not found')).toBeInTheDocument();
    });
  });
});
