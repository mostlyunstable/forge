import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { setApiBaseUrl } from '@/lib/api';

interface SettingsState {
  apiUrl: string;
  authToken: string | null;
  currentProjectId: string | null;
  connectionStatus: 'connected' | 'disconnected' | 'checking';
  setApiUrl: (url: string) => void;
  setAuthToken: (token: string | null) => void;
  setCurrentProject: (id: string | null) => void;
  setConnectionStatus: (status: 'connected' | 'disconnected' | 'checking') => void;
}

export const useSettings = create<SettingsState>()(
  persist(
    (set) => ({
      apiUrl: 'http://127.0.0.1:8000',
      authToken: null,
      currentProjectId: null,
      connectionStatus: 'checking',
      setApiUrl: (url) => {
        setApiBaseUrl(url);
        set({ apiUrl: url });
      },
      setAuthToken: (token) => set({ authToken: token }),
      setCurrentProject: (id) => set({ currentProjectId: id }),
      setConnectionStatus: (status) => set({ connectionStatus: status }),
    }),
    { name: 'forge-settings' },
  ),
);