import { describe, it, expect, vi } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@/test/test-utils';
import { DecisionCard } from '../DecisionCard';
import type { DecisionSummary } from '@/lib/api-types';

const mockDecision: DecisionSummary = {
  id: 'dec-1',
  title: 'Use PostgreSQL',
  decision: 'Use PostgreSQL as main database',
  status: 'accepted',
  created_at: '2024-01-15T10:00:00Z',
};

describe('DecisionCard', () => {
  it('renders decision title', () => {
    renderWithProviders(
      <DecisionCard decision={mockDecision} isSelected={false} onSelect={vi.fn()} />
    );
    expect(screen.getByText('Use PostgreSQL')).toBeInTheDocument();
  });

  it('renders formatted date', () => {
    renderWithProviders(
      <DecisionCard decision={mockDecision} isSelected={false} onSelect={vi.fn()} />
    );
    expect(screen.getByText(/Jan 15/)).toBeInTheDocument();
  });

  it('calls onSelect when clicked', async () => {
    const onSelect = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(
      <DecisionCard decision={mockDecision} isSelected={false} onSelect={onSelect} />
    );

    await user.click(screen.getByText('Use PostgreSQL'));
    expect(onSelect).toHaveBeenCalledWith('dec-1');
  });

  it('applies selected class when isSelected is true', () => {
    renderWithProviders(
      <DecisionCard decision={mockDecision} isSelected={true} onSelect={vi.fn()} />
    );
    const button = screen.getByRole('button');
    expect(button.className).toContain('card-selected');
  });

  it('handles decision with no created_at', () => {
    const decisionNoDate = { ...mockDecision, created_at: '' };
    renderWithProviders(
      <DecisionCard decision={decisionNoDate} isSelected={false} onSelect={vi.fn()} />
    );
    expect(screen.getByText('Use PostgreSQL')).toBeInTheDocument();
  });
});
