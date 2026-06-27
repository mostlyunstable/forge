import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@/test/test-utils';
import { RiskFeed } from '../RiskFeed';

describe('RiskFeed', () => {
  it('renders risk feed heading', () => {
    renderWithProviders(<RiskFeed />);
    expect(screen.getByText('Risk Feed')).toBeInTheDocument();
  });

  it('renders all risk items', () => {
    renderWithProviders(<RiskFeed />);
    expect(screen.getByText('auth module')).toBeInTheDocument();
    expect(screen.getByText('api routes')).toBeInTheDocument();
    expect(screen.getByText('tests')).toBeInTheDocument();
  });

  it('shows risk scores', () => {
    renderWithProviders(<RiskFeed />);
    expect(screen.getByText('8/10')).toBeInTheDocument();
    expect(screen.getByText('5/10')).toBeInTheDocument();
    expect(screen.getByText('2/10')).toBeInTheDocument();
  });

  it('renders colored risk level indicators', () => {
    const { container } = renderWithProviders(<RiskFeed />);
    const dots = container.querySelectorAll('.rounded-full');
    expect(dots.length).toBeGreaterThanOrEqual(3);
  });

  it('renders view all button', () => {
    renderWithProviders(<RiskFeed />);
    expect(screen.getByText('View all')).toBeInTheDocument();
  });
});
