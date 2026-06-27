import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CodeViewer } from '../CodeViewer';
import type { FileEntry } from '@/lib/api-types';

const mockEntries: FileEntry[] = [
  {
    name: 'Project',
    entry_type: 'class',
    content: 'class Project:\n    pass',
    language: 'python',
    start_line: 1,
    end_line: 3,
    metadata: {},
  },
];

describe('CodeViewer', () => {

  it('shows loading state', () => {
    render(<CodeViewer filePath="test.py" entries={[]} isLoading={true} />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('shows file header with path', () => {
    render(<CodeViewer filePath="forge/app.py" entries={[]} isLoading={false} />);
    expect(screen.getByText('forge/app.py')).toBeInTheDocument();
  });

  it('shows copy button', () => {
    render(<CodeViewer filePath="test.py" entries={[]} isLoading={false} />);
    expect(screen.getByText('Copy')).toBeInTheDocument();
  });

  it('shows code lines with line numbers', () => {
    render(<CodeViewer filePath="test.py" entries={mockEntries} isLoading={false} />);
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('class Project:')).toBeInTheDocument();
    expect(screen.getByText(/pass/)).toBeInTheDocument();
  });

  it('shows empty state when no entries', () => {
    render(<CodeViewer filePath="test.py" entries={[]} isLoading={false} />);
    expect(screen.getByText('No entries indexed for this file')).toBeInTheDocument();
  });

  it('copy button copies content to clipboard and shows Copied', async () => {
    const user = userEvent.setup();
    render(<CodeViewer filePath="test.py" entries={mockEntries} isLoading={false} />);
    expect(screen.getByText('Copy')).toBeInTheDocument();
    await user.click(screen.getByText('Copy'));
    expect(screen.getByText('Copied')).toBeInTheDocument();
    expect(screen.queryByText('Copy')).not.toBeInTheDocument();
  });
});
