import { describe, it, expect, beforeEach, afterEach, beforeAll, afterAll } from 'vitest'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { handlers } from '@/test/handlers'
import * as api from '@/lib/api'

const server = setupServer(...handlers)

beforeAll(() => server.listen({ onUnhandledRequest: 'bypass' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

beforeEach(() => {
  api.setApiBaseUrl('http://127.0.0.1:8000')
  api.setAuthToken('')
})

// ── Base URL helpers ──

describe('setApiBaseUrl', () => {
  it('appends /api/v1 when not present', () => {
    api.setApiBaseUrl('http://localhost:3000')
    expect(api.getApiBaseUrl()).toBe('http://localhost:3000/api/v1')
  })

  it('does not double-append /api/v1', () => {
    api.setApiBaseUrl('http://localhost:3000/api/v1')
    expect(api.getApiBaseUrl()).toBe('http://localhost:3000/api/v1')
  })

  it('handles trailing slash before /api/v1', () => {
    api.setApiBaseUrl('http://localhost:3000/')
    expect(api.getApiBaseUrl()).toBe('http://localhost:3000//api/v1')
  })
})

describe('getApiBaseUrl', () => {
  it('returns the current base URL', () => {
    expect(api.getApiBaseUrl()).toBe('http://127.0.0.1:8000/api/v1')
  })
})

describe('setAuthToken / getAuthToken', () => {
  it('stores and retrieves the auth token', () => {
    api.setAuthToken('my-secret-token')
    expect(api.getAuthToken()).toBe('my-secret-token')
  })

  it('clears the auth token with empty string', () => {
    api.setAuthToken('token')
    api.setAuthToken('')
    expect(api.getAuthToken()).toBe('')
  })

  it('returns null initially after reset', () => {
    api.setAuthToken('')
    expect(api.getAuthToken()).toBe('')
  })
})

// ── checkServerConnection ──

describe('checkServerConnection', () => {
  it('returns true when server responds ok', async () => {
    const result = await api.checkServerConnection('http://127.0.0.1:8000/api/v1')
    expect(result).toBe(true)
  })

  it('returns false when server is unreachable', async () => {
    const result = await api.checkServerConnection('http://localhost:19999/api/v1')
    expect(result).toBe(false)
  })

  it('returns false on server error', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/health', () => {
        return HttpResponse.json({ error: 'down' }, { status: 500 })
      })
    )
    const result = await api.checkServerConnection('http://127.0.0.1:8000/api/v1')
    expect(result).toBe(false)
  })

  it('strips /api/v1 and hits /health', async () => {
    let hitUrl = ''
    server.use(
      http.get('http://127.0.0.1:8000/health', ({ request }) => {
        hitUrl = new URL(request.url).pathname
        return HttpResponse.json({ status: 'ok' })
      })
    )
    await api.checkServerConnection('http://127.0.0.1:8000/api/v1')
    expect(hitUrl).toBe('/health')
  })
})

// ── Auth token in headers ──

describe('auth token headers', () => {
  it('includes Authorization header when token is set', async () => {
    let receivedAuth: string | null = null
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/projects', ({ request }) => {
        receivedAuth = request.headers.get('Authorization')
        return HttpResponse.json({ projects: [], total: 0 })
      })
    )

    api.setAuthToken('test-token-123')
    await api.projects.list()

    expect(receivedAuth).toBe('Bearer test-token-123')
  })

  it('does not include Authorization header when token is empty', async () => {
    let receivedAuth: string | null = null
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/projects', ({ request }) => {
        receivedAuth = request.headers.get('Authorization')
        return HttpResponse.json({ projects: [], total: 0 })
      })
    )

    await api.projects.list()

    expect(receivedAuth).toBeNull()
  })
})

// ── Projects ──

