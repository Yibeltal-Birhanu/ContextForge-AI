from pydantic import BaseModel
from typing import Optional


class AgentReadinessRequest(BaseModel):
    project_id: str


class AgentReadinessResponse(BaseModel):
    project_id: str
    ready: bool
    score: int
    summary: str
