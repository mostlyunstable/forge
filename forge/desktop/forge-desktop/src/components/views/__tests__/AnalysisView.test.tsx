import { describe, it, expect, beforeAll, afterEach, afterAll, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import { handlers } from '@/test/handlers'
import { renderWithProviders } from '@/test/test-utils'
import { useSettings } from '@/stores/settings'
import { AnalysisView } from '../AnalysisView'

const server = setupServer(...handlers)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

beforeEach(() => {
  useSettings.setState({ currentProjectId: 'proj-1', apiUrl: 'http://127.0.0.1:8000' })
})

describe('AnalysisView', () => {
  it('shows loading state', () => {
    renderWithProviders(<AnalysisView />)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('shows report list after loading', async () => {
    renderWithProviders(<AnalysisView />)
    await waitFor(() => {
      expect(screen.getByText('Refactor auth module')).toBeInTheDocument()
    })
  })

  it('shows report count in header', async () => {
    renderWithProviders(<AnalysisView />)
    await waitFor(() => {
      expect(screen.getByText('1 report')).toBeInTheDocument()
    })
  })

  it('shows risk level badge', async () => {
    renderWithProviders(<AnalysisView />)
    await waitFor(() => {
      expect(screen.getByText('Medium')).toBeInTheDocument()
    })
  })

  it('shows empty state when no reports', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/analysis/reports', () => {
        return HttpResponse.json({ reports: [], total: 0, project_id: 'proj-1' })
      })
    )
    renderWithProviders(<AnalysisView />)
    await waitFor(() => {
      expect(screen.getByText('No analysis reports yet')).toBeInTheDocument()
    })
  })

  it('clicking a report shows report detail panel', async () => {
    const user = userEvent.setup()
    renderWithProviders(<AnalysisView />)

    await waitFor(() => {
      expect(screen.getByText('Refactor auth module')).toBeInTheDocument()
    })

    await user.click(screen.getByText('Refactor auth module'))

    await waitFor(() => {
      expect(screen.getByText('Report')).toBeInTheDocument()
    })
  })

  it('report detail shows recommendations', async () => {
    const user = userEvent.setup()
    renderWithProviders(<AnalysisView />)

    await waitFor(() => {
      expect(screen.getByText('Refactor auth module')).toBeInTheDocument()
    })

    await user.click(screen.getByText('Refactor auth module'))

    await waitFor(() => {
      expect(screen.getByText('Recommendations')).toBeInTheDocument()
      expect(screen.getByText('Add integration tests')).toBeInTheDocument()
    })
  })
})
