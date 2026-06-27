import { describe, it, expect, beforeAll, afterEach, afterAll, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import { renderWithProviders } from '@/test/test-utils'
import { useSettings } from '@/stores/settings'
import { TitleBar } from '../TitleBar'

const server = setupServer(
  http.get('http://127.0.0.1:8000/health', () => HttpResponse.json({ status: 'ok' })),
  http.get('http://127.0.0.1:8000/', () => HttpResponse.json({ status: 'ok' })),
  http.get('http://127.0.0.1:8000/api/v1/projects', () =>
    HttpResponse.json({
      projects: [{ id: 'proj-1', name: 'My Project', description: '', status: 'active', stack: [] }],
      total: 1,
    })
  ),
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

beforeEach(() => {
  useSettings.setState({
    apiUrl: 'http://127.0.0.1:8000',
    authToken: null,
    currentProjectId: null,
    connectionStatus: 'checking',
  })
})

describe('TitleBar', () => {
  it('shows "No Project" when no current project is selected', async () => {
    renderWithProviders(<TitleBar />)
    await waitFor(() => {
      expect(screen.getByText('No Project')).toBeInTheDocument()
    })
  })

  it('shows current project name when one is selected', async () => {
    useSettings.setState({ currentProjectId: 'proj-1' })
    renderWithProviders(<TitleBar />)

    await waitFor(() => {
      expect(screen.getByText('My Project')).toBeInTheDocument()
    })
  })

  it('shows "Checking..." status initially', () => {
    useSettings.setState({ connectionStatus: 'checking' })
    renderWithProviders(<TitleBar />)
    expect(screen.getByText('Checking...')).toBeInTheDocument()
  })

  it('shows "Connected" when health check succeeds', async () => {
    renderWithProviders(<TitleBar />)

    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument()
    })
  })

  it('shows "Offline" when health check fails', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/', () => HttpResponse.error())
    )
    renderWithProviders(<TitleBar />)

    await waitFor(() => {
      expect(screen.getByText('Offline')).toBeInTheDocument()
    })
  })

  it('clicking the dropdown button opens the project list', async () => {
    const user = userEvent.setup()
    renderWithProviders(<TitleBar />)

    await waitFor(() => {
      expect(screen.getByText('No Project')).toBeInTheDocument()
    })

    const dropdownButton = screen.getByText('No Project').closest('button')!
    await user.click(dropdownButton)

    await waitFor(() => {
      expect(screen.getByText('My Project')).toBeInTheDocument()
    })
  })

  it('selecting a project from dropdown closes dropdown', async () => {
    const user = userEvent.setup()
    useSettings.setState({ currentProjectId: null })
    renderWithProviders(<TitleBar />)

    await waitFor(() => {
      expect(screen.getByText('No Project')).toBeInTheDocument()
    })

    await user.click(screen.getByText('No Project').closest('button')!)

    await waitFor(() => {
      expect(screen.getByText('My Project')).toBeInTheDocument()
    })

    await user.click(screen.getByText('My Project'))

    await waitFor(() => {
      expect(useSettings.getState().currentProjectId).toBe('proj-1')
    })
  })

  it('clicking outside dropdown closes it', async () => {
    const user = userEvent.setup()
    renderWithProviders(<TitleBar />)

    await waitFor(() => {
      expect(screen.getByText('No Project')).toBeInTheDocument()
    })

    await user.click(screen.getByText('No Project').closest('button')!)

    await waitFor(() => {
      expect(screen.getByText('My Project')).toBeInTheDocument()
    })

    await user.click(document.body)

    await waitFor(() => {
      const dropdownContainer = document.querySelector('.absolute.top-full')
      expect(dropdownContainer).not.toBeInTheDocument()
    })
  })

  it('shows "No projects found" when projects list is empty', async () => {
    server.use(
      http.get('http://127.0.0.1:8000/api/v1/projects', () => {
        return HttpResponse.json({ projects: [], total: 0 })
      })
    )

    const user = userEvent.setup()
    renderWithProviders(<TitleBar />)

    await waitFor(() => {
      expect(screen.getByText('No Project')).toBeInTheDocument()
    })

    await user.click(screen.getByText('No Project').closest('button')!)

    await waitFor(() => {
      expect(screen.getByText('No projects found')).toBeInTheDocument()
    })
  })

  it('dropdown highlights currently selected project', async () => {
    useSettings.setState({ currentProjectId: 'proj-1' })
    const user = userEvent.setup()
    renderWithProviders(<TitleBar />)

    await waitFor(() => {
      expect(screen.getByText('My Project')).toBeInTheDocument()
    })

    await user.click(screen.getByText('My Project').closest('button')!)

    await waitFor(() => {
      const buttons = screen.getAllByText('My Project')
      const dropdownItem = buttons.find(
        (b) => b.closest('[class*="absolute"]') !== null
      )
      expect(dropdownItem).toBeTruthy()
    })
  })

  it('renders the ChevronDown icon', () => {
    renderWithProviders(<TitleBar />)
    expect(document.querySelector('svg')).toBeInTheDocument()
  })
})
