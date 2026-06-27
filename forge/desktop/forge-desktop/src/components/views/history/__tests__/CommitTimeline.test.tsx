import { describe, it, expect, vi } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@/test/test-utils';
import { CommitTimeline } from '../CommitTimeline';

describe('CommitTimeline', () => {
  it('renders commit hashes', () => {
    renderWithProviders(<CommitTimeline onSelect={vi.fn()} selectedCommit={null} />);
    expect(screen.getByText('abc1234')).toBeInTheDocument();
    expect(screen.getByText('def5678')).toBeInTheDocument();
    expect(screen.getByText('ghi9012')).toBeInTheDocument();
    expect(screen.getByText('jkl3456')).toBeInTheDocument();
  });

  it('renders commit messages', () => {
    renderWithProviders(<CommitTimeline onSelect={vi.fn()} selectedCommit={null} />);
    expect(screen.getByText('feat: add chat endpoint')).toBeInTheDocument();
    expect(screen.getByText('fix: null pointer in auth')).toBeInTheDocument();
    expect(screen.getByText('refactor: extract context retriever')).toBeInTheDocument();
    expect(screen.getByText('feat: add indexing pipeline')).toBeInTheDocument();
  });

  it('renders commit metadata', () => {
    renderWithProviders(<CommitTimeline onSelect={vi.fn()} selectedCommit={null} />);
    expect(screen.getAllByText('@dev').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('2h ago')).toBeInTheDocument();
    expect(screen.getByText('3 files')).toBeInTheDocument();
  });

  it('calls onSelect when commit is clicked', async () => {
    const onSelect = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(<CommitTimeline onSelect={onSelect} selectedCommit={null} />);

    await user.click(screen.getByText('feat: add chat endpoint'));
    expect(onSelect).toHaveBeenCalledWith('abc1234');
  });

  it('highlights selected commit', () => {
    renderWithProviders(<CommitTimeline onSelect={vi.fn()} selectedCommit="def5678" />);
    const buttons = screen.getAllByRole('button');
    const selectedBtn = buttons.find((b) => b.textContent?.includes('def5678'));
    expect(selectedBtn?.className).toContain('border-[var(--color-accent)]');
  });
});
