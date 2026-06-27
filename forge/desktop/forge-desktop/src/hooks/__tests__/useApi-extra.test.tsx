import { describe, it, expect, beforeAll, afterEach, afterAll } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act } from '@testing-library/react'
import { type ReactNode } from 'react'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import { handlers } from '@/test/handlers'
import {
  useProject,
  useDecision,
  useBug,
  useIndexStatus,
  useStartIndex,
  useAnalysisReports,
  useAnalysisReport,
  useAnalyzePR,
  useSearchCode,
  useFileEntries,
  useSearchMemories,
  useGitCommits,
  useUpdateDecision,
  useUpdateBug,
  useDeleteBug,
} from '../useApi'

const server = setupServer(...handlers)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

function createWrapper() {
  const qc = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  })
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  )
}

describe('useProject', () => {
  it('fetches a single project when id is provided', async () => {
    const { result } = renderHook(() => useProject('proj-1'), { wrapper: createWrapper() })

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.id).toBe('proj-1')
    expect(result.current.data?.name).toBe('Test Project')
  })

  it('is disabled when id is null', () => {
    const { result } = renderHook(() => useProject(null), { wrapper: createWrapper() })
    expect(result.current.isLoading).toBe(false)
    expect(result.current.fetchStatus).toBe('idle')
  })
})

describe('useDecision', () => {
  it('fetches a single decision when id is provided', async () => {
    const { result } = renderHook(() => useDecision('dec-1'), { wrapper: createWrapper() })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.id).toBe('dec-1')
    expect(result.current.data?.title).toBe('Use PostgreSQL')
  })

  it('is disabled when id is null', () => {
    const { result } = renderHook(() => useDecision(null), { wrapper: createWrapper() })
    expect(result.current.isLoading).toBe(false)
    expect(result.current.fetchStatus).toBe('idle')
  })
})

describe('useBug', () => {
  it('fetches a single bug when id is provided', async () => {
    const { result } = renderHook(() => useBug('bug-1'), { wrapper: createWrapper() })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.id).toBe('bug-1')
    expect(result.current.data?.title).toBe('Login fails on Safari')
  })

  it('is disabled when id is null', () => {
    const { result } = renderHook(() => useBug(null), { wrapper: createWrapper() })
    expect(result.current.isLoading).toBe(false)
    expect(result.current.fetchStatus).toBe('idle')
  })
})

describe('useIndexStatus', () => {
  it('fetches status when projectId is provided', async () => {
    const { result } = renderHook(() => useIndexStatus('proj-1'), { wrapper: createWrapper() })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.project_id).toBe('proj-1')
    expect(result.current.data?.total_files_indexed).toBe(10)
  })

  it('is disabled when projectId is null', () => {
    const { result } = renderHook(() => useIndexStatus(null), { wrapper: createWrapper() })
    expect(result.current.isLoading).toBe(false)
    expect(result.current.fetchStatus).toBe('idle')
  })

  it('refetches when running_job is present', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/index/status/:projectId', () => {
        return HttpResponse.json({
          project_id: 'proj-1',
          total_files_indexed: 10,
          last_index_job: null,
          running_job: { id: 'job-running', status: 'running' },
          candidates_by_kind: {},
        })
      })
    )

    const { result } = renderHook(() => useIndexStatus('proj-1'), { wrapper: createWrapper() })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.running_job).toBeTruthy()
  })
})

describe('useStartIndex', () => {
  it('calls API and returns job data', async () => {
    const { result } = renderHook(() => useStartIndex(), { wrapper: createWrapper() })

    await act(async () => {
      await result.current.mutateAsync({ project_id: 'proj-1', repo_path: '/path/to/repo' })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })
    expect(result.current.data?.id).toBe('job-1')
    expect(result.current.data?.status).toBe('running')
  })

  it('shows error state on failure', async () => {
    server.use(
      http.post('http://127.0.0.1:8000/api/v1/index/jobs', () => {
        return HttpResponse.json({ detail: 'Server error' }, { status: 500 })
      })
    )

    const { result } = renderHook(() => useStartIndex(), { wrapper: createWrapper() })

    let caughtError: unknown = null
    await act(async () => {
      try {
        await result.current.mutateAsync({ project_id: 'proj-1', repo_path: '/path' })
      } catch (e) {
        caughtError = e
      }
    })

    expect(caughtError).toBeTruthy()
    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })
    expect(result.current.error).toBeTruthy()
  })
})

