export type PipelineStage =
  | "discovery"
  | "requirements"
  | "architecture"
  | "context"
  | "validation"
  | "complete";

export interface Question {
  field: string;
  question: string;
  reason: string;
}

export interface ProjectState {
  name: string | null;
  description: string | null;
  problem: string | null;
  target_users: string[];
  core_features: string[];
  platform: string | null;
  technologies: string[];
  database: string | null;
  authentication: string | null;
  integrations: string[];
  constraints: string[];
  deployment: string | null;
}

export interface PipelineResult {
  stage: PipelineStage;
  complete: boolean;
  project: ProjectState;
  missing_fields: string[];
  questions: Question[];
  project_id: string | null;
  download_markdown: string | null;
  download_txt: string | null;
}