describe('projects', () => {
  describe('list', () => {
    it('fetches the projects list', async () => {
      const result = await api.projects.list()
      expect(result.total).toBe(1)
      expect(result.projects).toHaveLength(1)
      expect(result.projects[0].id).toBe('proj-1')
    })
  })

  describe('get', () => {
    it('fetches a single project by id', async () => {
      const result = await api.projects.get('proj-1')
      expect(result.id).toBe('proj-1')
      expect(result.name).toBe('Test Project')
      expect(result.stack).toEqual(['Python', 'TypeScript'])
    })
  })

  describe('create', () => {
    it('creates a project with POST', async () => {
      const result = await api.projects.create({
        name: 'New Project',
        description: 'desc',
        stack: ['Go'],
      })
      expect(result.name).toBe('New Project')
    })
  })

  describe('delete', () => {
    it('deletes a project by id', async () => {
      const result = await api.projects.delete('proj-1')
      expect(result.deleted).toBe(true)
    })
  })
})

// ── Decisions ──

describe('decisions', () => {
  describe('list', () => {
    it('fetches decisions for a project', async () => {
      const result = await api.decisions.list('proj-1')
      expect(result.total).toBe(1)
      expect(result.decisions).toHaveLength(1)
      expect(result.project_id).toBe('proj-1')
    })

    it('sends skip and limit as query params', async () => {
      let capturedUrl = ''
      server.use(
        http.get('http://127.0.0.1:8000/api/v1/memory/decisions', ({ request }) => {
          capturedUrl = request.url
          return HttpResponse.json({ decisions: [], total: 0, project_id: 'proj-1' })
        })
      )

      await api.decisions.list('proj-1', 10, 50)
      const url = new URL(capturedUrl)
      expect(url.searchParams.get('project_id')).toBe('proj-1')
      expect(url.searchParams.get('skip')).toBe('10')
      expect(url.searchParams.get('limit')).toBe('50')
    })
  })

  describe('get', () => {
    it('fetches a single decision by id', async () => {
      const result = await api.decisions.get('dec-1')
      expect(result.id).toBe('dec-1')
      expect(result.title).toBe('Use PostgreSQL')
    })
  })

  describe('create', () => {
    it('creates a decision with POST', async () => {
      const result = await api.decisions.create({
        project_id: 'proj-1',
        title: 'New Decision',
        decision: 'Use Redis',
      })
      expect(result.id).toBe('dec-new')
      expect(result.title).toBe('New Decision')
    })
  })

  describe('update', () => {
    it('updates a decision with PUT', async () => {
      const result = await api.decisions.update('dec-1', {
        title: 'Updated Title',
        status: 'deprecated',
      })
      expect(result.title).toBe('Updated Title')
      expect(result.status).toBe('deprecated')
    })
  })

  describe('delete', () => {
    it('deletes a decision by id', async () => {
      const result = await api.decisions.delete('dec-1')
      expect(result.deleted).toBe(true)
    })
  })
})

// ── Bugs ──

describe('bugs', () => {
  describe('list', () => {
    it('fetches bugs for a project', async () => {
      const result = await api.bugs.list('proj-1')
      expect(result.total).toBe(1)
      expect(result.bugs).toHaveLength(1)
      expect(result.project_id).toBe('proj-1')
    })

    it('sends skip and limit as query params', async () => {
      let capturedUrl = ''
      server.use(
        http.get('http://127.0.0.1:8000/api/v1/memory/bugs', ({ request }) => {
          capturedUrl = request.url
          return HttpResponse.json({ bugs: [], total: 0, project_id: 'proj-1' })
        })
      )

      await api.bugs.list('proj-1', 5, 25)
      const url = new URL(capturedUrl)
      expect(url.searchParams.get('project_id')).toBe('proj-1')
      expect(url.searchParams.get('skip')).toBe('5')
      expect(url.searchParams.get('limit')).toBe('25')
    })
  })

  describe('get', () => {
    it('fetches a single bug by id', async () => {
      const result = await api.bugs.get('bug-1')
      expect(result.id).toBe('bug-1')
      expect(result.title).toBe('Login fails on Safari')
      expect(result.severity).toBe('high')
    })
  })

  describe('create', () => {
    it('creates a bug with POST', async () => {
      const result = await api.bugs.create({
        project_id: 'proj-1',
        title: 'New Bug',
        problem: 'Crashes on load',
      })
      expect(result.id).toBe('bug-new')
      expect(result.title).toBe('New Bug')
    })
  })

  describe('update', () => {
    it('updates a bug with PUT', async () => {
      const result = await api.bugs.update('bug-1', {
        severity: 'critical',
        resolved: true,
      })
      expect(result.severity).toBe('critical')
      expect(result.resolved).toBe(true)
    })
  })

  describe('delete', () => {
    it('deletes a bug by id', async () => {
      const result = await api.bugs.delete('bug-1')
      expect(result.deleted).toBe(true)
    })
  })
})

