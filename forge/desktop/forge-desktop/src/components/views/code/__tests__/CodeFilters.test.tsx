import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CodeFilters } from '../CodeFilters';

describe('CodeFilters', () => {
  it('renders search input', () => {
    render(<CodeFilters onSearch={vi.fn()} />);
    expect(screen.getByPlaceholderText('Search files...')).toBeInTheDocument();
  });

  it('calls onSearch callback when typing', async () => {
    const onSearch = vi.fn();
    render(<CodeFilters onSearch={onSearch} />);
    const input = screen.getByPlaceholderText('Search files...');
    await userEvent.type(input, 'test');
    expect(onSearch).toHaveBeenCalledTimes(4);
    expect(onSearch).toHaveBeenLastCalledWith('test');
  });

  it('input has correct placeholder text', () => {
    render(<CodeFilters onSearch={vi.fn()} />);
    const input = screen.getByPlaceholderText('Search files...');
    expect(input).toHaveAttribute('placeholder', 'Search files...');
  });
});
