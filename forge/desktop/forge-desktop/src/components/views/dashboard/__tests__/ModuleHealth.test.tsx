import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@/test/test-utils';
import { ModuleHealth } from '../ModuleHealth';

describe('ModuleHealth', () => {
  it('renders module health heading', () => {
    renderWithProviders(<ModuleHealth />);
    expect(screen.getByText('Module Health')).toBeInTheDocument();
  });

  it('renders all module names', () => {
    renderWithProviders(<ModuleHealth />);
    expect(screen.getByText('domain')).toBeInTheDocument();
    expect(screen.getByText('application')).toBeInTheDocument();
    expect(screen.getByText('infrastructure')).toBeInTheDocument();
    expect(screen.getByText('presentation')).toBeInTheDocument();
  });

  it('renders health percentages', () => {
    renderWithProviders(<ModuleHealth />);
    expect(screen.getByText('82%')).toBeInTheDocument();
    expect(screen.getByText('68%')).toBeInTheDocument();
    expect(screen.getByText('95%')).toBeInTheDocument();
    expect(screen.getByText('45%')).toBeInTheDocument();
  });

  it('renders risk labels for each module', () => {
    renderWithProviders(<ModuleHealth />);
    expect(screen.getAllByText('low').length).toBe(2);
    expect(screen.getByText('medium')).toBeInTheDocument();
    expect(screen.getByText('high')).toBeInTheDocument();
  });
});
