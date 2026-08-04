/* eslint-disable @typescript-eslint/no-explicit-any */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '@/test/test-utils'
import { useCommandPalette } from '@/stores/command-palette'
import { useNavigation } from '@/stores/navigation'
import { CommandPalette } from '../CommandPalette'

vi.mock('@/components/ui/command', () => ({
  CommandDialog: ({ children, open, onOpenChange }: any) => {
    if (!open) return null
    return (
      <div data-testid="command-dialog">
        <div data-testid="command-dialog-overlay" onClick={() => onOpenChange?.(false)} />
        {children}
      </div>
    )
  },
  CommandInput: (props: any) => <input data-testid="command-input" placeholder={props.placeholder} />,
  CommandList: ({ children }: any) => <div data-testid="command-list">{children}</div>,
  CommandEmpty: ({ children }: any) => <div data-testid="command-empty">{children}</div>,
  CommandGroup: ({ heading, children }: any) => (
    <div data-testid={`command-group-${heading}`}>
      <div data-testid="command-group-heading">{heading}</div>
      {children}
    </div>
  ),
  CommandItem: ({ value, onSelect, children }: any) => (
    <button data-testid={`cmd-${value}`} onClick={() => onSelect?.(value)}>
      {children}
    </button>
  ),
}))

beforeEach(() => {
  useCommandPalette.setState({
    isOpen: false,
    query: '',
    recentCommands: [],
  })
  useNavigation.setState({
    activeView: 'dashboard',
    pendingAction: null,
  })
})

describe('CommandPalette', () => {
  it('does not render when closed', () => {
    renderWithProviders(<CommandPalette />)
    expect(screen.queryByTestId('command-dialog')).not.toBeInTheDocument()
  })

  it('renders when open', () => {
    useCommandPalette.setState({ isOpen: true })
    renderWithProviders(<CommandPalette />)
    expect(screen.getByTestId('command-dialog')).toBeInTheDocument()
  })

  it('shows search input', () => {
    useCommandPalette.setState({ isOpen: true })
    renderWithProviders(<CommandPalette />)
    expect(screen.getByTestId('command-input')).toBeInTheDocument()
  })

  it('shows Commands group', () => {
    useCommandPalette.setState({ isOpen: true })
    renderWithProviders(<CommandPalette />)
    expect(screen.getByTestId('command-group-Commands')).toBeInTheDocument()
    expect(screen.getByText('Index Codebase')).toBeInTheDocument()
    expect(screen.getByText('New Decision')).toBeInTheDocument()
  })

  it('shows Navigation group', () => {
    useCommandPalette.setState({ isOpen: true })
    renderWithProviders(<CommandPalette />)
    expect(screen.getByTestId('command-group-Navigation')).toBeInTheDocument()
    expect(screen.getByText('Go to Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Go to Code')).toBeInTheDocument()
  })

  it('selecting a command navigates and sets pending action', async () => {
    const user = userEvent.setup()
    useCommandPalette.setState({ isOpen: true })
    renderWithProviders(<CommandPalette />)

    // "new-decision" command sets view to 'decisions' and pendingAction to 'create-decision'
    await user.click(screen.getByTestId('cmd-new-decision'))

    await waitFor(() => {
      expect(useNavigation.getState().activeView).toBe('decisions')
      expect(useNavigation.getState().pendingAction).toBe('create-decision')
    })
  })

  it('selecting "index" command navigates to code and sets pending action', async () => {
    const user = userEvent.setup()
    useCommandPalette.setState({ isOpen: true })
    renderWithProviders(<CommandPalette />)

    await user.click(screen.getByTestId('cmd-index'))

    await waitFor(() => {
      expect(useNavigation.getState().activeView).toBe('code')
      expect(useNavigation.getState().pendingAction).toBe('index-codebase')
    })
  })

  it('selecting "New Bug Report" sets pending action', async () => {
    const user = userEvent.setup()
    useCommandPalette.setState({ isOpen: true })
    renderWithProviders(<CommandPalette />)

    await user.click(screen.getByTestId('cmd-new-bug'))

    await waitFor(() => {
      expect(useNavigation.getState().pendingAction).toBe('create-bug')
    })
  })

  it('selecting "Open Settings" dispatches forge:open-settings event', async () => {
    const user = userEvent.setup()
    useCommandPalette.setState({ isOpen: true })

    const eventSpy = vi.fn()
    window.addEventListener('forge:open-settings', eventSpy)

    renderWithProviders(<CommandPalette />)
    await user.click(screen.getByTestId('cmd-settings'))

    await waitFor(() => {
      expect(eventSpy).toHaveBeenCalled()
    })

    window.removeEventListener('forge:open-settings', eventSpy)
  })

  it('Cmd+K keyboard shortcut toggles palette', async () => {
    renderWithProviders(<CommandPalette />)

    expect(useCommandPalette.getState().isOpen).toBe(false)

    await userEvent.setup().keyboard('{Meta>}k')

    await waitFor(() => {
      expect(useCommandPalette.getState().isOpen).toBe(true)
    })
  })

  it('shows recent commands section when there are recent commands', () => {
    useCommandPalette.setState({
      isOpen: true,
      recentCommands: ['Go to Dashboard'],
    })
    renderWithProviders(<CommandPalette />)
    expect(screen.getByTestId('command-group-Recent')).toBeInTheDocument()
    expect(screen.getByTestId('cmd-Go to Dashboard')).toBeInTheDocument()
  })

  it('closes after selecting a command', async () => {
    const user = userEvent.setup()
    useCommandPalette.setState({ isOpen: true })
    renderWithProviders(<CommandPalette />)

    await user.click(screen.getByTestId('cmd-new-decision'))

    await waitFor(() => {
      expect(useCommandPalette.getState().isOpen).toBe(false)
    })
  })
})
