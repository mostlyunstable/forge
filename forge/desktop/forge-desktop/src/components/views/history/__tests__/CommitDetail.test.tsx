import { describe, it, expect, vi } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@/test/test-utils';
import { CommitDetail } from '../CommitDetail';

describe('CommitDetail', () => {
  it('renders commit SHA', () => {
    renderWithProviders(<CommitDetail id="abc1234" onClose={vi.fn()} />);
    expect(screen.getByText('abc1234')).toBeInTheDocument();
  });

  it('renders commit message', () => {
    renderWithProviders(<CommitDetail id="abc1234" onClose={vi.fn()} />);
    expect(screen.getByText('feat: add chat endpoint')).toBeInTheDocument();
  });

  it('renders author and timestamp', () => {
    renderWithProviders(<CommitDetail id="abc1234" onClose={vi.fn()} />);
    expect(screen.getByText('@dev')).toBeInTheDocument();
    expect(screen.getByText('2 hours ago')).toBeInTheDocument();
  });

  it('renders files changed section', () => {
    renderWithProviders(<CommitDetail id="abc1234" onClose={vi.fn()} />);
    expect(screen.getByText('Files Changed')).toBeInTheDocument();
    expect(screen.getByText('forge/presentation/routes/chat.py')).toBeInTheDocument();
    expect(screen.getByText('forge/application/chat.py')).toBeInTheDocument();
    expect(screen.getByText('forge/domain/chat.py')).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(<CommitDetail id="abc1234" onClose={onClose} />);

    const closeButton = screen.getByRole('button');
    await user.click(closeButton);
    expect(onClose).toHaveBeenCalled();
  });

  it('renders commit heading', () => {
    renderWithProviders(<CommitDetail id="abc1234" onClose={vi.fn()} />);
    expect(screen.getByText('Commit')).toBeInTheDocument();
  });
});