describe('useAnalysisReports', () => {
  it('fetches reports when projectId is provided', async () => {
    const { result } = renderHook(() => useAnalysisReports('proj-1'), { wrapper: createWrapper() })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.reports).toHaveLength(1)
    expect(result.current.data?.reports[0].title).toBe('Refactor auth module')
  })

  it('is disabled when projectId is null', () => {
    const { result } = renderHook(() => useAnalysisReports(null), { wrapper: createWrapper() })
    expect(result.current.isLoading).toBe(false)
    expect(result.current.fetchStatus).toBe('idle')
  })
})

describe('useAnalysisReport', () => {
  it('fetches a single report when id is provided', async () => {
    const { result } = renderHook(() => useAnalysisReport('rpt-1'), { wrapper: createWrapper() })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.id).toBe('rpt-1')
    expect(result.current.data?.summary).toBe('Major refactor of the authentication module')
  })

  it('is disabled when id is null', () => {
    const { result } = renderHook(() => useAnalysisReport(null), { wrapper: createWrapper() })
    expect(result.current.isLoading).toBe(false)
    expect(result.current.fetchStatus).toBe('idle')
  })
})

describe('useAnalyzePR', () => {
  it('calls API and returns report data', async () => {
    const { result } = renderHook(() => useAnalyzePR(), { wrapper: createWrapper() })

    await act(async () => {
      await result.current.mutateAsync({ project_id: 'proj-1', pr_number: 42 })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })
    expect(result.current.data?.report_id).toBe('rpt-new')
  })

  it('shows error state on failure', async () => {
    server.use(
      http.post('http://127.0.0.1:8000/api/v1/analysis/pr', () => {
        return HttpResponse.json({ detail: 'Analysis failed' }, { status: 500 })
      })
    )

    const { result } = renderHook(() => useAnalyzePR(), { wrapper: createWrapper() })

    let caughtError: unknown = null
    await act(async () => {
      try {
        await result.current.mutateAsync({ project_id: 'proj-1', pr_number: 42 })
      } catch (e) {
        caughtError = e
      }
    })

    expect(caughtError).toBeTruthy()
    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })
    expect(result.current.error).toBeTruthy()
  })
})

describe('useSearchCode', () => {
  it('fetches results when query and projectId are provided', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/code/search', () => {
        return HttpResponse.json({
          results: [{ id: 'e1', name: 'main.ts', entry_type: 'function', file_path: 'src/main.ts', language: 'typescript', start_line: 1, end_line: 10 }],
          query: 'test',
          total: 1,
        })
      })
    )

    const { result } = renderHook(() => useSearchCode('test', 'proj-1'), { wrapper: createWrapper() })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.results).toHaveLength(1)
  })

  it('is disabled when query is empty', () => {
    const { result } = renderHook(() => useSearchCode('', 'proj-1'), { wrapper: createWrapper() })
    expect(result.current.isLoading).toBe(false)
    expect(result.current.fetchStatus).toBe('idle')
  })

  it('is disabled when projectId is null', () => {
    const { result } = renderHook(() => useSearchCode('test', null), { wrapper: createWrapper() })
    expect(result.current.isLoading).toBe(false)
    expect(result.current.fetchStatus).toBe('idle')
  })
})

describe('useFileEntries', () => {
  it('fetches entries when projectId and filePath are provided', async () => {
    const { result } = renderHook(() => useFileEntries('proj-1', 'src/main.ts'), { wrapper: createWrapper() })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.file_path).toBe('src/main.ts')
  })

  it('is disabled when projectId is null', () => {
    const { result } = renderHook(() => useFileEntries(null, 'src/main.ts'), { wrapper: createWrapper() })
    expect(result.current.isLoading).toBe(false)
    expect(result.current.fetchStatus).toBe('idle')
  })

  it('is disabled when filePath is null', () => {
    const { result } = renderHook(() => useFileEntries('proj-1', null), { wrapper: createWrapper() })
    expect(result.current.isLoading).toBe(false)
    expect(result.current.fetchStatus).toBe('idle')
  })
})

