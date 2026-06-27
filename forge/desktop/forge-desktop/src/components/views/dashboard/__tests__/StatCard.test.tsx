import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@/test/test-utils';
import { StatCard } from '../StatCard';

describe('StatCard', () => {
  it('renders label and value', () => {
    renderWithProviders(<StatCard label="Files Indexed" value="42" />);
    expect(screen.getByText('Files Indexed')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
  });

  it('renders with icon', () => {
    renderWithProviders(<StatCard label="Bugs" value="5" icon="bug" />);
    expect(screen.getByText('Bugs')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('renders positive trend', () => {
    renderWithProviders(<StatCard label="Decisions" value="12" trend={15} />);
    expect(screen.getByText('15% from last week')).toBeInTheDocument();
    expect(screen.getByText('↑')).toBeInTheDocument();
  });

  it('renders negative trend', () => {
    renderWithProviders(<StatCard label="Bugs" value="3" trend={-8} />);
    expect(screen.getByText('8% from last week')).toBeInTheDocument();
    expect(screen.getByText('↓')).toBeInTheDocument();
  });

  it('hides trend when zero', () => {
    renderWithProviders(<StatCard label="Score" value="10" trend={0} />);
    expect(screen.queryByText(/from last week/)).not.toBeInTheDocument();
  });

  it('hides trend when undefined', () => {
    renderWithProviders(<StatCard label="Score" value="10" />);
    expect(screen.queryByText(/from last week/)).not.toBeInTheDocument();
  });

  it('renders empty value as empty string', () => {
    renderWithProviders(<StatCard label="Empty" value="" />);
    expect(screen.getByText('Empty')).toBeInTheDocument();
  });
});
