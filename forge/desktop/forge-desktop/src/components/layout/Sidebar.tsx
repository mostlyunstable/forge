import { type View, useNavigation } from '@/stores/navigation';
import { useCommandPalette } from '@/stores/command-palette';
import { useDecisions, useBugs } from '@/hooks/useApi';
import { useSettings } from '@/stores/settings';
import { SettingsDialog } from '@/components/SettingsDialog';
import { useState, useEffect } from 'react';
import { checkServerConnection } from '@/lib/api';
import {
  LayoutDashboard,
  Code2,
  GitBranch,
  Bug,
  BarChart3,
  History,
  Network,
  Settings,
  ChevronsLeft,
  ChevronsRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';

interface NavItem {
  id: View;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  count?: number;
  group?: number;
}

export function Sidebar() {
  const { activeView, sidebarCollapsed, setView, toggleSidebar } = useNavigation();
  const commandPalette = useCommandPalette();
  const { currentProjectId, connectionStatus, setConnectionStatus, apiUrl } = useSettings();
  const decisionsQuery = useDecisions(currentProjectId);
  const bugsQuery = useBugs(currentProjectId);
  const [settingsOpen, setSettingsOpen] = useState(false);

  // Check connection on mount and when apiUrl changes
  useEffect(() => {
    let cancelled = false;
    const check = async () => {
      setConnectionStatus('checking');
      const connected = await checkServerConnection(apiUrl);
      if (!cancelled) {
        setConnectionStatus(connected ? 'connected' : 'disconnected');
      }
    };
    check();
    return () => { cancelled = true; };
  }, [apiUrl]);

  const decisionsCount = decisionsQuery.data?.total ?? 0;
  const openBugsCount = bugsQuery.data?.bugs?.filter((b) => !b.resolved).length ?? 0;

  const navItems: NavItem[] = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, group: 0 },
    { id: 'code', label: 'Code', icon: Code2, group: 0 },
    { id: 'decisions', label: 'Decisions', icon: GitBranch, count: decisionsCount, group: 0 },
    { id: 'bugs', label: 'Bugs', icon: Bug, count: openBugsCount, group: 0 },
    { id: 'analysis', label: 'Analysis', icon: BarChart3, group: 1 },
    { id: 'history', label: 'History', icon: History, group: 1 },
    { id: 'graph', label: 'Graph', icon: Network, group: 1 },
  ];

  const group0 = navItems.filter((n) => n.group === 0);
  const group1 = navItems.filter((n) => n.group === 1);

  const renderNavItem = (item: NavItem) => {
    const Icon = item.icon;
    const isActive = activeView === item.id;

    const button = (
      <button
        key={item.id}
        onClick={() => setView(item.id)}
        className={cn(
          'group flex w-full items-center gap-3 rounded-[4px] px-3 text-[13px] font-medium transition-colors duration-120',
          sidebarCollapsed ? 'justify-center h-[32px] px-0' : 'h-[32px]',
          isActive
            ? 'bg-[var(--color-bg-elevated)] text-[var(--color-text-primary)] border-l-2 border-l-[var(--color-accent-blue)] pl-[10px]'
            : 'text-[var(--color-text-muted)] hover:bg-[var(--color-bg-elevated)] hover:text-[var(--color-text-secondary)] border-l-2 border-l-transparent'
        )}
      >
        <Icon className={cn(
          'h-[14px] w-[14px] shrink-0',
          isActive ? 'text-[var(--color-accent-blue)]' : 'text-[var(--color-text-muted)]'
        )} />
        {!sidebarCollapsed && (
          <>
            <span className="flex-1 text-left">{item.label}</span>
            {item.count !== undefined && item.count > 0 && (
              <span className="font-mono text-[10px] text-[var(--color-text-muted)] tabular-nums">
                {item.count}
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
    <>
    <aside
      data-tauri-drag-region="false"
      className={cn(
        'flex h-full flex-col border-r border-[var(--color-border-subtle)] bg-[var(--color-bg-surface)]',
        sidebarCollapsed ? 'w-[var(--sidebar-collapsed)]' : 'w-[var(--sidebar-width)]'
      )}
    >
      {/* Logo */}
      <div className="flex h-[var(--titlebar-height)] items-center gap-2 border-b border-[var(--color-border-subtle)] px-3">
        <div className="flex h-[20px] w-[20px] items-center justify-center rounded-[4px] bg-[var(--color-accent-blue)]">
          <span className="text-[10px] font-bold text-white">F</span>
        </div>
        {!sidebarCollapsed && (
          <span className="text-[14px] font-semibold tracking-tight text-[var(--color-text-primary)]">
            Forge
          </span>
        )}
      </div>

      {/* Search trigger */}
      <div className="px-2 pt-[8px] pb-[4px]">
        <button
          onClick={commandPalette.open}
          className={cn(
            'flex w-full items-center gap-2 rounded-[4px] px-3 h-[28px] text-[12px] transition-colors duration-120',
            sidebarCollapsed && 'justify-center px-0',
            'text-[var(--color-text-muted)] hover:bg-[var(--color-bg-elevated)] hover:text-[var(--color-text-secondary)]'
          )}
        >
          {!sidebarCollapsed ? (
            <>
              <span className="flex-1 text-left">Search</span>
              <kbd className="font-mono text-[10px] text-[var(--color-text-muted)] border border-[var(--color-border-subtle)] rounded-[2px] px-1 py-0.5">
                ⌘K
              </kbd>
            </>
          ) : (
            <span className="text-[12px]">⌘K</span>
          )}
        </button>
      </div>

      {/* Nav groups */}
      <nav className="flex-1 overflow-y-auto px-2 pt-[4px]">
        <div className="space-y-[2px]">
          {group0.map(renderNavItem)}
        </div>

        <div className="mt-[8px] space-y-[2px]">
          {group1.map(renderNavItem)}
        </div>
      </nav>

      {/* Bottom section */}
      <div className="mt-auto">
        {/* Connection status */}
        {!sidebarCollapsed && (
          <div className="px-2 pb-[4px]">
            <div className="flex items-center gap-2 rounded-[4px] px-3 h-[28px] text-[11px] text-[var(--color-text-muted)]">
              <span className={`h-[6px] w-[6px] rounded-full shrink-0 ${
                connectionStatus === 'connected' ? 'bg-[var(--color-accent-green)]' :
                connectionStatus === 'disconnected' ? 'bg-[var(--color-accent-red)]' :
                'bg-[var(--color-accent-amber)]'
              }`} />
              <span>{connectionStatus === 'connected' ? 'Connected' : connectionStatus === 'disconnected' ? 'Offline' : 'Checking...'}</span>
            </div>
          </div>
        )}
        {/* Settings */}
        <div className="px-2 pb-[4px]">
          <button
            onClick={() => setSettingsOpen(true)}
            className={cn(
              'flex w-full items-center gap-3 rounded-[4px] px-3 h-[32px] text-[13px] transition-colors duration-120',
              sidebarCollapsed && 'justify-center px-0',
              'text-[var(--color-text-muted)] hover:bg-[var(--color-bg-elevated)] hover:text-[var(--color-text-secondary)]'
            )}
          >
            <Settings className="h-[14px] w-[14px] shrink-0" />
            {!sidebarCollapsed && <span>Settings</span>}
          </button>
        </div>

        {/* Collapse */}
        <div className="border-t border-[var(--color-border-subtle)] px-2 py-[4px]">
          <button
            onClick={toggleSidebar}
            className={cn(
              'flex w-full items-center gap-3 rounded-[4px] px-3 h-[32px] text-[13px] transition-colors duration-120',
              sidebarCollapsed && 'justify-center px-0',
              'text-[var(--color-text-muted)] hover:bg-[var(--color-bg-elevated)] hover:text-[var(--color-text-secondary)]'
            )}
          >
            {sidebarCollapsed ? (
              <ChevronsRight className="h-[14px] w-[14px]" />
            ) : (
              <>
                <ChevronsLeft className="h-[14px] w-[14px]" />
                <span>Collapse</span>
              </>
            )}
          </button>
        </div>
      </div>
    </aside>

    <SettingsDialog open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </>
  );
}