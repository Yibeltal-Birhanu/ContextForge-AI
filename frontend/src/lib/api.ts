import type { PipelineResult } from "@/types/project";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export function getDownloadUrl(path: string): string {
  if (path.startsWith("http")) {
    return path;
  }
  return `${API_URL}${path}`;
}

export async function startProject(
  idea: string
): Promise<PipelineResult> {
  const response = await fetch(`${API_URL}/projects/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ idea }),
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
  answers: Record<string, string | string[]>
): Promise<PipelineResult> {
  const response = await fetch(`${API_URL}/projects/continue`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project, answers }),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail || `Server error (${response.status})`;
    throw new Error(detail);
  }

  return response.json();
}
