import { http, HttpResponse } from 'msw'

const BASE = 'http://127.0.0.1:8000'

export const mockProject = {
  id: 'proj-1',
  name: 'Test Project',
  description: 'A test project',
  stack: ['Python', 'TypeScript'],
  goals: [],
  status: 'active',
  repository_url: null,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
}

export const mockDecision = {
  id: 'dec-1',
  project_id: 'proj-1',
  title: 'Use PostgreSQL',
  decision: 'Use PostgreSQL for the main database',
  reason: 'Mature, reliable',
  alternatives: ['MySQL', 'SQLite'],
  status: 'accepted',
  created_at: '2025-01-01T00:00:00Z',
}

export const mockBug = {
  id: 'bug-1',
  project_id: 'proj-1',
  title: 'Login fails on Safari',
  problem: 'Users cannot log in on Safari',
  root_cause: 'Cookie settings',
  solution: 'Updated cookie config',
  affected_files: ['auth.ts'],
  severity: 'high',
  resolved: false,
  created_at: '2025-01-01T00:00:00Z',
}

export const mockReport = {
  id: 'rpt-1',
  project_id: 'proj-1',
  pr_number: 42,
  title: 'Refactor auth module',
  risk_score: 6,
  risk_level: 'medium',
  files_changed: 5,
  blast_radius: 3,
  created_at: '2025-01-01T00:00:00Z',
}

export const mockReportDetail = {
  ...mockReport,
  summary: 'Major refactor of the authentication module',
  directly_affected: ['auth.ts'],
  transitively_affected: ['user.ts'],
  reverse_affected: ['app.ts'],
  related_decisions: 1,
  related_bugs: 2,
  related_commits: 3,
  recommendations: [
    { area: 'testing', priority: 'high', description: 'Add integration tests', files: ['auth.test.ts'] },
  ],
}

export const mockCommit = {
  sha: 'abc1234',
  message: 'feat: add login',
  author: 'Test User',
  classification: 'feature',
  files_changed: ['auth.ts'],
  timestamp: '2025-01-01T00:00:00Z',
}

