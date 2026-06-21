import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projects, decisions, bugs, indexing, analysis, code, chat, search } from '@/lib/api';

// ── Projects ──

export function useProjects() {
  return useQuery({
    queryKey: ['projects'],
    queryFn: projects.list,
  });
}

export function useProject(id: string | null) {
  return useQuery({
    queryKey: ['project', id],
    queryFn: () => projects.get(id!),
    enabled: !!id,
  });
}

export function useCreateProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: projects.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['projects'] }),
  });
}

// ── Decisions ──

export function useDecisions(projectId: string | null) {
  return useQuery({
    queryKey: ['decisions', projectId],
    queryFn: () => decisions.list(projectId!),
    enabled: !!projectId,
  });
}

export function useDecision(id: string | null) {
  return useQuery({
    queryKey: ['decision', id],
    queryFn: () => decisions.get(id!),
    enabled: !!id,
  });
}

export function useCreateDecision() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: decisions.create,
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: ['decisions', vars.project_id] });
    },
  });
}

// ── Bugs ──

export function useBugs(projectId: string | null) {
  return useQuery({
    queryKey: ['bugs', projectId],
    queryFn: () => bugs.list(projectId!),
    enabled: !!projectId,
  });
}

export function useBug(id: string | null) {
  return useQuery({
    queryKey: ['bug', id],
    queryFn: () => bugs.get(id!),
    enabled: !!id,
  });
}

export function useCreateBug() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: bugs.create,
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: ['bugs', vars.project_id] });
    },
  });
}

// ── Indexing ──

export function useIndexStatus(projectId: string | null) {
  return useQuery({
    queryKey: ['index-status', projectId],
    queryFn: () => indexing.getStatus(projectId!),
    enabled: !!projectId,
    refetchInterval: (query) => {
      const data = query.state.data;
      return data?.running_job ? 2000 : false;
    },
  });
}

export function useStartIndex() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: indexing.start,
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: ['index-status', vars.project_id] });
    },
  });
}

// ── Analysis ──

export function useAnalysisReports(projectId: string | null) {
  return useQuery({
    queryKey: ['analysis-reports', projectId],
    queryFn: () => analysis.listReports(projectId!),
    enabled: !!projectId,
  });
}

export function useAnalysisReport(reportId: string | null) {
  return useQuery({
    queryKey: ['analysis-report', reportId],
    queryFn: () => analysis.getReport(reportId!),
    enabled: !!reportId,
  });
}

export function useAnalyzePR() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: analysis.analyzePR,
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: ['analysis-reports', vars.project_id] });
    },
  });
}

// ── Code ──

export function useSearchCode(query: string, projectId: string | null) {
  return useQuery({
    queryKey: ['code-search', query, projectId],
    queryFn: () => code.search(query, projectId!),
    enabled: !!query && !!projectId,
  });
}

export function useFileEntries(projectId: string | null, filePath: string | null) {
  return useQuery({
    queryKey: ['file-entries', projectId, filePath],
    queryFn: () => code.getFileEntries(projectId!, filePath!),
    enabled: !!projectId && !!filePath,
  });
}

// ── Chat ──

export function useChat() {
  return useMutation({
    mutationFn: ({ projectId, message }: { projectId: string; message: string }) =>
      chat.send(projectId, message),
  });
}

// ── Search ──

export function useSearchMemories(query: string, projectId?: string) {
  return useQuery({
    queryKey: ['memory-search', query, projectId],
    queryFn: () => search.memories(query, projectId),
    enabled: !!query,
  });
}
