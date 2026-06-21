import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface SettingsState {
  apiUrl: string;
  authToken: string | null;
  currentProjectId: string | null;
  setApiUrl: (url: string) => void;
  setAuthToken: (token: string | null) => void;
  setCurrentProject: (id: string | null) => void;
}

export const useSettings = create<SettingsState>()(
  persist(
    (set) => ({
      apiUrl: 'http://127.0.0.1:8000',
      authToken: null,
      currentProjectId: null,
      setApiUrl: (url) => set({ apiUrl: url }),
      setAuthToken: (token) => set({ authToken: token }),
      setCurrentProject: (id) => set({ currentProjectId: id }),
    }),
    { name: 'forge-settings' },
  ),
);
