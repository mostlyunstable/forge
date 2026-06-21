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
  { id: 'index', label: 'Index Codebase', icon: Play },
  { id: 'new-decision', label: 'New Decision', icon: GitBranch },
  { id: 'new-bug', label: 'New Bug Report', icon: Bug },
  { id: 'analyze-pr', label: 'Analyze PR', icon: BarChart3 },
  { id: 'open-project', label: 'Open Project', icon: FolderOpen },
  { id: 'export', label: 'Export Report', icon: FileText },
  { id: 'settings', label: 'Open Settings', icon: Settings },
];

export function CommandPalette() {
  const { isOpen, close, recentCommands, addRecentCommand } = useCommandPalette();
  const { setView } = useNavigation();

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
      if (views.find((v) => v.id === value)) {
        setView(value as View);
        addRecentCommand(`Go to ${value}`);
      } else if (commands.find((c) => c.id === value)) {
        addRecentCommand(commands.find((c) => c.id === value)!.label);
      }
      close();
    },
    [setView, addRecentCommand, close]
  );

  return (
    <CommandDialog open={isOpen} onOpenChange={(open) => !open && close()}>
      <CommandInput placeholder="Search commands..." className="text-[13px]" />
      <CommandList>
        <CommandEmpty className="py-6 text-[12px] text-[var(--color-text-faint)]">
          No results found.
        </CommandEmpty>

        {recentCommands.length > 0 && (
          <CommandGroup heading="Recent" className="px-2 py-1">
            {recentCommands.map((cmd) => (
              <CommandItem
                key={cmd}
                value={cmd}
                onSelect={handleSelect}
                className="rounded-md px-2 py-1.5 text-[12px] data-[selected]:bg-[var(--color-accent-muted)] data-[selected]:text-[var(--color-accent)]"
              >
                <span className="text-[var(--color-text-muted)]">{cmd}</span>
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
                className="rounded-md px-2 py-1.5 text-[12px] data-[selected]:bg-[var(--color-accent-muted)] data-[selected]:text-[var(--color-accent)]"
              >
                <Icon className="mr-2 h-3.5 w-3.5 text-[var(--color-text-faint)]" />
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
                className="rounded-md px-2 py-1.5 text-[12px] data-[selected]:bg-[var(--color-accent-muted)] data-[selected]:text-[var(--color-accent)]"
              >
                <Icon className="mr-2 h-3.5 w-3.5 text-[var(--color-text-faint)]" />
                <span>Go to {view.label}</span>
              </CommandItem>
            );
          })}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
