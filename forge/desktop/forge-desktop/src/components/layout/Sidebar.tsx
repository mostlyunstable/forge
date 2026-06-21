import { type View } from '@/stores/navigation';
import { useNavigation } from '@/stores/navigation';
import { useCommandPalette } from '@/stores/command-palette';
import {
  LayoutDashboard,
  Code2,
  GitBranch,
  Bug,
  BarChart3,
  History,
  Network,
  Search,
  Settings,
  ChevronsLeft,
  ChevronsRight,
  Sparkles,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';

interface NavItem {
  id: View;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: number;
  section?: 'primary' | 'secondary';
}

const mainNav: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, section: 'primary' },
  { id: 'code', label: 'Code', icon: Code2, section: 'primary' },
  { id: 'decisions', label: 'Decisions', icon: GitBranch, badge: 7, section: 'primary' },
  { id: 'bugs', label: 'Bugs', icon: Bug, badge: 3, section: 'primary' },
  { id: 'analysis', label: 'Analysis', icon: BarChart3, section: 'secondary' },
  { id: 'history', label: 'History', icon: History, section: 'secondary' },
  { id: 'graph', label: 'Graph', icon: Network, section: 'secondary' },
];

const primaryNav = mainNav.filter((n) => n.section === 'primary');
const secondaryNav = mainNav.filter((n) => n.section === 'secondary');

export function Sidebar() {
  const { activeView, sidebarCollapsed, setView, toggleSidebar } = useNavigation();
  const commandPalette = useCommandPalette();

  const renderNavItem = (item: NavItem) => {
    const Icon = item.icon;
    const isActive = activeView === item.id;

    const button = (
      <button
        key={item.id}
        onClick={() => setView(item.id)}
        className={cn(
          'group flex w-full items-center gap-2.5 rounded-md px-2.5 py-1.5 text-[13px] font-medium transition-all duration-150',
          sidebarCollapsed && 'justify-center px-0',
          isActive
            ? 'bg-[var(--color-accent-muted)] text-[var(--color-accent)]'
            : 'text-[var(--color-text-muted)] hover:bg-[var(--color-surface-elevated)] hover:text-[var(--color-text-secondary)]'
        )}
      >
        <Icon className={cn(
          'h-4 w-4 shrink-0 transition-colors duration-150',
          isActive ? 'text-[var(--color-accent)]' : 'text-[var(--color-text-faint)] group-hover:text-[var(--color-text-muted)]'
        )} />
        {!sidebarCollapsed && (
          <>
            <span className="flex-1 text-left">{item.label}</span>
            {item.badge !== undefined && (
              <span className={cn(
                'rounded-full px-1.5 py-0.5 text-[10px] font-semibold tabular-nums',
                isActive
                  ? 'bg-[var(--color-accent)]/20 text-[var(--color-accent)]'
                  : 'bg-[var(--color-surface-elevated)] text-[var(--color-text-faint)]'
              )}>
                {item.badge}
              </span>
            )}
          </>
        )}
      </button>
    );

    if (sidebarCollapsed) {
      return (
        <Tooltip key={item.id}>
          <TooltipTrigger>{button}</TooltipTrigger>
          <TooltipContent side="right" sideOffset={8}>
            {item.label}
          </TooltipContent>
        </Tooltip>
      );
    }

    return button;
  };

  return (
    <aside
      className={cn(
        'flex h-full flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)] transition-all duration-200 ease-out',
        sidebarCollapsed ? 'w-[var(--sidebar-collapsed)]' : 'w-[var(--sidebar-width)]'
      )}
    >
      {/* Logo area */}
      <div className="flex h-[var(--titlebar-height)] items-center gap-2.5 border-b border-[var(--color-border-subtle)] px-3">
        <div className="flex h-6 w-6 items-center justify-center rounded-md bg-[var(--color-accent)]">
          <Sparkles className="h-3.5 w-3.5 text-white" />
        </div>
        {!sidebarCollapsed && (
          <span className="text-[14px] font-semibold tracking-tight text-[var(--color-text-primary)]">
            Forge
          </span>
        )}
      </div>

      {/* Search trigger */}
      <div className="px-2 pt-2.5 pb-1">
        <button
          onClick={commandPalette.open}
          className={cn(
            'flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-[12px] transition-all duration-150',
            sidebarCollapsed && 'justify-center px-0',
            'text-[var(--color-text-faint)] hover:bg-[var(--color-surface-elevated)] hover:text-[var(--color-text-muted)]'
          )}
        >
          <Search className="h-3.5 w-3.5 shrink-0" />
          {!sidebarCollapsed && (
            <>
              <span className="flex-1 text-left">Search</span>
              <kbd className="pointer-events-none rounded border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-1.5 py-0.5 font-mono text-[10px] text-[var(--color-text-faint)]">
                ⌘K
              </kbd>
            </>
          )}
        </button>
      </div>

      {/* Primary nav */}
      <nav className="flex-1 overflow-y-auto px-2 pt-1">
        <div className="space-y-0.5">
          {primaryNav.map(renderNavItem)}
        </div>

        {/* Secondary nav section */}
        {secondaryNav.length > 0 && (
          <div className="mt-4">
            {!sidebarCollapsed && (
              <div className="mb-1 px-2.5 text-[10px] font-medium uppercase tracking-wider text-[var(--color-text-faint)]">
                Tools
              </div>
            )}
            <div className="space-y-0.5">
              {secondaryNav.map(renderNavItem)}
            </div>
          </div>
        )}
      </nav>

      {/* Bottom section */}
      <div className="border-t border-[var(--color-border-subtle)]">
        <div className="space-y-0.5 px-2 py-2">
          <button
            onClick={toggleSidebar}
            className={cn(
              'flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-[12px] transition-all duration-150',
              sidebarCollapsed && 'justify-center px-0',
              'text-[var(--color-text-faint)] hover:bg-[var(--color-surface-elevated)] hover:text-[var(--color-text-muted)]'
            )}
          >
            {sidebarCollapsed ? (
              <ChevronsRight className="h-4 w-4" />
            ) : (
              <>
                <ChevronsLeft className="h-4 w-4" />
                <span>Collapse</span>
              </>
            )}
          </button>

          <button
            className={cn(
              'flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-[12px] transition-all duration-150',
              sidebarCollapsed && 'justify-center px-0',
              'text-[var(--color-text-faint)] hover:bg-[var(--color-surface-elevated)] hover:text-[var(--color-text-muted)]'
            )}
          >
            <Settings className="h-4 w-4 shrink-0" />
            {!sidebarCollapsed && <span>Settings</span>}
          </button>
        </div>

        {/* Status bar */}
        {!sidebarCollapsed && (
          <div className="border-t border-[var(--color-border-subtle)] px-3 py-2">
            <div className="flex items-center gap-2 text-[11px] text-[var(--color-text-faint)]">
              <span className="h-1.5 w-1.5 rounded-full bg-[var(--color-success)]" />
              <span>Connected</span>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
