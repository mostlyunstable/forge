import { describe, it, expect, beforeEach } from 'vitest';
import { useSettingsDialog } from '@/stores/settings-dialog';

const initialState = {
  isOpen: false,
};

describe('useSettingsDialog', () => {
  beforeEach(() => {
    useSettingsDialog.setState(initialState);
  });

  it('has correct default state', () => {
    expect(useSettingsDialog.getState().isOpen).toBe(false);
  });

  it('open sets isOpen to true', () => {
    useSettingsDialog.getState().open();
    expect(useSettingsDialog.getState().isOpen).toBe(true);
  });

  it('open is idempotent', () => {
    useSettingsDialog.getState().open();
    useSettingsDialog.getState().open();
    expect(useSettingsDialog.getState().isOpen).toBe(true);
  });

  it('close sets isOpen to false', () => {
    useSettingsDialog.getState().open();
    expect(useSettingsDialog.getState().isOpen).toBe(true);
    useSettingsDialog.getState().close();
    expect(useSettingsDialog.getState().isOpen).toBe(false);
  });

  it('close is idempotent', () => {
    useSettingsDialog.getState().close();
    expect(useSettingsDialog.getState().isOpen).toBe(false);
  });

  it('toggle toggles isOpen', () => {
    expect(useSettingsDialog.getState().isOpen).toBe(false);
    useSettingsDialog.getState().toggle();
    expect(useSettingsDialog.getState().isOpen).toBe(true);
    useSettingsDialog.getState().toggle();
    expect(useSettingsDialog.getState().isOpen).toBe(false);
  });
});
