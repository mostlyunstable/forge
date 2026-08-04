import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useSettings } from '@/stores/settings';

vi.mock('@/lib/api', () => ({
  setApiBaseUrl: vi.fn(),
}));

import { setApiBaseUrl } from '@/lib/api';

const initialState = {
  apiUrl: 'http://127.0.0.1:8000',
  authToken: null,
  currentProjectId: null,
  connectionStatus: 'checking' as const,
};

describe('useSettings', () => {
  beforeEach(() => {
    useSettings.setState(initialState);
    vi.clearAllMocks();
  });

  it('has correct default state', () => {
    const state = useSettings.getState();
    expect(state.apiUrl).toBe('http://127.0.0.1:8000');
    expect(state.authToken).toBeNull();
    expect(state.currentProjectId).toBeNull();
    expect(state.connectionStatus).toBe('checking');
  });

  it('setApiUrl updates apiUrl and calls setApiBaseUrl', () => {
    useSettings.getState().setApiUrl('http://localhost:3000');
    const state = useSettings.getState();
    expect(state.apiUrl).toBe('http://localhost:3000');
    expect(setApiBaseUrl).toHaveBeenCalledWith('http://localhost:3000');
  });

  it('setAuthToken updates authToken', () => {
    useSettings.getState().setAuthToken('my-secret-token');
    expect(useSettings.getState().authToken).toBe('my-secret-token');
  });

  it('setAuthToken can set token to null', () => {
    useSettings.getState().setAuthToken('my-secret-token');
    useSettings.getState().setAuthToken(null);
    expect(useSettings.getState().authToken).toBeNull();
  });

  it('setCurrentProject updates currentProjectId', () => {
    useSettings.getState().setCurrentProject('proj-123');
    expect(useSettings.getState().currentProjectId).toBe('proj-123');
  });

  it('setCurrentProject can set to null', () => {
    useSettings.getState().setCurrentProject('proj-123');
    useSettings.getState().setCurrentProject(null);
    expect(useSettings.getState().currentProjectId).toBeNull();
  });

  it('setConnectionStatus updates connectionStatus', () => {
    useSettings.getState().setConnectionStatus('connected');
    expect(useSettings.getState().connectionStatus).toBe('connected');

    useSettings.getState().setConnectionStatus('disconnected');
    expect(useSettings.getState().connectionStatus).toBe('disconnected');

    useSettings.getState().setConnectionStatus('checking');
    expect(useSettings.getState().connectionStatus).toBe('checking');
  });

  it('persists state to localStorage', () => {
    useSettings.getState().setApiUrl('http://custom:9000');
    useSettings.getState().setAuthToken('token-abc');
    useSettings.getState().setCurrentProject('proj-456');
    useSettings.getState().setConnectionStatus('connected');

    const stored = localStorage.getItem('forge-settings');
    expect(stored).toBeTruthy();

    const parsed = JSON.parse(stored!);
    expect(parsed.state.apiUrl).toBe('http://custom:9000');
    expect(parsed.state.authToken).toBe('token-abc');
    expect(parsed.state.currentProjectId).toBe('proj-456');
    expect(parsed.state.connectionStatus).toBe('connected');
  });
});