// ── Code ──

describe('code', () => {
  describe('search', () => {
    it('searches code with query params', async () => {
      const result = await api.code.search('login', 'proj-1')
      expect(result.query).toBe('test')
      expect(result.total).toBe(0)
    })

    it('encodes the query in the URL', async () => {
      let capturedUrl = ''
      server.use(
        http.get('http://127.0.0.1:8000/api/v1/code/search', ({ request }) => {
          capturedUrl = request.url
          return HttpResponse.json({ results: [], query: 'hello world', total: 0 })
        })
      )

      await api.code.search('hello world', 'proj-1')
      const url = new URL(capturedUrl)
      expect(url.searchParams.get('q')).toBe('hello world')
      expect(url.searchParams.get('project_id')).toBe('proj-1')
    })
  })

  describe('getFileEntries', () => {
    it('fetches file entries for a path', async () => {
      const result = await api.code.getFileEntries('proj-1', 'src/main.ts')
      expect(result.file_path).toBe('src/main.ts')
      expect(result.total).toBe(0)
    })
  })
})

// ── Indexing ──

describe('indexing', () => {
  describe('getStatus', () => {
    it('fetches index status for a project', async () => {
      const result = await api.indexing.getStatus('proj-1')
      expect(result.project_id).toBe('proj-1')
      expect(result.total_files_indexed).toBe(10)
      expect(result.candidates_by_kind).toEqual({ bug: 2, decision: 1 })
    })
  })

  describe('start', () => {
    it('starts an index job with POST', async () => {
      const result = await api.indexing.start({
        project_id: 'proj-1',
        repo_path: '/repos/test',
      })
      expect(result.id).toBe('job-1')
      expect(result.status).toBe('running')
    })
  })

  describe('getJob', () => {
    it('fetches a specific index job', async () => {
      const result = await api.indexing.getJob('job-1')
      expect(result.id).toBe('job-1')
      expect(result.status).toBe('completed')
      expect(result.duration_seconds).toBe(60)
    })
  })

  describe('listJobs', () => {
    it('lists jobs for a project', async () => {
      const result = await api.indexing.listJobs('proj-1')
      expect(result.total).toBe(0)
      expect(result.jobs).toEqual([])
    })
  })
})

// ── Analysis ──