export const handlers = [
  // Health
  http.get(`${BASE}/health`, () => {
    return HttpResponse.json({ status: 'ok' })
  }),

  // Projects
  http.get(`${BASE}/api/v1/projects`, () => {
    return HttpResponse.json({ projects: [mockProject], total: 1 })
  }),
  http.get(`${BASE}/api/v1/projects/:id`, () => {
    return HttpResponse.json(mockProject)
  }),
  http.post(`${BASE}/api/v1/projects`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>
    return HttpResponse.json({ ...mockProject, name: body.name as string }, { status: 201 })
  }),
  http.delete(`${BASE}/api/v1/projects/:id`, () => {
    return HttpResponse.json({ deleted: true })
  }),

  // Decisions
  http.get(`${BASE}/api/v1/memory/decisions`, () => {
    return HttpResponse.json({ decisions: [mockDecision], total: 1, project_id: 'proj-1' })
  }),
  http.get(`${BASE}/api/v1/memory/decisions/:id`, () => {
    return HttpResponse.json(mockDecision)
  }),
  http.post(`${BASE}/api/v1/memory/decisions`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>
    return HttpResponse.json({ ...mockDecision, title: body.title as string, id: 'dec-new' }, { status: 201 })
  }),
  http.put(`${BASE}/api/v1/memory/decisions/:id`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>
    return HttpResponse.json({ ...mockDecision, ...body })
  }),
  http.delete(`${BASE}/api/v1/memory/decisions/:id`, () => {
    return HttpResponse.json({ deleted: true })
  }),

  // Bugs
  http.get(`${BASE}/api/v1/memory/bugs`, () => {
    return HttpResponse.json({ bugs: [mockBug], total: 1, project_id: 'proj-1' })
  }),
  http.get(`${BASE}/api/v1/memory/bugs/:id`, () => {
    return HttpResponse.json(mockBug)
  }),
  http.post(`${BASE}/api/v1/memory/bugs`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>
    return HttpResponse.json({ ...mockBug, title: body.title as string, id: 'bug-new' }, { status: 201 })
  }),
  http.put(`${BASE}/api/v1/memory/bugs/:id`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>
    return HttpResponse.json({ ...mockBug, ...body })
  }),
  http.delete(`${BASE}/api/v1/memory/bugs/:id`, () => {
    return HttpResponse.json({ deleted: true })
  }),

  // Memory search
  http.get(`${BASE}/api/v1/memory/search`, () => {
    return HttpResponse.json({ results: [], query: 'test', total: 0 })
  }),

  // Code
  http.get(`${BASE}/api/v1/code/search`, () => {
    return HttpResponse.json({ results: [], query: 'test', total: 0 })
  }),
  http.get(`${BASE}/api/v1/code/files/:projectId/*`, () => {
    return HttpResponse.json({ file_path: 'src/main.ts', entries: [], total: 0 })
  }),

  // Indexing
  http.get(`${BASE}/api/v1/index/status/:projectId`, () => {
    return HttpResponse.json({
      project_id: 'proj-1',
      total_files_indexed: 10,
      last_index_job: null,
      running_job: null,
      candidates_by_kind: { bug: 2, decision: 1 },
    })
  }),
  http.post(`${BASE}/api/v1/index/jobs`, () => {
    return HttpResponse.json({
      id: 'job-1',
      project_id: 'proj-1',
      type: 'full',
      status: 'running',
      started_at: '2025-01-01T00:00:00Z',
      completed_at: null,
      progress: {},
      result: {},
      error_log: [],
      state_hash: 'abc',
      created_by: 'test',
      created_at: '2025-01-01T00:00:00Z',
      duration_seconds: null,
    })
  }),
  http.get(`${BASE}/api/v1/index/jobs/:jobId`, () => {
    return HttpResponse.json({
      id: 'job-1',
      project_id: 'proj-1',
      type: 'full',
      status: 'completed',
      started_at: '2025-01-01T00:00:00Z',
      completed_at: '2025-01-01T00:01:00Z',
      progress: {},
      result: {},
      error_log: [],
      state_hash: 'abc',
      created_by: 'test',
      created_at: '2025-01-01T00:00:00Z',
      duration_seconds: 60,
    })
  }),
  http.get(`${BASE}/api/v1/index/jobs`, () => {
    return HttpResponse.json({ jobs: [], total: 0 })
  }),

  // Analysis
  http.get(`${BASE}/api/v1/analysis/reports`, () => {
    return HttpResponse.json({ reports: [mockReport], total: 1, project_id: 'proj-1' })
  }),
  http.get(`${BASE}/api/v1/analysis/reports/:id`, () => {
    return HttpResponse.json(mockReportDetail)
  }),
  http.post(`${BASE}/api/v1/analysis/pr`, () => {
    return HttpResponse.json({
      report_id: 'rpt-new',
      project_id: 'proj-1',
      pr_number: 42,
      title: 'PR #42',
      summary: 'Analysis complete',
      risk_score: 5,
      risk_level: 'medium',
      blast_radius: 2,
      files_changed: 3,
      directly_affected: ['a.ts'],
      transitively_affected: ['b.ts'],
      reverse_affected: ['c.ts'],
      related_decisions: 0,
      related_bugs: 0,
      related_commits: 1,
      recommendations: [],
    })
  }),

  // Chat
  http.post(`${BASE}/api/v1/chat`, () => {
    return HttpResponse.json({
      response: 'Forge is a persistent engineering memory system.',
      sources: [{ type: 'code', name: 'README.md', score: 0.9, file: 'README.md' }],
      project_id: 'proj-1',
    })
  }),

  // Git
  http.get(`${BASE}/api/v1/git/commits/:projectId`, () => {
    return HttpResponse.json({
      commits: [mockCommit],
      total: 1,
      by_classification: { feature: 1 },
    })
  }),
]
