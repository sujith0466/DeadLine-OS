import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { ShieldAlert, RefreshCcw } from 'lucide-react';

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error in component:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center h-screen bg-background text-white p-6">
          <ShieldAlert className="w-16 h-16 text-rose-500 mb-4" />
          <h1 className="text-3xl font-bold mb-2">Something went wrong</h1>
          <p className="text-gray-400 mb-6 max-w-lg text-center">
            A critical error occurred while rendering this page. The rest of DeadlineOS is still running.
          </p>
          <div className="bg-rose-500/10 border border-rose-500/30 p-4 rounded-lg w-full max-w-2xl mb-6 overflow-auto">
            <pre className="text-rose-400 text-sm whitespace-pre-wrap">
              {this.state.error?.message}
            </pre>
          </div>
          <button
            onClick={() => window.location.reload()}
            className="flex items-center gap-2 px-6 py-3 bg-primary text-black font-bold rounded-lg hover:opacity-90 transition-opacity"
          >
            <RefreshCcw className="w-5 h-5" /> Reload Application
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
