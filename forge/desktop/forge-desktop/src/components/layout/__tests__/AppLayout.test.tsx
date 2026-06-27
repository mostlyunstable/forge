import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AppLayout } from '../AppLayout';

vi.mock('@/stores/settings', () => ({
  useSettings: vi.fn(() => ({
    apiUrl: 'http://127.0.0.1:8000',
    currentProjectId: null,
    connectionStatus: 'checking',
    setConnectionStatus: vi.fn(),
  })),
}));

vi.mock('@/stores/settings-dialog', () => ({
  useSettingsDialog: vi.fn(() => ({
    isOpen: false,
    open: vi.fn(),
    close: vi.fn(),
  })),
}));

vi.mock('@/hooks/useApi', () => ({
  useDecisions: vi.fn(() => ({ data: { total: 0 } })),
  useBugs: vi.fn(() => ({ data: { bugs: [] } })),
  useProjects: vi.fn(() => ({ data: { projects: [] } })),
}));

vi.mock('@/lib/api', () => ({
  checkServerConnection: vi.fn(() => Promise.resolve(true)),
}));

describe('AppLayout', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders children', () => {
    render(
      <AppLayout>
        <div>Main content</div>
      </AppLayout>
    );

    expect(screen.getByText('Main content')).toBeInTheDocument();
  });

  it('renders Sidebar (logo text)', () => {
    render(
      <AppLayout>
        <div>content</div>
      </AppLayout>
    );

    expect(screen.getByText('Forge')).toBeInTheDocument();
  });

  it('renders TitleBar (project selector area)', () => {
    render(
      <AppLayout>
        <div>content</div>
      </AppLayout>
    );

    expect(screen.getByText('No Project')).toBeInTheDocument();
  });

  it('renders CommandPalette (search trigger)', () => {
    render(
      <AppLayout>
        <div>content</div>
      </AppLayout>
    );

    expect(screen.getByText('Search')).toBeInTheDocument();
  });

  it('has proper layout structure', () => {
    const { container } = render(
      <AppLayout>
        <div>content</div>
      </AppLayout>
    );

    const root = container.firstChild as HTMLElement;
    expect(root).toHaveClass('flex', 'h-screen', 'w-screen', 'flex-col', 'overflow-hidden');
  });
});
