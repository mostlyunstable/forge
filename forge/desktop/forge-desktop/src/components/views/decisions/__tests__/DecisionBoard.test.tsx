import { describe, it, expect, vi } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@/test/test-utils';
import { DecisionBoard } from '../DecisionBoard';
import type { DecisionSummary } from '@/lib/api-types';

const mockDecisions: DecisionSummary[] = [
  { id: '1', title: 'Use PostgreSQL', decision: 'Use PostgreSQL as main DB', status: 'accepted', created_at: '2024-01-15' },
  { id: '2', title: 'Use FastAPI', decision: 'Use FastAPI for API layer', status: 'proposed', created_at: '2024-01-16' },
  { id: '3', title: 'Use REST', decision: 'Use REST over GraphQL', status: 'superseded', created_at: '2024-01-17' },
];

describe('DecisionBoard', () => {
  it('renders filter buttons', () => {
    renderWithProviders(
      <DecisionBoard decisions={mockDecisions} onSelect={vi.fn()} selectedDecision={null} />
    );
    expect(screen.getByRole('button', { name: 'All' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Proposed' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Accepted' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Superseded' })).toBeInTheDocument();
  });

  it('renders column headers', () => {
    renderWithProviders(
      <DecisionBoard decisions={mockDecisions} onSelect={vi.fn()} selectedDecision={null} />
    );
    expect(screen.getAllByText('Proposed').length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByText('Accepted').length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByText('Superseded').length).toBeGreaterThanOrEqual(2);
  });

  it('renders decision cards', () => {
    renderWithProviders(
      <DecisionBoard decisions={mockDecisions} onSelect={vi.fn()} selectedDecision={null} />
    );
    expect(screen.getByText('Use PostgreSQL')).toBeInTheDocument();
    expect(screen.getByText('Use FastAPI')).toBeInTheDocument();
    expect(screen.getByText('Use REST')).toBeInTheDocument();
  });

  it('shows empty state for column with no decisions', () => {
    renderWithProviders(
      <DecisionBoard decisions={[]} onSelect={vi.fn()} selectedDecision={null} />
    );
    expect(screen.getAllByText('No items').length).toBe(3);
  });

  it('filters decisions by status', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <DecisionBoard decisions={mockDecisions} onSelect={vi.fn()} selectedDecision={null} />
    );

    await user.click(screen.getByRole('button', { name: 'Accepted' }));

    expect(screen.getByText('Use PostgreSQL')).toBeInTheDocument();
    expect(screen.queryByText('Use FastAPI')).not.toBeInTheDocument();
    expect(screen.queryByText('Use REST')).not.toBeInTheDocument();
  });

  it('shows all when All filter is selected', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <DecisionBoard decisions={mockDecisions} onSelect={vi.fn()} selectedDecision={null} />
    );

    await user.click(screen.getByRole('button', { name: 'Accepted' }));
    await user.click(screen.getByRole('button', { name: 'All' }));

    expect(screen.getByText('Use PostgreSQL')).toBeInTheDocument();
    expect(screen.getByText('Use FastAPI')).toBeInTheDocument();
    expect(screen.getByText('Use REST')).toBeInTheDocument();
  });
});
