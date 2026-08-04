import { describe, it, expect, vi, beforeAll, afterEach, afterAll } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { renderWithProviders } from '@/test/test-utils';
import { DecisionDetail } from '../DecisionDetail';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

const server = setupServer(
  http.get('http://127.0.0.1:8000/api/v1/memory/decisions/:id', () => {
    return HttpResponse.json({
      id: 'dec-1',
      project_id: 'proj-1',
      title: 'Use PostgreSQL',
      decision: 'Use PostgreSQL as the main database',
      reason: 'It is mature and well-supported',
      alternatives: ['MySQL', 'SQLite'],
      status: 'accepted',
      created_at: '2024-01-15T10:00:00Z',
    });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('DecisionDetail', () => {
  it('renders decision detail with data', async () => {
    renderWithProviders(<DecisionDetail id="dec-1" onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('Use PostgreSQL')).toBeInTheDocument();
    });

    expect(screen.getByText('Use PostgreSQL as the main database')).toBeInTheDocument();
    expect(screen.getByText('It is mature and well-supported')).toBeInTheDocument();
    expect(screen.getByText('accepted')).toBeInTheDocument();
    expect(screen.getByText('MySQL')).toBeInTheDocument();
    expect(screen.getByText('SQLite')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/memory/decisions/:id', () => {
        return new Promise(() => {});
      })
    );

    renderWithProviders(<DecisionDetail id="dec-1" onClose={vi.fn()} />);
    expect(screen.getByText('Decision')).toBeInTheDocument();
  });

  it('shows close button and calls onClose', async () => {
    const onClose = vi.fn();
    renderWithProviders(<DecisionDetail id="dec-1" onClose={onClose} />);

    await waitFor(() => {
      expect(screen.getByText('Use PostgreSQL')).toBeInTheDocument();
    });

    const closeButton = screen.getByRole('button');
    await closeButton.click();
    expect(onClose).toHaveBeenCalled();
  });

  it('shows not found when decision does not exist', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/memory/decisions/:id', () => {
        return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
      })
    );

    renderWithProviders(<DecisionDetail id="nonexistent" onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('Not found')).toBeInTheDocument();
    });
  });
});
