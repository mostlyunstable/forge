import { useState } from 'react';
import { ChevronRight, ChevronDown, File, Folder, FolderOpen, FileCode, FileText, FileJson } from 'lucide-react';
import { cn } from '@/lib/utils';

interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  children?: FileNode[];
}

const fileTree: FileNode[] = [
  {
    name: 'forge',
    path: 'forge',
    type: 'directory',
    children: [
      {
        name: 'domain',
        path: 'forge/domain',
        type: 'directory',
        children: [
          { name: 'project.py', path: 'forge/domain/project.py', type: 'file' },
          { name: 'decision.py', path: 'forge/domain/decision.py', type: 'file' },
          { name: 'bug.py', path: 'forge/domain/bug.py', type: 'file' },
        ],
      },
      {
        name: 'application',
        path: 'forge/application',
        type: 'directory',
        children: [
          { name: 'chat.py', path: 'forge/application/chat.py', type: 'file' },
          { name: 'code.py', path: 'forge/application/code.py', type: 'file' },
          { name: 'indexing.py', path: 'forge/application/indexing.py', type: 'file' },
        ],
      },
      {
        name: 'infrastructure',
        path: 'forge/infrastructure',
        type: 'directory',
        children: [
          { name: 'repos.py', path: 'forge/infrastructure/repos.py', type: 'file' },
          { name: 'search.py', path: 'forge/infrastructure/search.py', type: 'file' },
        ],
      },
      {
        name: 'presentation',
        path: 'forge/presentation',
        type: 'directory',
        children: [
          { name: 'app.py', path: 'forge/presentation/app.py', type: 'file' },
          { name: 'routes.py', path: 'forge/presentation/routes.py', type: 'file' },
        ],
      },
    ],
  },
];

function getFileIcon(name: string) {
  if (name.endsWith('.py')) return FileCode;
  if (name.endsWith('.json')) return FileJson;
  if (name.endsWith('.md')) return FileText;
  return File;
}

interface FileTreeItemProps {
  node: FileNode;
  selectedFile: string | null;
  onSelect: (path: string) => void;
  level?: number;
}

function FileTreeItem({ node, selectedFile, onSelect, level = 0 }: FileTreeItemProps) {
  const [expanded, setExpanded] = useState(level < 1);

  if (node.type === 'file') {
    const FileIcon = getFileIcon(node.name);
    const isSelected = selectedFile === node.path;

    return (
      <button
        onClick={() => onSelect(node.path)}
        className={cn(
          'group flex w-full items-center gap-2 h-[28px] text-[12px] transition-colors duration-120',
          isSelected
            ? 'bg-[var(--color-bg-elevated)] text-[var(--color-accent-blue)]'
            : 'text-[var(--color-text-muted)] hover:bg-[var(--color-bg-elevated)] hover:text-[var(--color-text-secondary)]'
        )}
        style={{ paddingLeft: `${(level * 14) + 12}px`, paddingRight: '12px' }}
      >
        <FileIcon className={cn(
          'h-[14px] w-[14px] shrink-0',
          isSelected ? 'text-[var(--color-accent-blue)]' : 'text-[var(--color-text-muted)]'
        )} />
        <span className="truncate font-mono text-[12px]">{node.name}</span>
      </button>
    );
  }

  return (
    <div>
      <button
        onClick={() => setExpanded(!expanded)}
        className="group flex w-full items-center gap-2 h-[28px] text-[12px] text-[var(--color-text-muted)] transition-colors duration-120 hover:bg-[var(--color-bg-elevated)] hover:text-[var(--color-text-secondary)]"
        style={{ paddingLeft: `${(level * 14) + 12}px`, paddingRight: '12px' }}
      >
        <span className="flex h-[14px] w-[14px] shrink-0 items-center justify-center">
          {expanded ? (
            <ChevronDown className="h-[12px] w-[12px] text-[var(--color-text-muted)]" />
          ) : (
            <ChevronRight className="h-[12px] w-[12px] text-[var(--color-text-muted)]" />
          )}
        </span>
        {expanded ? (
          <FolderOpen className="h-[14px] w-[14px] shrink-0 text-[var(--color-accent-blue)]" />
        ) : (
          <Folder className="h-[14px] w-[14px] shrink-0 text-[var(--color-text-muted)]" />
        )}
        <span className="truncate text-[12px] font-medium">{node.name}</span>
      </button>
      {expanded && node.children && (
        <div>
          {node.children.map((child) => (
            <FileTreeItem
              key={child.path}
              node={child}
              selectedFile={selectedFile}
              onSelect={onSelect}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface FileTreeProps {
  onSelect: (path: string) => void;
  selectedFile: string | null;
}

export function FileTree({ onSelect, selectedFile }: FileTreeProps) {
  return (
    <div className="overflow-y-auto py-1">
      {fileTree.map((node) => (
        <FileTreeItem
          key={node.path}
          node={node}
          selectedFile={selectedFile}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}