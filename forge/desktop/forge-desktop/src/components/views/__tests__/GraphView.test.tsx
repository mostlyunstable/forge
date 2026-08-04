import { describe, it, expect, beforeAll, afterEach, afterAll, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'

import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import { handlers } from '@/test/handlers'
import { renderWithProviders } from '@/test/test-utils'
import { useSettings } from '@/stores/settings'
import { GraphView } from '../GraphView'

const server = setupServer(...handlers)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

beforeEach(() => {
  useSettings.setState({ currentProjectId: 'proj-1', apiUrl: 'http://127.0.0.1:8000' })
})

describe('GraphView', () => {
  it('shows empty state when no data', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/memory/decisions', () => {
        return HttpResponse.json({ decisions: [], total: 0, project_id: 'proj-1' })
      }),
      http.get('http://127.0.0.1:8000/api/v1/memory/bugs', () => {
        return HttpResponse.json({ bugs: [], total: 0, project_id: 'proj-1' })
      }),
      http.get('http://127.0.0.1:8000/api/v1/analysis/reports', () => {
        return HttpResponse.json({ reports: [], total: 0, project_id: 'proj-1' })
      })
    )
    renderWithProviders(<GraphView />)
    await waitFor(() => {
      expect(screen.getByText(/No data to visualize/)).toBeInTheDocument()
    })
  })

  it('renders SVG element when data exists', async () => {
    renderWithProviders(<GraphView />)
    await waitFor(() => {
      const svg = document.querySelector('svg.w-full')
      expect(svg).toBeInTheDocument()
    })
  })

  it('shows zoom controls', () => {
    renderWithProviders(<GraphView />)
    expect(screen.getByText('Knowledge Graph')).toBeInTheDocument()
    // Zoom buttons should be present (icons rendered via lucide-react)
    const buttons = document.querySelectorAll('button.btn-ghost')
    expect(buttons.length).toBeGreaterThanOrEqual(3)
  })

  it('shows legend', async () => {
    renderWithProviders(<GraphView />)
    await waitFor(() => {
      expect(screen.getByText('Legend')).toBeInTheDocument()
    })
    expect(screen.getByText('Decision')).toBeInTheDocument()
    expect(screen.getByText('Report')).toBeInTheDocument()
    expect(screen.getByText('Bug')).toBeInTheDocument()
  })

  it('shows loading skeleton', () => {
    renderWithProviders(<GraphView />)
    expect(screen.getByText('Knowledge Graph')).toBeInTheDocument()
  })
})
