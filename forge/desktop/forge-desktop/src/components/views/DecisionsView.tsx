import { useState } from 'react';
import { useDecisions, useCreateDecision, useUpdateDecision, useDeleteDecision } from '@/hooks/useApi';
import { useSettings } from '@/stores/settings';
import { SkeletonRow } from '@/components/ui/SkeletonRow';
import { ErrorState } from '@/components/ui/ErrorState';
import { Plus, Trash2 } from 'lucide-react';

export function DecisionsView() {
  const currentProjectId = useSettings((s) => s.currentProjectId);
  const decisionsQuery = useDecisions(currentProjectId);
  const createDecision = useCreateDecision();
  const updateDecision = useUpdateDecision();
  const deleteDecision = useDeleteDecision();

  const decisions = decisionsQuery.data?.decisions ?? [];
  const [slideOpen, setSlideOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState({ title: '', decision: '', reason: '', status: 'proposed' });
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const openCreate = () => {
    setEditingId(null);
    setForm({ title: '', decision: '', reason: '', status: 'proposed' });
    setSlideOpen(true);
  };

  const openEdit = (d: { id: string; title: string; decision: string; status: string }) => {
    setEditingId(d.id);
    setForm({ title: d.title, decision: d.decision, reason: '', status: d.status });
    setSlideOpen(true);
  };

  const handleSave = async () => {
    if (!currentProjectId) return;
    if (editingId) {
      await updateDecision.mutateAsync({ id: editingId, data: form });
    } else {
      await createDecision.mutateAsync({ project_id: currentProjectId, ...form });
    }
    setSlideOpen(false);
  };

  const handleDelete = async (id: string) => {
    await deleteDecision.mutateAsync(id);
    setConfirmDeleteId(null);
  };

  return (
    <div className="flex h-full">
      <div className="flex-1 overflow-y-auto">
        <div className="px-6 pt-6 pb-4">
          <div className="mb-6 flex items-center justify-between">
            <h1 className="text-display-sm">Decisions</h1>
            <button onClick={openCreate} className="btn btn-primary">
              <Plus className="h-[14px] w-[14px]" />
              New Decision
            </button>
          </div>

          <div className="memory-pulse memory-pulse--active mb-6" />

          {decisionsQuery.isLoading ? (
            <SkeletonRow lines={6} />
          ) : decisionsQuery.error ? (
            <ErrorState
              code="API_ERROR"
              message="Failed to load decisions."
              retry={() => decisionsQuery.refetch()}
            />
          ) : decisions.length === 0 ? (
            <div className="text-[13px] text-[var(--color-text-muted)] py-8">
              No decisions recorded yet.
            </div>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th className="w-[80px]">Actions</th>
                </tr>
              </thead>
              <tbody>
                {decisions.map((d) => (
                  <tr key={d.id}>
                    <td>
                      <button
                        onClick={() => openEdit(d)}
                        className="text-left text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors duration-120"
                      >
                        {d.title}
                      </button>
                    </td>
                    <td>
                      <span className={`badge ${
                        d.status === 'accepted' ? 'badge-green' :
                        d.status === 'superseded' ? 'badge-muted' :
                        'badge-blue'
                      }`}>
                        {d.status}
                      </span>
                    </td>
                    <td className="mono">{new Date(d.created_at).toLocaleDateString()}</td>
                    <td>
                      {confirmDeleteId === d.id ? (
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleDelete(d.id)}
                            className="text-[11px] text-[var(--color-accent-red)] hover:text-[var(--color-accent-red)]"
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
                          onClick={() => setConfirmDeleteId(d.id)}
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
                {editingId ? 'Edit Decision' : 'New Decision'}
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
                  placeholder="Decision title"
                />
              </div>

              <div>
                <label className="text-label mb-1 block">Decision</label>
                <textarea
                  value={form.decision}
                  onChange={(e) => setForm({ ...form, decision: e.target.value })}
                  className="input min-h-[100px] resize-y"
                  placeholder="What was decided"
                />
              </div>

              <div>
                <label className="text-label mb-1 block">Reason</label>
                <textarea
                  value={form.reason}
                  onChange={(e) => setForm({ ...form, reason: e.target.value })}
                  className="input min-h-[60px] resize-y"
                  placeholder="Why this decision was made"
                />
              </div>

              <div>
                <label className="text-label mb-1 block">Status</label>
                <select
                  value={form.status}
                  onChange={(e) => setForm({ ...form, status: e.target.value })}
                  className="input"
                >
                  <option value="proposed">Proposed</option>
                  <option value="accepted">Accepted</option>
                  <option value="superseded">Superseded</option>
                </select>
              </div>

              <button onClick={handleSave} className="btn btn-primary w-full">
                {createDecision.isPending || updateDecision.isPending ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}