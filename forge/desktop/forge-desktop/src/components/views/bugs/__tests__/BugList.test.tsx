import { describe, it, expect, vi } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@/test/test-utils';
import { BugList } from '../BugList';
import type { BugSummary } from '@/lib/api-types';

const mockBugs: BugSummary[] = [
  { id: 'bug-1', title: 'Null pointer in auth', severity: 'high', resolved: false, created_at: '2024-01-15' },
  { id: 'bug-2', title: 'Missing validation', severity: 'medium', resolved: true, created_at: '2024-01-16' },
  { id: 'bug-3', title: 'Typo in config', severity: 'low', resolved: false, created_at: '2024-01-17' },
];

describe('BugList', () => {
  it('renders bug titles', () => {
    renderWithProviders(
      <BugList bugs={mockBugs} onSelect={vi.fn()} selectedBug={null} />
    );
    expect(screen.getByText('Null pointer in auth')).toBeInTheDocument();
    expect(screen.getByText('Missing validation')).toBeInTheDocument();
    expect(screen.getByText('Typo in config')).toBeInTheDocument();
  });

  it('renders severity badges', () => {
    renderWithProviders(
      <BugList bugs={mockBugs} onSelect={vi.fn()} selectedBug={null} />
    );
    expect(screen.getByText('High')).toBeInTheDocument();
    expect(screen.getByText('Medium')).toBeInTheDocument();
    expect(screen.getByText('Low')).toBeInTheDocument();
  });

  it('shows resolved status', () => {
    renderWithProviders(
      <BugList bugs={mockBugs} onSelect={vi.fn()} selectedBug={null} />
    );
    expect(screen.getByText('Resolved')).toBeInTheDocument();
    expect(screen.getAllByText('Open').length).toBeGreaterThanOrEqual(1);
  });

  it('shows empty state when no bugs', () => {
    renderWithProviders(
      <BugList bugs={[]} onSelect={vi.fn()} selectedBug={null} />
    );
    expect(screen.getByText('No bugs recorded')).toBeInTheDocument();
  });

  it('calls onSelect when bug is clicked', async () => {
    const onSelect = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(
      <BugList bugs={mockBugs} onSelect={onSelect} selectedBug={null} />
    );

    await user.click(screen.getByText('Null pointer in auth'));
    expect(onSelect).toHaveBeenCalledWith('bug-1');
  });
});
