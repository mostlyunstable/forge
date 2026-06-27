import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CodeInsightPanel } from '../CodeInsightPanel';
import type { FileEntry } from '@/lib/api-types';

const mockEntries: FileEntry[] = [
  {
    name: 'Project',
    entry_type: 'class',
    content: 'class Project: pass',
    language: 'python',
    start_line: 1,
    end_line: 5,
    metadata: {},
  },
  {
    name: 'create_project',
    entry_type: 'function',
    content: 'def create_project(): pass',
    language: 'python',
    start_line: 7,
    end_line: 10,
    metadata: {},
  },
];

describe('CodeInsightPanel', () => {
  it('renders file summary with entries count and language', () => {
    render(<CodeInsightPanel filePath="test.py" entries={mockEntries} />);
    expect(screen.getByText('File Summary')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('Entries')).toBeInTheDocument();
    expect(screen.getByText('python')).toBeInTheDocument();
    expect(screen.getByText('Language')).toBeInTheDocument();
  });

  it('renders entry types badges', () => {
    render(<CodeInsightPanel filePath="test.py" entries={mockEntries} />);
    expect(screen.getByText('Entry Types')).toBeInTheDocument();
    expect(screen.getByText('class: 1')).toBeInTheDocument();
    expect(screen.getByText('function: 1')).toBeInTheDocument();
  });

  it('renders entries list with names and line ranges', () => {
    render(<CodeInsightPanel filePath="test.py" entries={mockEntries} />);
    expect(screen.getByText('Entries in File')).toBeInTheDocument();
    expect(screen.getByText('Project')).toBeInTheDocument();
    expect(screen.getByText('create_project')).toBeInTheDocument();
    expect(screen.getByText('L1–5')).toBeInTheDocument();
    expect(screen.getByText('L7–10')).toBeInTheDocument();
  });

  it('handles empty entries', () => {
    render(<CodeInsightPanel filePath="test.py" entries={[]} />);
    expect(screen.getByText('File Summary')).toBeInTheDocument();
    expect(screen.getByText('0')).toBeInTheDocument();
    expect(screen.getByText('—')).toBeInTheDocument();
    expect(screen.queryByText('Entry Types')).not.toBeInTheDocument();
    expect(screen.queryByText('Entries in File')).not.toBeInTheDocument();
  });
});
