import { create } from 'zustand';

interface CommandPaletteState {
  isOpen: boolean;
  query: string;
  recentCommands: string[];
  toggle: () => void;
  open: () => void;
  close: () => void;
  setQuery: (query: string) => void;
  addRecentCommand: (command: string) => void;
}

export const useCommandPalette = create<CommandPaletteState>((set) => ({
  isOpen: false,
  query: '',
  recentCommands: [],
  toggle: () => set((s) => ({ isOpen: !s.isOpen })),
  open: () => set({ isOpen: true }),
  close: () => set({ isOpen: false, query: '' }),
  setQuery: (query) => set({ query }),
  addRecentCommand: (command) =>
    set((s) => ({
      recentCommands: [command, ...s.recentCommands.filter((c) => c !== command)].slice(0, 5),
    })),
}));
