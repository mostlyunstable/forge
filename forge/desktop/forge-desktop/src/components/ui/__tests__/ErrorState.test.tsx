import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ErrorState } from '../ErrorState';

describe('ErrorState', () => {
  it('renders error message', () => {
    render(<ErrorState message="Something failed" />);
    expect(screen.getByText('Something failed')).toBeInTheDocument();
  });

  it('renders error code when provided', () => {
    render(<ErrorState message="Request failed" code="ERR_404" />);
    expect(screen.getByText('ERR_404')).toBeInTheDocument();
  });

  it('does not render error code when not provided', () => {
    render(<ErrorState message="Request failed" />);
    expect(screen.queryByText(/ERR/)).not.toBeInTheDocument();
  });

  it('renders retry button when retry prop is provided', () => {
    const handleRetry = vi.fn();
    render(<ErrorState message="Failed" retry={handleRetry} />);
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
  });

  it('does not render retry button when retry prop is not provided', () => {
    render(<ErrorState message="Failed" />);
    expect(screen.queryByRole('button', { name: /try again/i })).not.toBeInTheDocument();
  });

  it('retry button calls retry function on click', async () => {
    const handleRetry = vi.fn();
    render(<ErrorState message="Failed" retry={handleRetry} />);

    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /try again/i }));

    expect(handleRetry).toHaveBeenCalledOnce();
  });
});
