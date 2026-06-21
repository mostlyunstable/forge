import { Sidebar } from './Sidebar';
import { TitleBar } from './TitleBar';
import { CommandPalette } from '@/components/command-palette/CommandPalette';

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="flex h-screen w-screen flex-col overflow-hidden">
      <TitleBar />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-hidden">
          {children}
        </main>
      </div>
      <CommandPalette />
    </div>
  );
}
