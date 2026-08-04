import { describe, it, expect, beforeAll, afterEach, afterAll, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import { handlers } from '@/test/handlers'
import { renderWithProviders } from '@/test/test-utils'
import { useSettings } from '@/stores/settings'
import { HistoryView } from '../HistoryView'

const server = setupServer(...handlers)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

beforeEach(() => {
  useSettings.setState({ currentProjectId: 'proj-1', apiUrl: 'http://127.0.0.1:8000' })
})

describe('HistoryView', () => {
  it('shows loading state', () => {
    renderWithProviders(<HistoryView />)
    expect(screen.getByText('History')).toBeInTheDocument()
  })

  it('shows commit list after loading', async () => {
    renderWithProviders(<HistoryView />)
    await waitFor(() => {
      expect(screen.getByText('feat: add login')).toBeInTheDocument()
    })
  })

  it('shows truncated SHA', async () => {
    renderWithProviders(<HistoryView />)
    await waitFor(() => {
      expect(screen.getByText('abc1234')).toBeInTheDocument()
    })
  })

  it('shows commit author', async () => {
    renderWithProviders(<HistoryView />)
    await waitFor(() => {
      expect(screen.getByText('Test User')).toBeInTheDocument()
    })
  })

  it('shows empty state when no commits', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/git/commits/:projectId', () => {
        return HttpResponse.json({ commits: [], total: 0, by_classification: {} })
      })
    )
    renderWithProviders(<HistoryView />)
    await waitFor(() => {
      expect(screen.getByText(/No commits indexed yet/)).toBeInTheDocument()
    })
  })
})
