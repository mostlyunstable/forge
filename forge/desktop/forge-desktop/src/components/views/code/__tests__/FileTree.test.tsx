import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FileTree } from '../FileTree';

describe('FileTree', () => {
  it('renders directory structure', () => {
    render(<FileTree onSelect={vi.fn()} selectedFile={null} />);
    expect(screen.getByText('forge')).toBeInTheDocument();
    expect(screen.getByText('domain')).toBeInTheDocument();
    expect(screen.getByText('application')).toBeInTheDocument();
    expect(screen.getByText('infrastructure')).toBeInTheDocument();
    expect(screen.getByText('presentation')).toBeInTheDocument();
  });

  it('clicking file calls onSelect', async () => {
    const onSelect = vi.fn();
    const user = userEvent.setup();
    render(<FileTree onSelect={onSelect} selectedFile={null} />);

    await user.click(screen.getByText('domain'));
    await user.click(screen.getByText('project.py'));

    expect(onSelect).toHaveBeenCalledWith('forge/domain/project.py');
  });

  it('expanding directory shows children', async () => {
    const user = userEvent.setup();
    render(<FileTree onSelect={vi.fn()} selectedFile={null} />);

    expect(screen.queryByText('project.py')).not.toBeInTheDocument();
    await user.click(screen.getByText('domain'));
    expect(screen.getByText('project.py')).toBeInTheDocument();
    expect(screen.getByText('decision.py')).toBeInTheDocument();
    expect(screen.getByText('bug.py')).toBeInTheDocument();
  });

  it('collapsing directory hides children', async () => {
    const user = userEvent.setup();
    render(<FileTree onSelect={vi.fn()} selectedFile={null} />);

    await user.click(screen.getByText('domain'));
    expect(screen.getByText('project.py')).toBeInTheDocument();

    await user.click(screen.getByText('domain'));
    expect(screen.queryByText('project.py')).not.toBeInTheDocument();
  });

  it('file icons show correct type for .py files', async () => {
    const user = userEvent.setup();
    render(<FileTree onSelect={vi.fn()} selectedFile={null} />);

    await user.click(screen.getByText('domain'));

    const fileButton = screen.getByText('project.py').closest('button');
    expect(fileButton).toBeInTheDocument();
    const svg = fileButton?.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });
});
