import { Component, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex h-full w-full flex-col items-center justify-center bg-[var(--color-bg-base)] p-8">
          <div className="max-w-md text-center">
            <div className="mb-4 font-mono text-[14px] text-[var(--color-accent-red)]">
              ERROR
            </div>
            <div className="mb-2 text-[14px] text-[var(--color-text-primary)]">
              Something went wrong
            </div>
            <div className="mb-6 font-mono text-[12px] text-[var(--color-text-muted)] leading-relaxed">
              {this.state.error?.message ?? 'Unknown error'}
            </div>
            <button
              onClick={() => window.location.reload()}
              className="btn btn-primary"
            >
              Reload App
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}