describe('analysis', () => {
  describe('listReports', () => {
    it('fetches analysis reports for a project', async () => {
      const result = await api.analysis.listReports('proj-1')
      expect(result.total).toBe(1)
      expect(result.reports).toHaveLength(1)
      expect(result.project_id).toBe('proj-1')
    })

    it('sends skip and limit as query params', async () => {
      let capturedUrl = ''
      server.use(
        http.get('http://127.0.0.1:8000/api/v1/analysis/reports', ({ request }) => {
          capturedUrl = request.url
          return HttpResponse.json({ reports: [], total: 0, project_id: 'proj-1' })
        })
      )

      await api.analysis.listReports('proj-1', 5, 10)
      const url = new URL(capturedUrl)
      expect(url.searchParams.get('project_id')).toBe('proj-1')
      expect(url.searchParams.get('skip')).toBe('5')
      expect(url.searchParams.get('limit')).toBe('10')
    })
  })

  describe('getReport', () => {
    it('fetches a single report by id', async () => {
      const result = await api.analysis.getReport('rpt-1')
      expect(result.id).toBe('rpt-1')
      expect(result.title).toBe('Refactor auth module')
      expect(result.risk_score).toBe(6)
      expect(result.summary).toBe('Major refactor of the authentication module')
      expect(result.recommendations).toHaveLength(1)
    })
  })

  describe('analyzePR', () => {
    it('submits a PR analysis with POST', async () => {
      const result = await api.analysis.analyzePR({
        project_id: 'proj-1',
        pr_number: 42,
      })
      expect(result.report_id).toBe('rpt-new')
      expect(result.pr_number).toBe(42)
      expect(result.risk_score).toBe(5)
      expect(result.directly_affected).toEqual(['a.ts'])
    })

    it('sends all provided fields in the body', async () => {
      let capturedBody: Record<string, unknown> = {}
      server.use(
        http.post('http://127.0.0.1:8000/api/v1/analysis/pr', async ({ request }) => {
          capturedBody = (await request.json()) as Record<string, unknown>
          return HttpResponse.json({
            report_id: 'rpt-new',
            project_id: 'proj-1',
            pr_number: 42,
            title: 'PR #42',
            summary: '',
            risk_score: 0,
            risk_level: 'low',
            blast_radius: 0,
            files_changed: 0,
            directly_affected: [],
            transitively_affected: [],
            reverse_affected: [],
            related_decisions: 0,
            related_bugs: 0,
            related_commits: 0,
            recommendations: [],
          })
        })
      )

      await api.analysis.analyzePR({
        project_id: 'proj-1',
        pr_number: 42,
        base_sha: 'aaa',
        head_sha: 'bbb',
        title: 'Test PR',
      })

      expect(capturedBody.project_id).toBe('proj-1')
      expect(capturedBody.pr_number).toBe(42)
      expect(capturedBody.base_sha).toBe('aaa')
      expect(capturedBody.head_sha).toBe('bbb')
      expect(capturedBody.title).toBe('Test PR')
    })
  })
})

// ── Chat ──

describe('chat', () => {
  describe('send', () => {
    it('sends a chat message with POST', async () => {
      const result = await api.chat.send('proj-1', 'What is this project about?')
      expect(result.response).toBe('Forge is a persistent engineering memory system.')
      expect(result.sources).toHaveLength(1)
      expect(result.project_id).toBe('proj-1')
    })

    it('sends project_id and message in the body', async () => {
      let capturedBody: Record<string, unknown> = {}
      server.use(
        http.post('http://127.0.0.1:8000/api/v1/chat', async ({ request }) => {
          capturedBody = (await request.json()) as Record<string, unknown>
          return HttpResponse.json({
            response: 'ok',
            sources: [],
            project_id: 'proj-1',
          })
        })
      )

      await api.chat.send('proj-1', 'Hello!')
      expect(capturedBody.project_id).toBe('proj-1')
      expect(capturedBody.message).toBe('Hello!')
    })
  })
})

// ── Search ──

describe('search', () => {
  describe('memories', () => {
    it('searches memories with query', async () => {
      const result = await api.search.memories('login')
      expect(result.query).toBe('test')
      expect(result.total).toBe(0)
    })

    it('includes project_id when provided', async () => {
      let capturedUrl = ''
      server.use(
        http.get('http://127.0.0.1:8000/api/v1/memory/search', ({ request }) => {
          capturedUrl = request.url
          return HttpResponse.json({ results: [], query: 'test', total: 0 })
        })
      )

      await api.search.memories('login', 'proj-1')
      const url = new URL(capturedUrl)
      expect(url.searchParams.get('project_id')).toBe('proj-1')
    })

    it('omits project_id when not provided', async () => {
      let capturedUrl = ''
      server.use(
        http.get('http://127.0.0.1:8000/api/v1/memory/search', ({ request }) => {
          capturedUrl = request.url
          return HttpResponse.json({ results: [], query: 'test', total: 0 })
        })
      )

      await api.search.memories('login')
      const url = new URL(capturedUrl)
      expect(url.searchParams.has('project_id')).toBe(false)
    })
  })
})

