from pydantic import BaseModel
from typing import List, Optional


class ImproveContextRequest(BaseModel):
    project_id: Optional[str] = None
    project: dict
    answers: dict
    quality_checks: dict
    improvement_targets: Optional[List[str]] = None


class ImproveContextResponse(BaseModel):
    stage: str
    complete: bool
    project: dict
    quality: Optional[dict] = None
    project_id: Optional[str] = None
    download_markdown: Optional[str] = None
    download_txt: Optional[str] = None
    message: Optional[str] = None
