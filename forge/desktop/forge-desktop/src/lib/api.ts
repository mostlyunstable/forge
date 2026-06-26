import type {
  ListProjectsResponse,
  Project,
  ListDecisionsResponse,
  Decision,
  ListBugsResponse,
  Bug,
  SearchCodeResponse,
  GetFileEntriesResponse,
  IndexStatusResponse,
  IndexJob,
  AnalyzePRResponse,
  ListAnalysisReportsResponse,
  AnalysisReportDetail,
  SendMessageResponse,
  SearchMemoriesResponse,
  AnalyzeCommitsResponse,
} from './api-types';

const DEFAULT_BASE_URL = 'http://127.0.0.1:8000/api/v1';
let _baseUrl = DEFAULT_BASE_URL;
let _token: string | null = null;

export function setApiBaseUrl(url: string) {
  _baseUrl = url.endsWith('/api/v1') ? url : `${url}/api/v1`;
}

export function getApiBaseUrl(): string {
  return _baseUrl;
}

export function setAuthToken(token: string) {
  _token = token;
}

export function getAuthToken(): string | null {
  return _token;
}

export async function checkServerConnection(baseUrl: string = _baseUrl): Promise<boolean> {
  try {
    const url = baseUrl.replace('/api/v1', '/health');
    const res = await fetch(url, { signal: AbortSignal.timeout(3000) });
    return res.ok;
  } catch {
    return false;
  }
}

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

function getBaseUrl(): string {
  // Use module-level _baseUrl as default; settings store overrides via setApiBaseUrl
  return _baseUrl;
}

function getAuthTokenValue(): string | null {
  return _token;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const baseUrl = getBaseUrl();
  const token = getAuthTokenValue();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const body = await res.text();
    throw new ApiError(res.status, body);
  }

  return res.json();
}

// ── Projects ──

export const projects = {
  list: () => request<ListProjectsResponse>('/projects'),
  get: (id: string) => request<Project>(`/projects/${id}`),
  create: (data: { name: string; description?: string; stack?: string[] }) =>
    request<Project>('/projects', { method: 'POST', body: JSON.stringify(data) }),
  delete: (id: string) =>
    request<{ deleted: boolean }>(`/projects/${id}`, { method: 'DELETE' }),
};

// ── Decisions ──

export const decisions = {
  list: (projectId: string, skip = 0, limit = 100) =>
    request<ListDecisionsResponse>(`/memory/decisions?project_id=${projectId}&skip=${skip}&limit=${limit}`),
  get: (id: string) => request<Decision>(`/memory/decisions/${id}`),
  create: (data: { project_id: string; title: string; decision: string; reason?: string }) =>
    request<Decision>('/memory/decisions', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: { title?: string; decision?: string; reason?: string; status?: string }) =>
    request<Decision>(`/memory/decisions/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id: string) =>
    request<{ deleted: boolean }>(`/memory/decisions/${id}`, { method: 'DELETE' }),
};

// ── Bugs ──

export const bugs = {
  list: (projectId: string, skip = 0, limit = 100) =>
    request<ListBugsResponse>(`/memory/bugs?project_id=${projectId}&skip=${skip}&limit=${limit}`),
  get: (id: string) => request<Bug>(`/memory/bugs/${id}`),
  create: (data: { project_id: string; title: string; problem: string; root_cause?: string; solution?: string; affected_files?: string[]; severity?: string }) =>
    request<Bug>('/memory/bugs', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: { title?: string; problem?: string; root_cause?: string; solution?: string; severity?: string; resolved?: boolean }) =>
    request<Bug>(`/memory/bugs/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id: string) =>
    request<{ deleted: boolean }>(`/memory/bugs/${id}`, { method: 'DELETE' }),
};

// ── Code ──

export const code = {
  search: (query: string, projectId: string) =>
    request<SearchCodeResponse>(`/code/search?q=${encodeURIComponent(query)}&project_id=${projectId}`),
  getFileEntries: (projectId: string, filePath: string) =>
    request<GetFileEntriesResponse>(`/code/files/${projectId}/${filePath}`),
};

// ── Indexing ──

export const indexing = {
  getStatus: (projectId: string) =>
    request<IndexStatusResponse>(`/index/status/${projectId}`),
  start: (data: { project_id: string; repo_path: string; type?: string }) =>
    request<IndexJob>('/index/jobs', { method: 'POST', body: JSON.stringify(data) }),
  getJob: (jobId: string) => request<IndexJob>(`/index/jobs/${jobId}`),
  listJobs: (projectId: string) =>
    request<{ jobs: IndexJob[]; total: number }>(`/index/jobs?project_id=${projectId}`),
};

// ── Analysis ──

export const analysis = {
  listReports: (projectId: string, skip = 0, limit = 20) =>
    request<ListAnalysisReportsResponse>(`/analysis/reports?project_id=${projectId}&skip=${skip}&limit=${limit}`),
  getReport: (reportId: string) =>
    request<AnalysisReportDetail>(`/analysis/reports/${reportId}`),
  analyzePR: (data: { project_id: string; pr_number?: number; base_sha?: string; head_sha?: string; title?: string }) =>
    request<AnalyzePRResponse>('/analysis/pr', { method: 'POST', body: JSON.stringify(data) }),
};

// ── Chat ──

export const chat = {
  send: (projectId: string, message: string) =>
    request<SendMessageResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify({ project_id: projectId, message }),
    }),
};

// ── Search ──

export const search = {
  memories: (query: string, projectId?: string) => {
    const params = new URLSearchParams({ q: query });
    if (projectId) params.set('project_id', projectId);
    return request<SearchMemoriesResponse>(`/memory/search?${params}`);
  },
};

// ── Git ──

export const git = {
  getCommits: (projectId: string, limit = 50) =>
    request<AnalyzeCommitsResponse>(`/git/commits/${projectId}?limit=${limit}`),
};