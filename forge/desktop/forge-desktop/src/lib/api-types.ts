// ── API Types (mirrors Forge backend schemas) ──

export interface Project {
  id: string;
  name: string;
  description: string;
  stack: string[];
  goals: string[];
  status: string;
  repository_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectSummary {
  id: string;
  name: string;
  description: string;
  status: string;
  stack: string[];
}

export interface ListProjectsResponse {
  projects: ProjectSummary[];
  total: number;
}

export interface Decision {
  id: string;
  project_id: string;
  title: string;
  decision: string;
  reason: string;
  alternatives: string[];
  status: string;
  created_at: string;
}

export interface DecisionSummary {
  id: string;
  title: string;
  decision: string;
  status: string;
  created_at: string;
}

export interface ListDecisionsResponse {
  decisions: DecisionSummary[];
  total: number;
  project_id: string;
}

export interface Bug {
  id: string;
  project_id: string;
  title: string;
  problem: string;
  root_cause: string;
  solution: string;
  affected_files: string[];
  severity: string;
  resolved: boolean;
  created_at: string;
}

export interface BugSummary {
  id: string;
  title: string;
  severity: string;
  resolved: boolean;
  created_at: string;
}

export interface ListBugsResponse {
  bugs: BugSummary[];
  total: number;
  project_id: string;
}

export interface CodeEntry {
  id: string;
  name: string;
  entry_type: string;
  file_path: string;
  language: string;
  start_line: number;
  end_line: number;
}

export interface SearchCodeResponse {
  results: CodeEntry[];
  query: string;
  total: number;
}

export interface FileEntry {
  name: string;
  entry_type: string;
  content: string;
  language: string;
  start_line: number;
  end_line: number;
  metadata: Record<string, unknown>;
}

export interface GetFileEntriesResponse {
  file_path: string;
  entries: FileEntry[];
  total: number;
}

export interface IndexJob {
  id: string;
  project_id: string;
  type: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  progress: Record<string, unknown>;
  result: Record<string, unknown>;
  error_log: unknown[];
  state_hash: string;
  created_by: string;
  created_at: string;
  duration_seconds: number | null;
}

export interface IndexStatusResponse {
  project_id: string;
  total_files_indexed: number;
  last_index_job: IndexJob | null;
  running_job: IndexJob | null;
  candidates_by_kind: Record<string, number>;
}

export interface Recommendation {
  area: string;
  priority: string;
  description: string;
  files: string[];
}

export interface AnalyzePRResponse {
  report_id: string;
  project_id: string;
  pr_number: number | null;
  title: string;
  summary: string;
  risk_score: number;
  risk_level: string;
  blast_radius: number;
  files_changed: number;
  directly_affected: string[];
  transitively_affected: string[];
  reverse_affected: string[];
  related_decisions: number;
  related_bugs: number;
  related_commits: number;
  recommendations: Recommendation[];
}

export interface AnalysisReportSummary {
  id: string;
  project_id: string;
  pr_number: number | null;
  title: string;
  risk_score: number;
  risk_level: string;
  files_changed: number;
  blast_radius: number;
  created_at: string;
}

export interface ListAnalysisReportsResponse {
  reports: AnalysisReportSummary[];
  total: number;
  project_id: string;
}

export interface AnalysisReportDetail extends AnalysisReportSummary {
  summary: string;
  directly_affected: string[];
  transitively_affected: string[];
  reverse_affected: string[];
  related_decisions: number;
  related_bugs: number;
  related_commits: number;
  recommendations: Recommendation[];
}

export interface ChatSource {
  type: string;
  name: string;
  score: number;
  file: string | null;
}

export interface SendMessageResponse {
  response: string;
  sources: ChatSource[];
  project_id: string;
}

export interface MemoryResult {
  type: string;
  id: string;
  title: string;
  content: string;
  score: number;
}

export interface SearchMemoriesResponse {
  results: MemoryResult[];
  query: string;
  total: number;
}

// ── Git ──

export interface CommitSummary {
  sha: string;
  message: string;
  author: string;
  classification: string;
  files_changed: string[];
  timestamp: string;
}

export interface AnalyzeCommitsResponse {
  commits: CommitSummary[];
  total: number;
  by_classification: Record<string, number>;
}
