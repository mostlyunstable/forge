import { describe, it, expect, beforeEach } from 'vitest';
import { useNavigation } from '@/stores/navigation';

const initialState = {
  activeView: 'dashboard' as const,
  sidebarCollapsed: false,
  detailPanelOpen: false,
  selectedFile: null,
  selectedDecision: null,
  selectedBug: null,
  selectedReport: null,
  selectedCommit: null,
  pendingAction: null,
};

describe('useNavigation', () => {
  beforeEach(() => {
    useNavigation.setState(initialState);
  });

  it('has correct default state', () => {
    const state = useNavigation.getState();
    expect(state.activeView).toBe('dashboard');
    expect(state.sidebarCollapsed).toBe(false);
    expect(state.detailPanelOpen).toBe(false);
    expect(state.selectedFile).toBeNull();
    expect(state.selectedDecision).toBeNull();
    expect(state.selectedBug).toBeNull();
    expect(state.selectedReport).toBeNull();
    expect(state.selectedCommit).toBeNull();
    expect(state.pendingAction).toBeNull();
  });

  it('setView changes activeView', () => {
    useNavigation.getState().setView('code');
    expect(useNavigation.getState().activeView).toBe('code');
  });

  it('all views can be set', () => {
    const views = ['dashboard', 'code', 'decisions', 'bugs', 'analysis', 'history', 'graph'] as const;
    for (const view of views) {
      useNavigation.getState().setView(view);
      expect(useNavigation.getState().activeView).toBe(view);
    }
  });

  it('toggleSidebar toggles sidebarCollapsed', () => {
    expect(useNavigation.getState().sidebarCollapsed).toBe(false);
    useNavigation.getState().toggleSidebar();
    expect(useNavigation.getState().sidebarCollapsed).toBe(true);
    useNavigation.getState().toggleSidebar();
    expect(useNavigation.getState().sidebarCollapsed).toBe(false);
  });

  it('toggleDetailPanel toggles detailPanelOpen', () => {
    expect(useNavigation.getState().detailPanelOpen).toBe(false);
    useNavigation.getState().toggleDetailPanel();
    expect(useNavigation.getState().detailPanelOpen).toBe(true);
    useNavigation.getState().toggleDetailPanel();
    expect(useNavigation.getState().detailPanelOpen).toBe(false);
  });

  it('selectFile sets selectedFile and opens detailPanelOpen when path is not null', () => {
    useNavigation.getState().selectFile('/src/main.ts');
    const state = useNavigation.getState();
    expect(state.selectedFile).toBe('/src/main.ts');
    expect(state.detailPanelOpen).toBe(true);
  });

  it('selectFile with null closes detailPanelOpen', () => {
    useNavigation.getState().selectFile('/src/main.ts');
    expect(useNavigation.getState().detailPanelOpen).toBe(true);
    useNavigation.getState().selectFile(null);
    const state = useNavigation.getState();
    expect(state.selectedFile).toBeNull();
    expect(state.detailPanelOpen).toBe(false);
  });

  it('selectDecision sets selectedDecision and opens detailPanel when id is not null', () => {
    useNavigation.getState().selectDecision('dec-1');
    const state = useNavigation.getState();
    expect(state.selectedDecision).toBe('dec-1');
    expect(state.detailPanelOpen).toBe(true);
  });

  it('selectDecision with null closes detailPanelOpen', () => {
    useNavigation.getState().selectDecision('dec-1');
    useNavigation.getState().selectDecision(null);
    expect(useNavigation.getState().selectedDecision).toBeNull();
    expect(useNavigation.getState().detailPanelOpen).toBe(false);
  });

  it('selectBug sets selectedBug and opens detailPanel when id is not null', () => {
    useNavigation.getState().selectBug('bug-1');
    const state = useNavigation.getState();
    expect(state.selectedBug).toBe('bug-1');
    expect(state.detailPanelOpen).toBe(true);
  });

  it('selectBug with null closes detailPanelOpen', () => {
    useNavigation.getState().selectBug('bug-1');
    useNavigation.getState().selectBug(null);
    expect(useNavigation.getState().selectedBug).toBeNull();
    expect(useNavigation.getState().detailPanelOpen).toBe(false);
  });

  it('selectReport sets selectedReport and opens detailPanel when id is not null', () => {
    useNavigation.getState().selectReport('report-1');
    const state = useNavigation.getState();
    expect(state.selectedReport).toBe('report-1');
    expect(state.detailPanelOpen).toBe(true);
  });

  it('selectReport with null closes detailPanelOpen', () => {
    useNavigation.getState().selectReport('report-1');
    useNavigation.getState().selectReport(null);
    expect(useNavigation.getState().selectedReport).toBeNull();
    expect(useNavigation.getState().detailPanelOpen).toBe(false);
  });

  it('selectCommit sets selectedCommit and opens detailPanel when id is not null', () => {
    useNavigation.getState().selectCommit('abc123');
    const state = useNavigation.getState();
    expect(state.selectedCommit).toBe('abc123');
    expect(state.detailPanelOpen).toBe(true);
  });

  it('selectCommit with null closes detailPanelOpen', () => {
    useNavigation.getState().selectCommit('abc123');
    useNavigation.getState().selectCommit(null);
    expect(useNavigation.getState().selectedCommit).toBeNull();
    expect(useNavigation.getState().detailPanelOpen).toBe(false);
  });

  it('setPendingAction sets the pending action', () => {
    useNavigation.getState().setPendingAction('create-decision');
    expect(useNavigation.getState().pendingAction).toBe('create-decision');
    useNavigation.getState().setPendingAction('create-bug');
    expect(useNavigation.getState().pendingAction).toBe('create-bug');
    useNavigation.getState().setPendingAction('index-codebase');
    expect(useNavigation.getState().pendingAction).toBe('index-codebase');
  });

  it('clearPendingAction sets pendingAction to null', () => {
    useNavigation.getState().setPendingAction('create-decision');
    expect(useNavigation.getState().pendingAction).toBe('create-decision');
    useNavigation.getState().clearPendingAction();
    expect(useNavigation.getState().pendingAction).toBeNull();
  });
});
