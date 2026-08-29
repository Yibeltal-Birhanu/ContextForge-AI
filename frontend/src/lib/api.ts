import type { PipelineResult } from "@/types/project";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export function getDownloadUrl(path: string): string {
  if (path.startsWith("http")) {
    return path;
  }
  return `${API_URL}${path}`;
}

// ============================================================
// Pipeline endpoints
// ============================================================

export async function startProject(
  idea: string,
  projectId?: string | null
): Promise<PipelineResult> {
  const response = await fetch(`${API_URL}/projects/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ idea, project_id: projectId || undefined }),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail || `Server error (${response.status})`;
    throw new Error(detail);
  }

  return response.json();
}

export async function continueProject(
  project: PipelineResult["project"],
  answers: Record<string, string | string[]>,
  conversationHistory: Array<{ field: string; answer: string }> = [],
  projectId?: string | null
): Promise<PipelineResult> {
  const response = await fetch(`${API_URL}/projects/continue`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      project,
      answers,
      conversation_history: conversationHistory,
      project_id: projectId || undefined,
    }),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail || `Server error (${response.status})`;
    throw new Error(detail);
  }

  return response.json();
}

export async function improveProject(
  project: PipelineResult["project"],
  answers: Record<string, string | string[]>,
  qualityChecks: Record<string, unknown>,
  projectId?: string | null
): Promise<PipelineResult> {
  const response = await fetch(`${API_URL}/projects/improve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      project_id: projectId || undefined,
      project,
      answers,
      quality_checks: qualityChecks,
    }),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail || `Server error (${response.status})`;
    throw new Error(detail);
  }

  return response.json();
}

// ============================================================
// Project management endpoints
// ============================================================

export interface ProjectSummary {
  id: string;
  name: string;
  idea: string;
  description: string;
  status: string;
  current_stage: string;
  project_data: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectDetail {
  project: ProjectSummary;
  context: Record<string, unknown> | null;
  artifacts: Array<{ id: string; quality_score: number; created_at: string }>;
  latest_artifact: { id: string; quality_score: number; created_at: string } | null;
}

export async function listProjects(): Promise<ProjectSummary[]> {
  const response = await fetch(`${API_URL}/projects`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });

  if (!response.ok) {
    throw new Error("Failed to load projects.");
  }

  const data = await response.json();
  return data.projects || [];
}

export async function getProjectDetail(
  projectId: string
): Promise<ProjectDetail> {
  const response = await fetch(`${API_URL}/projects/${projectId}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });

  if (!response.ok) {
    throw new Error("Project not found.");
  }

  return response.json();
}

export async function createProject(
  name: string,
  idea: string,
  description: string = ""
): Promise<ProjectSummary> {
  const response = await fetch(`${API_URL}/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, idea, description }),
  });

  if (!response.ok) {
    throw new Error("Failed to create project.");
  }

  return response.json();
}

export async function updateProject(
  projectId: string,
  data: {
    name?: string;
    description?: string;
    status?: string;
    current_stage?: string;
    project_data?: Record<string, unknown>;
  }
): Promise<ProjectSummary> {
  const response = await fetch(`${API_URL}/projects/${projectId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error("Failed to update project.");
  }

  return response.json();
}

export async function deleteProject(
  projectId: string
): Promise<void> {
  const response = await fetch(`${API_URL}/projects/${projectId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error("Failed to delete project.");
  }
}

export async function getProjectArtifacts(
  projectId: string
): Promise<Array<{ id: string; quality_score: number; created_at: string }>> {
  const response = await fetch(`${API_URL}/projects/${projectId}/artifacts`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });

  if (!response.ok) {
    return [];
  }

  const data = await response.json();
  return data.artifacts || [];
}

// ============================================================
// Resume endpoints
// ============================================================

export async function saveProjectState(
  projectId: string,
  projectData: Record<string, unknown>,
  options: {
    status?: string;
    current_stage?: string;
    name?: string;
  } = {}
): Promise<ProjectSummary> {
  const response = await fetch(`${API_URL}/projects/${projectId}/resume`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      project_data: projectData,
      ...options,
    }),
  });

  if (!response.ok) {
    throw new Error("Failed to save project state.");
  }

  return response.json();
}

export async function getProjectState(
  projectId: string
): Promise<{
  project: ProjectSummary;
  project_data: Record<string, unknown>;
  status: string;
  current_stage: string;
}> {
  const response = await fetch(`${API_URL}/projects/${projectId}/state`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });

  if (!response.ok) {
    throw new Error("Project not found.");
  }

  return response.json();
}
