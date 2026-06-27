import { describe, it, expect, beforeEach } from 'vitest';
import { useCommandPalette } from '@/stores/command-palette';

const initialState = {
  isOpen: false,
  query: '',
  recentCommands: [],
};

describe('useCommandPalette', () => {
  beforeEach(() => {
    useCommandPalette.setState(initialState);
  });

  it('has correct default state', () => {
    const state = useCommandPalette.getState();
    expect(state.isOpen).toBe(false);
    expect(state.query).toBe('');
    expect(state.recentCommands).toEqual([]);
  });

  it('toggle toggles isOpen', () => {
    expect(useCommandPalette.getState().isOpen).toBe(false);
    useCommandPalette.getState().toggle();
    expect(useCommandPalette.getState().isOpen).toBe(true);
    useCommandPalette.getState().toggle();
    expect(useCommandPalette.getState().isOpen).toBe(false);
  });

  it('open sets isOpen to true', () => {
    useCommandPalette.getState().open();
    expect(useCommandPalette.getState().isOpen).toBe(true);
  });

  it('open is idempotent', () => {
    useCommandPalette.getState().open();
    useCommandPalette.getState().open();
    expect(useCommandPalette.getState().isOpen).toBe(true);
  });

  it('close sets isOpen to false and clears query', () => {
    useCommandPalette.getState().open();
    useCommandPalette.getState().setQuery('test query');
    expect(useCommandPalette.getState().isOpen).toBe(true);
    expect(useCommandPalette.getState().query).toBe('test query');

    useCommandPalette.getState().close();
    expect(useCommandPalette.getState().isOpen).toBe(false);
    expect(useCommandPalette.getState().query).toBe('');
  });

  it('setQuery updates query', () => {
    useCommandPalette.getState().setQuery('find component');
    expect(useCommandPalette.getState().query).toBe('find component');
  });

  it('addRecentCommand adds to front of list', () => {
    useCommandPalette.getState().addRecentCommand('command-1');
    expect(useCommandPalette.getState().recentCommands).toEqual(['command-1']);
  });

  it('addRecentCommand adds new commands to front', () => {
    useCommandPalette.getState().addRecentCommand('command-1');
    useCommandPalette.getState().addRecentCommand('command-2');
    expect(useCommandPalette.getState().recentCommands).toEqual(['command-2', 'command-1']);
  });

  it('addRecentCommand deduplicates existing commands', () => {
    useCommandPalette.getState().addRecentCommand('command-1');
    useCommandPalette.getState().addRecentCommand('command-2');
    useCommandPalette.getState().addRecentCommand('command-1');
    expect(useCommandPalette.getState().recentCommands).toEqual(['command-1', 'command-2']);
  });

  it('addRecentCommand limits to 5 items', () => {
    const commands = ['cmd-1', 'cmd-2', 'cmd-3', 'cmd-4', 'cmd-5', 'cmd-6'];
    for (const cmd of commands) {
      useCommandPalette.getState().addRecentCommand(cmd);
    }
    const recent = useCommandPalette.getState().recentCommands;
    expect(recent.length).toBe(5);
    expect(recent).toEqual(['cmd-6', 'cmd-5', 'cmd-4', 'cmd-3', 'cmd-2']);
  });

  it('close clears query even when palette is already closed', () => {
    useCommandPalette.getState().setQuery('some query');
    useCommandPalette.getState().close();
    expect(useCommandPalette.getState().query).toBe('');
    expect(useCommandPalette.getState().isOpen).toBe(false);
  });
});
