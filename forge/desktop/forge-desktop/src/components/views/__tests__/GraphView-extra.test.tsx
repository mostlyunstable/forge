import { describe, it, expect, beforeAll, afterEach, afterAll, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
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

describe('GraphView - extra coverage', () => {
  it('renders SVG with nodes when decisions and bugs exist', async () => {
    renderWithProviders(<GraphView />)

    await waitFor(() => {
      const svg = document.querySelector('svg.w-full')
      expect(svg).toBeInTheDocument()
    })

    // SVG should contain node groups
    await waitFor(() => {
      const circles = document.querySelectorAll('svg.w-full circle')
      expect(circles.length).toBeGreaterThan(0)
    })
  })

  it('renders text labels for nodes', async () => {
    renderWithProviders(<GraphView />)

    await waitFor(() => {
      const texts = document.querySelectorAll('svg.w-full text')
      expect(texts.length).toBeGreaterThan(0)
    })
  })

  it('renders links between sequential decisions', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/memory/decisions', () => {
        return HttpResponse.json({
          decisions: [
            { id: 'd1', title: 'Decision 1', decision: 'First', status: 'accepted', created_at: '2025-01-01T00:00:00Z' },
            { id: 'd2', title: 'Decision 2', decision: 'Second', status: 'accepted', created_at: '2025-01-02T00:00:00Z' },
          ],
          total: 2,
          project_id: 'proj-1',
        })
      })
    )

    renderWithProviders(<GraphView />)

    await waitFor(() => {
      const lines = document.querySelectorAll('svg.w-full line')
      expect(lines.length).toBeGreaterThan(0)
    })
  })

  it('renders links between sequential bugs', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/memory/bugs', () => {
        return HttpResponse.json({
          bugs: [
            { id: 'b1', title: 'Bug 1', severity: 'high', resolved: false, created_at: '2025-01-01T00:00:00Z' },
            { id: 'b2', title: 'Bug 2', severity: 'low', resolved: true, created_at: '2025-01-02T00:00:00Z' },
          ],
          total: 2,
          project_id: 'proj-1',
        })
      })
    )

    renderWithProviders(<GraphView />)

    await waitFor(() => {
      const lines = document.querySelectorAll('svg.w-full line')
      expect(lines.length).toBeGreaterThan(0)
    })
  })

  it('shows "No data" state when all sources are empty', async () => {
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

  it('shows legend with all three categories', async () => {
    renderWithProviders(<GraphView />)

    await waitFor(() => {
      expect(screen.getByText('Legend')).toBeInTheDocument()
    })

    expect(screen.getByText('Decision')).toBeInTheDocument()
    expect(screen.getByText('Report')).toBeInTheDocument()
    expect(screen.getByText('Bug')).toBeInTheDocument()
  })

  it('legend has colored dots for each category', async () => {
    renderWithProviders(<GraphView />)

    await waitFor(() => {
      expect(screen.getByText('Legend')).toBeInTheDocument()
    })

    const dots = document.querySelectorAll('.rounded-full')
    expect(dots.length).toBeGreaterThanOrEqual(3)
  })

  it('zoom in button works', async () => {
    const user = userEvent.setup()
    renderWithProviders(<GraphView />)

    await waitFor(() => {
      expect(screen.getByText('Knowledge Graph')).toBeInTheDocument()
    })

    // Find zoom in button (first button after the title controls)
    const buttons = document.querySelectorAll('button.btn-ghost')
    const zoomInButton = buttons[0]

    await user.click(zoomInButton)

    // The SVG should have a scale transform applied
    await waitFor(() => {
      const svg = document.querySelector('svg.w-full')
      expect(svg).toHaveStyle({ transform: 'scale(1.25)' })
    })
  })

  it('zoom out button works', async () => {
    const user = userEvent.setup()
    renderWithProviders(<GraphView />)

    await waitFor(() => {
      expect(screen.getByText('Knowledge Graph')).toBeInTheDocument()
    })

    const buttons = document.querySelectorAll('button.btn-ghost')
    const zoomOutButton = buttons[1]

    await user.click(zoomOutButton)

    await waitFor(() => {
      const svg = document.querySelector('svg.w-full')
      expect(svg).toHaveStyle({ transform: 'scale(0.75)' })
    })
  })

  it('reset zoom button returns to scale 1', async () => {
    const user = userEvent.setup()
    renderWithProviders(<GraphView />)

    await waitFor(() => {
      expect(screen.getByText('Knowledge Graph')).toBeInTheDocument()
    })

    const buttons = document.querySelectorAll('button.btn-ghost')
    const zoomInButton = buttons[0]
    const resetButton = buttons[2]

    // Zoom in first
    await user.click(zoomInButton)

    // Then reset
    await user.click(resetButton)

    await waitFor(() => {
      const svg = document.querySelector('svg.w-full')
      expect(svg).toHaveStyle({ transform: 'scale(1)' })
    })
  })

  it('does not render SVG when loading', () => {
    // Without data loaded, the component should show loading skeleton
    const { container } = renderWithProviders(<GraphView />)
    expect(container.querySelector('svg.w-full')).not.toBeInTheDocument()
  })

  it('renders with reports data', async () => {
    renderWithProviders(<GraphView />)

    await waitFor(() => {
      const svg = document.querySelector('svg.w-full')
      expect(svg).toBeInTheDocument()
    })

    // Should have nodes for decisions, bugs, and reports
    await waitFor(() => {
      const circles = document.querySelectorAll('svg.w-full circle')
      expect(circles.length).toBeGreaterThanOrEqual(3)
    })
  })

  it('node circles have correct colors', async () => {
    renderWithProviders(<GraphView />)

    await waitFor(() => {
      const circles = document.querySelectorAll('svg.w-full circle')
      expect(circles.length).toBeGreaterThan(0)
    })

    const circles = document.querySelectorAll('svg.w-full circle')
    const fills = Array.from(circles).map((c) => c.getAttribute('fill'))
    // Should contain the color codes for decision, bug, report
    expect(fills).toContain('#4A4AFF')
    expect(fills).toContain('#EF4444')
    expect(fills).toContain('#06B6D4')
  })
})
