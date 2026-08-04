import { describe, it, expect, beforeAll, afterEach, afterAll, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { setupServer } from 'msw/node'

import { handlers } from '@/test/handlers'
import { renderWithProviders } from '@/test/test-utils'
import { useSettings } from '@/stores/settings'
import { CodeView } from '../CodeView'

const server = setupServer(...handlers)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

beforeEach(() => {
  useSettings.setState({ currentProjectId: 'proj-1', apiUrl: 'http://127.0.0.1:8000' })
})

describe('CodeView', () => {
  it('shows file tree sidebar', async () => {
    renderWithProviders(<CodeView />)
    expect(screen.getByText('Files')).toBeInTheDocument()
    // File tree has hardcoded entries
    expect(screen.getByText('forge')).toBeInTheDocument()
  })

  it('shows search input', () => {
    renderWithProviders(<CodeView />)
    expect(screen.getByPlaceholderText('Search files...')).toBeInTheDocument()
  })

  it('shows empty code viewer state when no file selected', () => {
    renderWithProviders(<CodeView />)
    expect(screen.getByText('Select a file to view')).toBeInTheDocument()
  })

  it('shows file tree items', async () => {
    renderWithProviders(<CodeView />)
    // Top-level directory
    expect(screen.getByText('forge')).toBeInTheDocument()
    // Subdirectories should be visible when expanded
    expect(screen.getByText('domain')).toBeInTheDocument()
    expect(screen.getByText('application')).toBeInTheDocument()
    expect(screen.getByText('infrastructure')).toBeInTheDocument()
    expect(screen.getByText('presentation')).toBeInTheDocument()
  })

  it('clicking a file selects it', async () => {
    const user = userEvent.setup()
    renderWithProviders(<CodeView />)

    // Expand domain directory (level 1, collapsed by default)
    await user.click(screen.getByText('domain'))
    // Now click on a file
    await user.click(screen.getByText('project.py'))

    await waitFor(() => {
      expect(screen.getByText('forge/domain/project.py')).toBeInTheDocument()
    })
  })

  it('shows code viewer after file selection', async () => {
    const user = userEvent.setup()
    renderWithProviders(<CodeView />)

    await user.click(screen.getByText('domain'))
    await user.click(screen.getByText('project.py'))

    await waitFor(() => {
      expect(screen.getByText('forge/domain/project.py')).toBeInTheDocument()
      expect(screen.getByText('File Summary')).toBeInTheDocument()
    })
  })
})
