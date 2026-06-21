import { TooltipProvider } from '@/components/ui/tooltip';
import { QueryProvider } from '@/components/QueryProvider';
import { AppLayout } from '@/components/layout/AppLayout';
import { DashboardView } from '@/components/views/DashboardView';
import { CodeView } from '@/components/views/CodeView';
import { DecisionsView } from '@/components/views/DecisionsView';
import { BugsView } from '@/components/views/BugsView';
import { AnalysisView } from '@/components/views/AnalysisView';
import { HistoryView } from '@/components/views/HistoryView';
import { GraphView } from '@/components/views/GraphView';
import { useNavigation } from '@/stores/navigation';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';

function ViewRouter() {
  const activeView = useNavigation((s) => s.activeView);

  switch (activeView) {
    case 'dashboard':
      return <DashboardView />;
    case 'code':
      return <CodeView />;
    case 'decisions':
      return <DecisionsView />;
    case 'bugs':
      return <BugsView />;
    case 'analysis':
      return <AnalysisView />;
    case 'history':
      return <HistoryView />;
    case 'graph':
      return <GraphView />;
    default:
      return <DashboardView />;
  }
}

function App() {
  useKeyboardShortcuts();

  return (
    <QueryProvider>
      <TooltipProvider>
        <AppLayout>
          <ViewRouter />
        </AppLayout>
      </TooltipProvider>
    </QueryProvider>
  );
}

export default App;
