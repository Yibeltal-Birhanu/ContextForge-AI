from pydantic import BaseModel
from typing import Optional


class ContextArtifact(BaseModel):

    project_id: str

    project_name: str

    markdown: str

    text: str

    validation_score: int

    valid: bool
