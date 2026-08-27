from enum import Enum

from pydantic import BaseModel

from app.models.project import ProjectState


class PipelineStage(str, Enum):
    DISCOVERY = "discovery"
    REQUIREMENTS = "requirements"
    ARCHITECTURE = "architecture"
    CONTEXT = "context"
    VALIDATION = "validation"
    COMPLETE = "complete"


class PipelineResult(BaseModel):
    stage: PipelineStage
    complete: bool

    project: ProjectState

    missing_fields: list[str] = []
    questions: list[dict] = []

    project_id: str | None = None
    download_markdown: str | None = None
    download_txt: str | None = None
