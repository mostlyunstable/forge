import { useEffect } from 'react';
import { useNavigation, type View } from '@/stores/navigation';
import { useCommandPalette } from '@/stores/command-palette';

const viewShortcuts: Record<string, View> = {
  '1': 'dashboard',
  '2': 'code',
  '3': 'decisions',
  '4': 'bugs',
  '5': 'analysis',
  '6': 'history',
  '7': 'graph',
};

export function useKeyboardShortcuts() {
  const setView = useNavigation((s) => s.setView);
  const toggleSidebar = useNavigation((s) => s.toggleSidebar);
  const toggleCommandPalette = useCommandPalette((s) => s.toggle);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const isMeta = e.metaKey || e.ctrlKey;

      // Cmd+K: Command palette (handled in CommandPalette component)
      // Cmd+/: Quick search
      if (isMeta && e.key === '/') {
        e.preventDefault();
        toggleCommandPalette();
        return;
      }

      // Cmd+\: Toggle sidebar
      if (isMeta && e.key === '\\') {
        e.preventDefault();
        toggleSidebar();
        return;
      }

      // Cmd+1-7: Switch views
      if (isMeta && viewShortcuts[e.key]) {
        e.preventDefault();
        setView(viewShortcuts[e.key]);
        return;
      }
    };

    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [setView, toggleSidebar, toggleCommandPalette]);
}