// ── Git ──

describe('git', () => {
  describe('getCommits', () => {
    it('fetches commits for a project', async () => {
      const result = await api.git.getCommits('proj-1')
      expect(result.total).toBe(1)
      expect(result.commits).toHaveLength(1)
      expect(result.commits[0].sha).toBe('abc1234')
      expect(result.commits[0].message).toBe('feat: add login')
    })

    it('sends limit as query param', async () => {
      let capturedUrl = ''
      server.use(
        http.get('http://127.0.0.1:8000/api/v1/git/commits/:projectId', ({ request }) => {
          capturedUrl = request.url
          return HttpResponse.json({ commits: [], total: 0, by_classification: {} })
        })
      )

      await api.git.getCommits('proj-1', 10)
      const url = new URL(capturedUrl)
      expect(url.searchParams.get('limit')).toBe('10')
    })

    it('defaults limit to 50', async () => {
      let capturedUrl = ''
      server.use(
        http.get('http://127.0.0.1:8000/api/v1/git/commits/:projectId', ({ request }) => {
          capturedUrl = request.url
          return HttpResponse.json({ commits: [], total: 0, by_classification: {} })
        })
      )

      await api.git.getCommits('proj-1')
      const url = new URL(capturedUrl)
      expect(url.searchParams.get('limit')).toBe('50')
    })
  })
})

// ── Error handling ──

describe('error handling', () => {
  it('throws on 404 with correct status', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/projects/:id', () => {
        return HttpResponse.json({ detail: 'Not found' }, { status: 404 })
      })
    )

    await expect(api.projects.get('nonexistent')).rejects.toThrow('Not found')
    try {
      await api.projects.get('nonexistent')
    } catch (e: unknown) {
      expect((e as { status: number }).status).toBe(404)
    }
  })

  it('throws on 401 with correct status', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/projects', () => {
        return HttpResponse.json({ detail: 'Unauthorized' }, { status: 401 })
      })
    )

    await expect(api.projects.list()).rejects.toThrow('Unauthorized')
    try {
      await api.projects.list()
    } catch (e: unknown) {
      expect((e as { status: number }).status).toBe(401)
    }
  })

  it('throws on 422 with correct status', async () => {
    server.use(
      http.post('http://127.0.0.1:8000/api/v1/projects', () => {
        return HttpResponse.json({ detail: 'Validation error' }, { status: 422 })
      })
    )

    await expect(api.projects.create({ name: '' })).rejects.toThrow('Validation error')
    try {
      await api.projects.create({ name: '' })
    } catch (e: unknown) {
      expect((e as { status: number }).status).toBe(422)
    }
  })

  it('throws on 500 with correct status', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/memory/bugs', () => {
        return HttpResponse.json({ detail: 'Internal error' }, { status: 500 })
      })
    )

    await expect(api.bugs.list('proj-1')).rejects.toThrow('Internal error')
    try {
      await api.bugs.list('proj-1')
    } catch (e: unknown) {
      expect((e as { status: number }).status).toBe(500)
    }
  })

  it('throws ApiError on DELETE failure', async () => {
    server.use(
      http.delete('http://127.0.0.1:8000/api/v1/projects/:id', () => {
        return HttpResponse.json({ detail: 'Cannot delete' }, { status: 403 })
      })
    )

    try {
      await api.projects.delete('proj-1')
    } catch (e: unknown) {
      expect((e as { name: string }).name).toBe('ApiError')
      expect((e as { status: number }).status).toBe(403)
    }
  })

  it('throws ApiError on PUT failure', async () => {
    server.use(
      http.put('http://127.0.0.1:8000/api/v1/memory/decisions/:id', () => {
        return HttpResponse.json({ detail: 'Forbidden' }, { status: 403 })
      })
    )

    try {
      await api.decisions.update('dec-1', { title: 'x' })
    } catch (e: unknown) {
      expect((e as { name: string }).name).toBe('ApiError')
      expect((e as { status: number }).status).toBe(403)
    }
  })
})