describe('useSearchMemories', () => {
  it('fetches results when query is provided', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/memory/search', () => {
        return HttpResponse.json({ results: [], query: 'auth', total: 0 })
      })
    )

    const { result } = renderHook(() => useSearchMemories('auth'), { wrapper: createWrapper() })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.query).toBe('auth')
  })

  it('is disabled when query is empty', () => {
    const { result } = renderHook(() => useSearchMemories(''), { wrapper: createWrapper() })
    expect(result.current.isLoading).toBe(false)
    expect(result.current.fetchStatus).toBe('idle')
  })

  it('passes projectId when provided', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/memory/search', ({ request }) => {
        const url = new URL(request.url)
        const projectId = url.searchParams.get('project_id')
        return HttpResponse.json({ results: [], query: 'test', total: 0, project_id: projectId })
      })
    )

    const { result } = renderHook(() => useSearchMemories('test', 'proj-1'), { wrapper: createWrapper() })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })
  })
})

describe('useGitCommits', () => {
  it('fetches commits when projectId is provided', async () => {
    const { result } = renderHook(() => useGitCommits('proj-1'), { wrapper: createWrapper() })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.commits).toHaveLength(1)
    expect(result.current.data?.commits[0].sha).toBe('abc1234')
  })

  it('is disabled when projectId is null', () => {
    const { result } = renderHook(() => useGitCommits(null), { wrapper: createWrapper() })
    expect(result.current.isLoading).toBe(false)
    expect(result.current.fetchStatus).toBe('idle')
  })
})

describe('useUpdateDecision', () => {
  it('calls API and returns updated data', async () => {
    const { result } = renderHook(() => useUpdateDecision(), { wrapper: createWrapper() })

    await act(async () => {
      await result.current.mutateAsync({ id: 'dec-1', data: { title: 'Updated Title' } })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })
    expect(result.current.data?.title).toBe('Updated Title')
  })

  it('shows error state on failure', async () => {
    server.use(
      http.put('http://127.0.0.1:8000/api/v1/memory/decisions/:id', () => {
        return HttpResponse.json({ detail: 'Not found' }, { status: 404 })
      })
    )

    const { result } = renderHook(() => useUpdateDecision(), { wrapper: createWrapper() })

    let caughtError: unknown = null
    await act(async () => {
      try {
        await result.current.mutateAsync({ id: 'dec-1', data: { title: 'Updated' } })
      } catch (e) {
        caughtError = e
      }
    })

    expect(caughtError).toBeTruthy()
    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })
    expect(result.current.error).toBeTruthy()
  })
})

describe('useUpdateBug', () => {
  it('calls API and returns updated data', async () => {
    const { result } = renderHook(() => useUpdateBug(), { wrapper: createWrapper() })

    await act(async () => {
      await result.current.mutateAsync({ id: 'bug-1', data: { title: 'Updated Bug' } })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })
    expect(result.current.data?.title).toBe('Updated Bug')
  })

  it('shows error state on failure', async () => {
    server.use(
      http.put('http://127.0.0.1:8000/api/v1/memory/bugs/:id', () => {
        return HttpResponse.json({ detail: 'Not found' }, { status: 404 })
      })
    )

    const { result } = renderHook(() => useUpdateBug(), { wrapper: createWrapper() })

    let caughtError: unknown = null
    await act(async () => {
      try {
        await result.current.mutateAsync({ id: 'bug-1', data: { title: 'Updated' } })
      } catch (e) {
        caughtError = e
      }
    })

    expect(caughtError).toBeTruthy()
    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })
    expect(result.current.error).toBeTruthy()
  })
})

describe('useDeleteBug', () => {
  it('calls API and succeeds', async () => {
    const { result } = renderHook(() => useDeleteBug(), { wrapper: createWrapper() })

    await act(async () => {
      await result.current.mutateAsync('bug-1')
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })
  })

  it('shows error state on failure', async () => {
    server.use(
      http.delete('http://127.0.0.1:8000/api/v1/memory/bugs/:id', () => {
        return HttpResponse.json({ detail: 'Not found' }, { status: 404 })
      })
    )

    const { result } = renderHook(() => useDeleteBug(), { wrapper: createWrapper() })

    let caughtError: unknown = null
    await act(async () => {
      try {
        await result.current.mutateAsync('bug-1')
      } catch (e) {
        caughtError = e
      }
    })

    expect(caughtError).toBeTruthy()
    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })
    expect(result.current.error).toBeTruthy()
  })
})
