import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@/test/test-utils';
import { ActivityFeed } from '../ActivityFeed';

describe('ActivityFeed', () => {
  it('renders recent activity heading', () => {
    renderWithProviders(<ActivityFeed />);
    expect(screen.getByText('Recent Activity')).toBeInTheDocument();
  });

  it('renders list of activity items', () => {
    renderWithProviders(<ActivityFeed />);
    expect(screen.getByText('Index completed: 266 files')).toBeInTheDocument();
    expect(screen.getByText('3 bugs extracted from commit history')).toBeInTheDocument();
    expect(screen.getByText('Decision recorded: "Use FastAPI"')).toBeInTheDocument();
    expect(screen.getByText('PR #142 analyzed (risk: high)')).toBeInTheDocument();
    expect(screen.getByText('Incremental index: 12 new files')).toBeInTheDocument();
  });

  it('shows timestamps for items', () => {
    renderWithProviders(<ActivityFeed />);
    expect(screen.getByText('2h ago')).toBeInTheDocument();
    expect(screen.getByText('5h ago')).toBeInTheDocument();
    expect(screen.getByText('1d ago')).toBeInTheDocument();
    expect(screen.getByText('2d ago')).toBeInTheDocument();
    expect(screen.getByText('3d ago')).toBeInTheDocument();
  });

  it('renders view all button', () => {
    renderWithProviders(<ActivityFeed />);
    expect(screen.getByText('View all')).toBeInTheDocument();
  });

  it('renders all five hardcoded activities', () => {
    const { container } = renderWithProviders(<ActivityFeed />);
    const items = container.querySelectorAll('[class*="hover:bg"]');
    expect(items.length).toBe(5);
  });
});
