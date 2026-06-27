import { describe, it, expect, beforeAll, afterEach, afterAll, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import { handlers } from '@/test/handlers'
import { renderWithProviders } from '@/test/test-utils'
import { useSettings } from '@/stores/settings'
import { LoginView } from '../LoginView'

const server = setupServer(...handlers)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

beforeEach(() => {
  useSettings.setState({
    apiUrl: 'http://127.0.0.1:8000',
    authToken: null,
    currentProjectId: null,
    connectionStatus: 'disconnected',
  })
})

describe('LoginView - extra coverage', () => {
  it('displays error message when connection fails with network error', async () => {
    server.use(
      http.post('http://127.0.0.1:8000/api/v1/chat', () => HttpResponse.error())
    )

    renderWithProviders(<LoginView />)
    await userEvent.click(screen.getByRole('button', { name: /connect/i }))

    await waitFor(() => {
      expect(screen.getByText(/failed to fetch/i)).toBeInTheDocument()
    })
  })

  it('displays error message when server returns unexpected status', async () => {
    server.use(
      http.post('http://127.0.0.1:8000/api/v1/chat', () => {
        return HttpResponse.json({ detail: 'Internal error' }, { status: 500 })
      })
    )

    renderWithProviders(<LoginView />)
    await userEvent.click(screen.getByRole('button', { name: /connect/i }))

    await waitFor(() => {
      expect(screen.getByText(/Server returned 500/)).toBeInTheDocument()
    })
  })

  it('shows loading spinner during connection test', async () => {
    server.use(
      http.post('http://127.0.0.1:8000/api/v1/chat', async () => {
        await new Promise((r) => setTimeout(r, 500))
        return HttpResponse.json({ response: 'ok', sources: [], project_id: 'proj-1' })
      })
    )

    const user = userEvent.setup()
    renderWithProviders(<LoginView />)

    await user.click(screen.getByRole('button', { name: /connect/i }))

    await waitFor(() => {
      expect(screen.getByText('Connecting...')).toBeInTheDocument()
    })
  })

  it('disables the connect button while loading', async () => {
    server.use(
      http.post('http://127.0.0.1:8000/api/v1/chat', async () => {
        await new Promise((r) => setTimeout(r, 500))
        return HttpResponse.json({ response: 'ok', sources: [], project_id: 'proj-1' })
      })
    )

    const user = userEvent.setup()
    renderWithProviders(<LoginView />)

    const button = screen.getByRole('button', { name: /connect/i })
    expect(button).not.toBeDisabled()

    await user.click(button)

    await waitFor(() => {
      expect(button).toBeDisabled()
    })
  })

  it('clears error when reconnecting', async () => {
    server.use(
      http.post('http://127.0.0.1:8000/api/v1/chat', () => HttpResponse.error())
    )

    const user = userEvent.setup()
    renderWithProviders(<LoginView />)

    // First attempt fails
    await user.click(screen.getByRole('button', { name: /connect/i }))

    await waitFor(() => {
      expect(screen.getByText(/failed to fetch/i)).toBeInTheDocument()
    })

    // Now make it succeed
    server.use(
      http.post('http://127.0.0.1:8000/api/v1/chat', () => {
        return HttpResponse.json({ response: 'ok', sources: [], project_id: 'proj-1' })
      })
    )

    await user.click(screen.getByRole('button', { name: /connect/i }))

    await waitFor(() => {
      expect(screen.queryByText(/failed to fetch/i)).not.toBeInTheDocument()
    })
  })

  it('stores auth token on successful connection', async () => {
    renderWithProviders(<LoginView />)
    await userEvent.click(screen.getByRole('button', { name: /connect/i }))

    await waitFor(() => {
      const state = useSettings.getState()
      expect(state.authToken).toBe('dev-token')
    })
  })

  it('stores custom API key when provided', async () => {
    const user = userEvent.setup()
    renderWithProviders(<LoginView />)

    const apiKeyInput = screen.getByPlaceholderText('Optional')
    await user.type(apiKeyInput, 'my-secret-key')

    await user.click(screen.getByRole('button', { name: /connect/i }))

    await waitFor(() => {
      const state = useSettings.getState()
      expect(state.authToken).toBe('my-secret-key')
    })
  })

  it('handles connection with URL that already has /api/v1 suffix', async () => {
    useSettings.setState({ apiUrl: 'http://127.0.0.1:8000/api/v1' })

    const user = userEvent.setup()
    renderWithProviders(<LoginView />)

    // The URL input should show the full URL with /api/v1
    const urlInput = screen.getByPlaceholderText('http://localhost:8000')
    expect(urlInput).toHaveValue('http://127.0.0.1:8000/api/v1')

    await user.click(screen.getByRole('button', { name: /connect/i }))

    await waitFor(() => {
      expect(screen.queryByText(/Server returned/i)).not.toBeInTheDocument()
    })
  })

  it('accepts 401 status as valid server response', async () => {
    server.use(
      http.post('http://127.0.0.1:8000/api/v1/chat', () => {
        return HttpResponse.json({ detail: 'Unauthorized' }, { status: 401 })
      })
    )

    renderWithProviders(<LoginView />)
    await userEvent.click(screen.getByRole('button', { name: /connect/i }))

    await waitFor(() => {
      const state = useSettings.getState()
      expect(state.authToken).toBe('dev-token')
    })
  })

  it('accepts 404 status as valid server response', async () => {
    server.use(
      http.post('http://127.0.0.1:8000/api/v1/chat', () => {
        return HttpResponse.json({ detail: 'Not found' }, { status: 404 })
      })
    )

    renderWithProviders(<LoginView />)
    await userEvent.click(screen.getByRole('button', { name: /connect/i }))

    await waitFor(() => {
      const state = useSettings.getState()
      expect(state.authToken).toBe('dev-token')
    })
  })

  it('accepts 422 status as valid server response', async () => {
    server.use(
      http.post('http://127.0.0.1:8000/api/v1/chat', () => {
        return HttpResponse.json({ detail: 'Validation error' }, { status: 422 })
      })
    )

    renderWithProviders(<LoginView />)
    await userEvent.click(screen.getByRole('button', { name: /connect/i }))

    await waitFor(() => {
      const state = useSettings.getState()
      expect(state.authToken).toBe('dev-token')
    })
  })
})
