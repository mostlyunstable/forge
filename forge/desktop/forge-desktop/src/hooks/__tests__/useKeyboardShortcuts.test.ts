import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useKeyboardShortcuts } from '../useKeyboardShortcuts';
import { useNavigation } from '@/stores/navigation';
import { useCommandPalette } from '@/stores/command-palette';

function pressKey(key: string, metaKey = true) {
  const event = new KeyboardEvent('keydown', { key, metaKey, bubbles: true });
  document.dispatchEvent(event);
}

describe('useKeyboardShortcuts', () => {
  beforeEach(() => {
    useNavigation.setState({
      activeView: 'dashboard',
      sidebarCollapsed: false,
    });
    useCommandPalette.setState({ isOpen: false });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('Cmd+1 switches to dashboard view', () => {
    renderHook(() => useKeyboardShortcuts());

    act(() => pressKey('1'));

    expect(useNavigation.getState().activeView).toBe('dashboard');
  });

  it('Cmd+2 switches to code view', () => {
    renderHook(() => useKeyboardShortcuts());

    act(() => pressKey('2'));

    expect(useNavigation.getState().activeView).toBe('code');
  });

  it('Cmd+3 switches to decisions view', () => {
    renderHook(() => useKeyboardShortcuts());

    act(() => pressKey('3'));

    expect(useNavigation.getState().activeView).toBe('decisions');
  });

  it('Cmd+4 switches to bugs view', () => {
    renderHook(() => useKeyboardShortcuts());

    act(() => pressKey('4'));

    expect(useNavigation.getState().activeView).toBe('bugs');
  });

  it('Cmd+5 switches to analysis view', () => {
    renderHook(() => useKeyboardShortcuts());

    act(() => pressKey('5'));

    expect(useNavigation.getState().activeView).toBe('analysis');
  });

  it('Cmd+6 switches to history view', () => {
    renderHook(() => useKeyboardShortcuts());

    act(() => pressKey('6'));

    expect(useNavigation.getState().activeView).toBe('history');
  });

  it('Cmd+7 switches to graph view', () => {
    renderHook(() => useKeyboardShortcuts());

    act(() => pressKey('7'));

    expect(useNavigation.getState().activeView).toBe('graph');
  });

  it('Cmd+\\ toggles sidebar', () => {
    renderHook(() => useKeyboardShortcuts());

    expect(useNavigation.getState().sidebarCollapsed).toBe(false);

    act(() => pressKey('\\'));
    expect(useNavigation.getState().sidebarCollapsed).toBe(true);

    act(() => pressKey('\\'));
    expect(useNavigation.getState().sidebarCollapsed).toBe(false);
  });

  it('Cmd+/ toggles command palette', () => {
    renderHook(() => useKeyboardShortcuts());

    expect(useCommandPalette.getState().isOpen).toBe(false);

    act(() => pressKey('/'));
    expect(useCommandPalette.getState().isOpen).toBe(true);

    act(() => pressKey('/'));
    expect(useCommandPalette.getState().isOpen).toBe(false);
  });

  it('does not trigger without meta key', () => {
    renderHook(() => useKeyboardShortcuts());

    act(() => {
      const event = new KeyboardEvent('keydown', { key: '2', metaKey: false, bubbles: true });
      document.dispatchEvent(event);
    });

    expect(useNavigation.getState().activeView).toBe('dashboard');
  });
});
