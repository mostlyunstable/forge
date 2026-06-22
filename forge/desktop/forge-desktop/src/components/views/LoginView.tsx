import { useState } from 'react';
import { useSettings } from '@/stores/settings';
import { setApiBaseUrl } from '@/lib/api';

export function LoginView() {
  const { apiUrl, setApiUrl, setAuthToken } = useSettings();
  const [serverUrl, setServerUrl] = useState(apiUrl);
  const [apiKey, setApiKey] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleConnect = async () => {
    setLoading(true);
    setError(null);

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

      // Any response (even 4xx) means the server is reachable
      if (res.ok || res.status === 401 || res.status === 404 || res.status === 422) {
        setApiBaseUrl(serverUrl);
        setApiUrl(serverUrl);
        setAuthToken(apiKey || 'dev-token');
      } else {
        throw new Error(`Server returned ${res.status}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-full w-full flex-col items-center justify-center bg-[var(--color-bg-base)]">
      <div className="w-full max-w-[320px]">
        {/* Logo */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-3 flex h-[32px] w-[32px] items-center justify-center rounded-[4px] bg-[var(--color-accent-blue)]">
            <span className="text-[14px] font-bold text-white">F</span>
          </div>
          <div className="text-[20px] font-semibold text-[var(--color-text-primary)]">
            Forge
          </div>
          <div className="mt-1 text-[12px] text-[var(--color-text-muted)]">
            Engineering Memory System
          </div>
        </div>

        {/* Form */}
        <div className="space-y-[16px]">
          <div>
            <label className="text-label mb-[4px] block">Server URL</label>
            <input
              type="text"
              value={serverUrl}
              onChange={(e) => setServerUrl(e.target.value)}
              className="input"
              placeholder="http://localhost:8000"
            />
          </div>

          <div>
            <label className="text-label mb-[4px] block">API Key</label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="input"
              placeholder="Optional"
            />
          </div>

          {error && (
            <div className="text-[12px] text-[var(--color-accent-red)]">
              {error}
            </div>
          )}

          <button
            onClick={handleConnect}
            disabled={loading}
            className="btn btn-primary w-full"
          >
            {loading ? 'Connecting...' : 'Connect'}
          </button>
        </div>
      </div>
    </div>
  );
}