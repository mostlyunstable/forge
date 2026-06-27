import { lazy, Suspense } from 'react';
import { Toaster } from 'react-hot-toast';
import { TooltipProvider } from '@/components/ui/tooltip';
import { QueryProvider } from '@/components/QueryProvider';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { AppLayout } from '@/components/layout/AppLayout';
import { DashboardView } from '@/components/views/DashboardView';
import { CodeView } from '@/components/views/CodeView';
import { DecisionsView } from '@/components/views/DecisionsView';
import { BugsView } from '@/components/views/BugsView';
import { HistoryView } from '@/components/views/HistoryView';
import { LoginView } from '@/components/views/LoginView';
import { useNavigation } from '@/stores/navigation';
import { useSettings } from '@/stores/settings';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';

const AnalysisView = lazy(() => import('@/components/views/AnalysisView').then(m => ({ default: m.AnalysisView })));
const GraphView = lazy(() => import('@/components/views/GraphView').then(m => ({ default: m.GraphView })));

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
      return <Suspense fallback={<div className="p-6 text-[var(--color-text-muted)]">Loading...</div>}><AnalysisView /></Suspense>;
    case 'history':
      return <HistoryView />;
    case 'graph':
      return <Suspense fallback={<div className="p-6 text-[var(--color-text-muted)]">Loading...</div>}><GraphView /></Suspense>;
    default:
      return <DashboardView />;
  }
}

function App() {
  useKeyboardShortcuts();
  const authToken = useSettings((s) => s.authToken);

  if (!authToken) {
    return (
      <ErrorBoundary>
        <QueryProvider>
          <LoginView />
        </QueryProvider>
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary>
      <QueryProvider>
        <TooltipProvider>
          <Toaster
            position="bottom-right"
            containerStyle={{ bottom: 16, right: 16 }}
            toastOptions={{
              style: {
                background: 'var(--color-bg-overlay)',
                color: 'var(--color-text-primary)',
                border: '1px solid var(--color-border-default)',
                borderRadius: '4px',
                fontSize: '13px',
                fontFamily: 'var(--font-sans)',
              },
            }}
          />
          <AppLayout>
            <ViewRouter />
          </AppLayout>
        </TooltipProvider>
      </QueryProvider>
    </ErrorBoundary>
  );
}

export default App;