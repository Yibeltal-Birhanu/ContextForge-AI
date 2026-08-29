from enum import Enum

from pydantic import BaseModel

from app.models.project import ProjectState


class PipelineStage(str, Enum):
    DISCOVERY = "discovery"
    REQUIREMENTS = "requirements"
    ARCHITECTURE = "architecture"
    CONTEXT = "context"
    VALIDATION = "validation"
    IMPROVEMENT = "improvement"
    COMPLETE = "complete"


class QualityInfo(BaseModel):
    overall_score: int = 0
    validation_score: int = 0
    readiness_score: int = 0
    ready_for_agent: bool = False
    checks: dict = {}
    warnings_count: int = 0
    assumptions_count: int = 0
    warnings: list[dict] = []
    assumptions: list[dict] = []
    errors: list[str] = []
    rejection_reasons: list[str] = []
    tech_preservation: dict = {}


class PipelineResult(BaseModel):
    stage: PipelineStage
    complete: bool

    project: ProjectState

    missing_fields: list[str] = []
    questions: list[dict] = []
    conversation_history: list[dict] = []

    project_id: str | None = None
    download_markdown: str | None = None
    download_txt: str | None = None
    quality: QualityInfo | None = None
