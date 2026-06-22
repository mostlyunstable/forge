import { useState } from 'react';
import { useBugs, useCreateBug, useUpdateBug, useDeleteBug } from '@/hooks/useApi';
import { useSettings } from '@/stores/settings';
import { SkeletonRow } from '@/components/ui/SkeletonRow';
import { ErrorState } from '@/components/ui/ErrorState';
import { Plus, Trash2 } from 'lucide-react';

export function BugsView() {
  const currentProjectId = useSettings((s) => s.currentProjectId);
  const bugsQuery = useBugs(currentProjectId);
  const createBug = useCreateBug();
  const updateBug = useUpdateBug();
  const deleteBug = useDeleteBug();

  const bugList = bugsQuery.data?.bugs ?? [];
  const [slideOpen, setSlideOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState({
    title: '',
    problem: '',
    root_cause: '',
    solution: '',
    severity: 'medium',
    resolved: false,
  });
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const openCreate = () => {
    setEditingId(null);
    setForm({ title: '', problem: '', root_cause: '', solution: '', severity: 'medium', resolved: false });
    setSlideOpen(true);
  };

  const openEdit = (b: { id: string; title: string; severity: string; resolved: boolean }) => {
    setEditingId(b.id);
    setForm({
      title: b.title,
      problem: '',
      root_cause: '',
      solution: '',
      severity: b.severity,
      resolved: b.resolved,
    });
    setSlideOpen(true);
  };

  const handleSave = async () => {
    if (!currentProjectId) return;
    if (editingId) {
      await updateBug.mutateAsync({ id: editingId, data: form });
    } else {
      await createBug.mutateAsync({ project_id: currentProjectId, title: form.title, problem: form.problem, root_cause: form.root_cause, solution: form.solution, severity: form.severity });
    }
    setSlideOpen(false);
  };

  const handleDelete = async (id: string) => {
    await deleteBug.mutateAsync(id);
    setConfirmDeleteId(null);
  };

  const severityBadge = (severity: string) => {
    switch (severity) {
      case 'critical': return 'badge-red';
      case 'high': return 'badge-amber';
      case 'medium': return 'badge-blue';
      default: return 'badge-muted';
    }
  };

  return (
    <div className="flex h-full">
      <div className="flex-1 overflow-y-auto">
        <div className="px-6 pt-6 pb-4">
          <div className="mb-6 flex items-center justify-between">
            <h1 className="text-display-sm">Bugs</h1>
            <button onClick={openCreate} className="btn btn-primary">
              <Plus className="h-[14px] w-[14px]" />
              New Bug
            </button>
          </div>

          <div className="memory-pulse memory-pulse--active mb-6" />

          {bugsQuery.isLoading ? (
            <SkeletonRow lines={6} />
          ) : bugsQuery.error ? (
            <ErrorState
              code="API_ERROR"
              message="Failed to load bugs."
              retry={() => bugsQuery.refetch()}
            />
          ) : bugList.length === 0 ? (
            <div className="text-[13px] text-[var(--color-text-muted)] py-8">
              No bugs tracked yet.
            </div>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Severity</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th className="w-[80px]">Actions</th>
                </tr>
              </thead>
              <tbody>
                {bugList.map((b) => (
                  <tr key={b.id}>
                    <td>
                      <button
                        onClick={() => openEdit(b)}
                        className="text-left text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors duration-120"
                      >
                        {b.title}
                      </button>
                    </td>
                    <td>
                      <span className={`badge ${severityBadge(b.severity)}`}>
                        {b.severity}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${b.resolved ? 'badge-green' : 'badge-muted'}`}>
                        {b.resolved ? 'resolved' : 'open'}
                      </span>
                    </td>
                    <td className="mono">{new Date(b.created_at).toLocaleDateString()}</td>
                    <td>
                      {confirmDeleteId === b.id ? (
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleDelete(b.id)}
                            className="text-[11px] text-[var(--color-accent-red)]"
                          >
                            Yes
                          </button>
                          <button
                            onClick={() => setConfirmDeleteId(null)}
                            className="text-[11px] text-[var(--color-text-muted)]"
                          >
                            No
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => setConfirmDeleteId(b.id)}
                          className="text-[var(--color-text-muted)] hover:text-[var(--color-accent-red)] transition-colors duration-120"
                        >
                          <Trash2 className="h-[14px] w-[14px]" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Slide-over panel */}
      {slideOpen && (
        <div className="w-[380px] shrink-0 border-l border-[var(--color-border-subtle)] bg-[var(--color-bg-surface)] overflow-y-auto">
          <div className="p-6">
            <div className="mb-6 flex items-center justify-between">
              <h2 className="text-[16px] font-semibold text-[var(--color-text-primary)]">
                {editingId ? 'Edit Bug' : 'New Bug'}
              </h2>
              <button
                onClick={() => setSlideOpen(false)}
                className="text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] text-[13px]"
              >
                Close
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-label mb-1 block">Title</label>
                <input
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  className="input"
                  placeholder="Bug title"
                />
              </div>

              <div>
                <label className="text-label mb-1 block">Problem</label>
                <textarea
                  value={form.problem}
                  onChange={(e) => setForm({ ...form, problem: e.target.value })}
                  className="input min-h-[80px] resize-y"
                  placeholder="Describe the problem"
                />
              </div>

              <div>
                <label className="text-label mb-1 block">Root Cause</label>
                <textarea
                  value={form.root_cause}
                  onChange={(e) => setForm({ ...form, root_cause: e.target.value })}
                  className="input min-h-[60px] resize-y"
                  placeholder="Root cause analysis"
                />
              </div>

              <div>
                <label className="text-label mb-1 block">Solution</label>
                <textarea
                  value={form.solution}
                  onChange={(e) => setForm({ ...form, solution: e.target.value })}
                  className="input min-h-[60px] resize-y"
                  placeholder="How it was fixed"
                />
              </div>

              <div>
                <label className="text-label mb-1 block">Severity</label>
                <select
                  value={form.severity}
                  onChange={(e) => setForm({ ...form, severity: e.target.value })}
                  className="input"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>

              {editingId && (
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={form.resolved}
                    onChange={(e) => setForm({ ...form, resolved: e.target.checked })}
                    className="h-4 w-4"
                  />
                  <label className="text-[13px] text-[var(--color-text-secondary)]">Resolved</label>
                </div>
              )}

              <button onClick={handleSave} className="btn btn-primary w-full">
                {createBug.isPending || updateBug.isPending ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}