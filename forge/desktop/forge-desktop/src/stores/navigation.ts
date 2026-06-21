import { create } from 'zustand';

export type View = 'dashboard' | 'code' | 'decisions' | 'bugs' | 'analysis' | 'history' | 'graph';

interface NavigationState {
  activeView: View;
  sidebarCollapsed: boolean;
  detailPanelOpen: boolean;
  selectedFile: string | null;
  selectedDecision: string | null;
  selectedBug: string | null;
  selectedReport: string | null;
  selectedCommit: string | null;
  setView: (view: View) => void;
  toggleSidebar: () => void;
  toggleDetailPanel: () => void;
  selectFile: (path: string | null) => void;
  selectDecision: (id: string | null) => void;
  selectBug: (id: string | null) => void;
  selectReport: (id: string | null) => void;
  selectCommit: (id: string | null) => void;
}

export const useNavigation = create<NavigationState>((set) => ({
  activeView: 'dashboard',
  sidebarCollapsed: false,
  detailPanelOpen: false,
  selectedFile: null,
  selectedDecision: null,
  selectedBug: null,
  selectedReport: null,
  selectedCommit: null,
  setView: (view) => set({ activeView: view }),
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  toggleDetailPanel: () => set((s) => ({ detailPanelOpen: !s.detailPanelOpen })),
  selectFile: (path) => set({ selectedFile: path, detailPanelOpen: path !== null }),
  selectDecision: (id) => set({ selectedDecision: id, detailPanelOpen: id !== null }),
  selectBug: (id) => set({ selectedBug: id, detailPanelOpen: id !== null }),
  selectReport: (id) => set({ selectedReport: id, detailPanelOpen: id !== null }),
  selectCommit: (id) => set({ selectedCommit: id, detailPanelOpen: id !== null }),
}));
