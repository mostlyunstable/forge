import { describe, it, expect, beforeAll, afterEach, afterAll } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { type ReactNode } from 'react'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import { handlers } from '@/test/handlers'
import {
  useProjects,
  useDecisions,
  useBugs,
  useCreateDecision,
  useCreateBug,
  useDeleteDecision,
  useChat,
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

describe('useProjects', () => {
  it('shows loading then data', async () => {
    const { result } = renderHook(() => useProjects(), { wrapper: createWrapper() })

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.projects).toHaveLength(1)
    expect(result.current.data?.projects[0].name).toBe('Test Project')
  })

  it('handles error', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/projects', () => {
        return HttpResponse.json({ detail: 'Server error' }, { status: 500 })
      })
    )
    const { result } = renderHook(() => useProjects(), { wrapper: createWrapper() })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })
  })
})

describe('useDecisions', () => {
  it('shows loading then data', async () => {
    const { result } = renderHook(() => useDecisions('proj-1'), { wrapper: createWrapper() })

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.decisions).toHaveLength(1)
    expect(result.current.data?.decisions[0].title).toBe('Use PostgreSQL')
  })

  it('is disabled when no projectId', () => {
    const { result } = renderHook(() => useDecisions(null), { wrapper: createWrapper() })
    expect(result.current.isLoading).toBe(false)
    expect(result.current.fetchStatus).toBe('idle')
  })
})

describe('useBugs', () => {
  it('shows loading then data', async () => {
    const { result } = renderHook(() => useBugs('proj-1'), { wrapper: createWrapper() })

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.bugs).toHaveLength(1)
    expect(result.current.data?.bugs[0].title).toBe('Login fails on Safari')
  })

  it('is disabled when no projectId', () => {
    const { result } = renderHook(() => useBugs(null), { wrapper: createWrapper() })
    expect(result.current.isLoading).toBe(false)
    expect(result.current.fetchStatus).toBe('idle')
  })
})

describe('useCreateDecision', () => {
  it('calls API and returns data', async () => {
    const { result } = renderHook(() => useCreateDecision(), { wrapper: createWrapper() })

    result.current.mutate({
      project_id: 'proj-1',
      title: 'New decision',
      decision: 'Details',
      reason: 'Because',
      alternatives: [],
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.id).toBe('dec-new')
  })
})

describe('useCreateBug', () => {
  it('calls API and returns data', async () => {
    const { result } = renderHook(() => useCreateBug(), { wrapper: createWrapper() })

    result.current.mutate({
      project_id: 'proj-1',
      title: 'New bug',
      problem: 'Something is broken',
      root_cause: 'Unknown',
      solution: 'Fix it',
      severity: 'high',
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.id).toBe('bug-new')
  })
})

describe('useDeleteDecision', () => {
  it('calls API successfully', async () => {
    const { result } = renderHook(() => useDeleteDecision(), { wrapper: createWrapper() })

    result.current.mutate('dec-1')

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })
  })
})

describe('useChat', () => {
  it('sends message and returns response', async () => {
    const { result } = renderHook(() => useChat(), { wrapper: createWrapper() })

    result.current.mutate({ projectId: 'proj-1', message: 'What is this project?' })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.response).toContain('Forge')
    expect(result.current.data?.sources).toHaveLength(1)
  })
})
