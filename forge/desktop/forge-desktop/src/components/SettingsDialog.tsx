import { useState } from 'react';
import { useSettings } from '@/stores/settings';
import { X } from 'lucide-react';

interface SettingsDialogProps {
  open: boolean;
  onClose: () => void;
}

export function SettingsDialog({ open, onClose }: SettingsDialogProps) {
  const { apiUrl, setApiUrl, authToken, setAuthToken } = useSettings();
  const [serverUrl, setServerUrl] = useState(apiUrl);
  const [apiKey, setApiKey] = useState(authToken ?? '');
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<'success' | 'error' | null>(null);

  if (!open) return null;

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const baseUrl = serverUrl.endsWith('/api/v1') ? serverUrl : `${serverUrl}/api/v1`;
      const res = await fetch(`${baseUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}),
        },
        body: JSON.stringify({ project_id: 'test', message: 'test' }),
      });
      setTestResult(res.ok || res.status === 401 || res.status === 404 || res.status === 422 ? 'success' : 'error');
    } catch {
      setTestResult('error');
    } finally {
      setTesting(false);
    }
  };

  const handleSave = () => {
    setApiUrl(serverUrl);
    setAuthToken(apiKey || null);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />

      {/* Dialog */}
      <div className="relative w-full max-w-[400px] rounded-[4px] border border-[var(--color-border-default)] bg-[var(--color-bg-surface)]">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[var(--color-border-subtle)] px-6 py-4">
          <h2 className="text-[16px] font-semibold text-[var(--color-text-primary)]">Settings</h2>
          <button onClick={onClose} className="text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]">
            <X className="h-[14px] w-[14px]" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Connection */}
          <div>
            <h3 className="text-label mb-3">Connection</h3>
            <div className="space-y-3">
              <div>
                <label className="text-[12px] text-[var(--color-text-muted)] mb-1 block">Server URL</label>
                <input
                  value={serverUrl}
                  onChange={(e) => setServerUrl(e.target.value)}
                  className="input"
                  placeholder="http://localhost:8000"
                />
              </div>
              <div>
                <label className="text-[12px] text-[var(--color-text-muted)] mb-1 block">API Key</label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="input"
                  placeholder="Optional"
                />
              </div>
              <div className="flex items-center gap-3">
                <button onClick={handleTestConnection} className="btn">
                  {testing ? 'Testing...' : 'Test Connection'}
                </button>
                {testResult === 'success' && (
                  <span className="text-[12px] text-[var(--color-accent-green)]">Connected</span>
                )}
                {testResult === 'error' && (
                  <span className="text-[12px] text-[var(--color-accent-red)]">Failed</span>
                )}
              </div>
            </div>
          </div>

          {/* Appearance */}
          <div>
            <h3 className="text-label mb-3">Appearance</h3>
            <div className="text-[12px] text-[var(--color-text-muted)]">
              Dark theme is the only option for now.
            </div>
          </div>

          {/* About */}
          <div>
            <h3 className="text-label mb-3">About</h3>
            <div className="space-y-1 text-[12px] text-[var(--color-text-muted)]">
              <div>Forge v0.1.0</div>
              <div>Persistent Engineering Memory</div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 border-t border-[var(--color-border-subtle)] px-6 py-4">
          <button onClick={onClose} className="btn">Cancel</button>
          <button onClick={handleSave} className="btn btn-primary">Save</button>
        </div>
      </div>
    </div>
  );
}