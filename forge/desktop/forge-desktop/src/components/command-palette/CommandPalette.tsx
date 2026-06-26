import { useEffect, useCallback } from 'react';
import { useCommandPalette } from '@/stores/command-palette';
import { useNavigation, type View } from '@/stores/navigation';
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command';
import {
  LayoutDashboard,
  Code2,
  GitBranch,
  Bug,
  BarChart3,
  History,
  Network,
  Play,
  FileText,
  Settings,
  FolderOpen,
} from 'lucide-react';

const views: { id: View; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'code', label: 'Code', icon: Code2 },
  { id: 'decisions', label: 'Decisions', icon: GitBranch },
  { id: 'bugs', label: 'Bugs', icon: Bug },
  { id: 'analysis', label: 'Analysis', icon: BarChart3 },
  { id: 'history', label: 'History', icon: History },
  { id: 'graph', label: 'Graph', icon: Network },
];

const commands = [
  { id: 'index', label: 'Index Codebase', icon: Play, view: 'code' as View },
  { id: 'new-decision', label: 'New Decision', icon: GitBranch, view: 'decisions' as View },
  { id: 'new-bug', label: 'New Bug Report', icon: Bug, view: 'bugs' as View },
  { id: 'analyze-pr', label: 'Analyze PR', icon: BarChart3, view: 'analysis' as View },
  { id: 'open-project', label: 'Open Project', icon: FolderOpen, view: 'settings' as View },
  { id: 'export', label: 'Export Report', icon: FileText, view: null },
  { id: 'settings', label: 'Open Settings', icon: Settings, view: 'settings' as View },
];

export function CommandPalette() {
  const { isOpen, close, recentCommands, addRecentCommand } = useCommandPalette();
  const { setView, setPendingAction } = useNavigation();

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        useCommandPalette.getState().toggle();
      }
    };
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, []);

  const handleSelect = useCallback(
    (value: string) => {
      // Check if it's a view
      const view = views.find((v) => v.id === value);
      if (view) {
        setView(view.id);
        addRecentCommand(`Go to ${view.label}`);
        close();
        return;
      }

      // Check if it's a command
      const cmd = commands.find((c) => c.id === value);
      if (cmd) {
        // Handle settings specially — don't navigate, emit action
        if (cmd.id === 'settings' || cmd.id === 'open-project') {
          // Dispatch a custom event that App listens for
          window.dispatchEvent(new CustomEvent('forge:open-settings'));
          addRecentCommand(cmd.label);
          close();
          return;
        }

        // Navigate to the view and set pending action
        if (cmd.view) {
          setView(cmd.view);
        }

        // Set pending action for create commands
        if (cmd.id === 'new-decision') {
          setPendingAction('create-decision');
        } else if (cmd.id === 'new-bug') {
          setPendingAction('create-bug');
        } else if (cmd.id === 'index') {
          setPendingAction('index-codebase');
        }

        addRecentCommand(cmd.label);
        close();
      }
    },
    [setView, setPendingAction, addRecentCommand, close]
  );

  return (
    <CommandDialog open={isOpen} onOpenChange={(open) => !open && close()}>
      <CommandInput placeholder="Search commands..." className="text-[13px]" />
      <CommandList>
        <CommandEmpty className="py-6 text-[12px] text-[var(--color-text-muted)]">
          No results found.
        </CommandEmpty>

        {recentCommands.length > 0 && (
          <CommandGroup heading="Recent" className="px-2 py-1">
            {recentCommands.map((cmd) => (
              <CommandItem
                key={cmd}
                value={cmd}
                onSelect={handleSelect}
                className="rounded-[4px] px-2 py-1.5 text-[12px] data-[selected]:bg-[var(--color-bg-elevated)] data-[selected]:text-[var(--color-text-primary)]"
              >
                <span className="text-[var(--color-text-secondary)]">{cmd}</span>
              </CommandItem>
            ))}
          </CommandGroup>
        )}

        <CommandGroup heading="Commands" className="px-2 py-1">
          {commands.map((cmd) => {
            const Icon = cmd.icon;
            return (
              <CommandItem
                key={cmd.id}
                value={cmd.id}
                onSelect={handleSelect}
                className="rounded-[4px] px-2 py-1.5 text-[12px] data-[selected]:bg-[var(--color-bg-elevated)] data-[selected]:text-[var(--color-text-primary)]"
              >
                <Icon className="mr-2 h-[14px] w-[14px] text-[var(--color-text-muted)]" />
                <span>{cmd.label}</span>
              </CommandItem>
            );
          })}
        </CommandGroup>

        <CommandGroup heading="Navigation" className="px-2 py-1">
          {views.map((view) => {
            const Icon = view.icon;
            return (
              <CommandItem
                key={view.id}
                value={`go-to-${view.id}`}
                onSelect={handleSelect}
                className="rounded-[4px] px-2 py-1.5 text-[12px] data-[selected]:bg-[var(--color-bg-elevated)] data-[selected]:text-[var(--color-text-primary)]"
              >
                <Icon className="mr-2 h-[14px] w-[14px] text-[var(--color-text-muted)]" />
                <span>Go to {view.label}</span>
              </CommandItem>
            );
          })}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}