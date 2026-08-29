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

export interface QualityChecks {
  requirements_coverage: number;
  architecture_consistency: number;
  technology_consistency: number;
  api_coverage: number;
  data_model_coverage: number;
  security_coverage: number;
  implementation_coverage: number;
  agent_rules_quality: number;
  definition_of_done: number;
}

export interface QualityWarning {
  category: string;
  message: string;
}

export interface QualityAssumption {
  area: string;
  assumption: string;
  severity: string;
}

export interface QualityInfo {
  overall_score: number;
  validation_score: number;
  readiness_score: number;
  ready_for_agent: boolean;
  checks: QualityChecks;
  warnings_count: number;
  assumptions_count: number;
  warnings: QualityWarning[];
  assumptions: QualityAssumption[];
  errors: string[];
  rejection_reasons: string[];
}

export interface ConversationEntry {
  field: string;
  question: string;
  answer: string;
}

export interface PipelineResult {
  stage: PipelineStage;
  complete: boolean;
  project: ProjectState;
  missing_fields: string[];
  questions: Question[];
  conversation_history: ConversationEntry[];
  project_id: string | null;
  download_markdown: string | null;
  download_txt: string | null;
  quality: QualityInfo | null;
}
