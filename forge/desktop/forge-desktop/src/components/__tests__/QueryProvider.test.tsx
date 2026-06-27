import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { useQuery } from '@tanstack/react-query';
import { QueryProvider } from '../QueryProvider';

function TestChild() {
  return <div>Test child</div>;
}

function TestQueryConsumer() {
  const { data } = useQuery({
    queryKey: ['test-query'],
    queryFn: () => 'query-data',
  });
  return <div>{data ?? 'loading'}</div>;
}

describe('QueryProvider', () => {
  it('renders children', () => {
    render(
      <QueryProvider>
        <TestChild />
      </QueryProvider>
    );

    expect(screen.getByText('Test child')).toBeInTheDocument();
  });

  it('provides QueryClient context to children', async () => {
    render(
      <QueryProvider>
        <TestQueryConsumer />
      </QueryProvider>
    );

    expect(screen.getByText('loading')).toBeInTheDocument();
  });
});
