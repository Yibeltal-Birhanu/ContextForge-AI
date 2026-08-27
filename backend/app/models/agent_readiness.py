from pydantic import BaseModel, Field
from typing import List, Optional


class ReadinessWarning(BaseModel):
    category: str
    message: str


class ReadinessAssumption(BaseModel):
    area: str
    assumption: str
    severity: str  # "info", "warning", "critical"


class CheckScores(BaseModel):
    requirements_coverage: int = Field(ge=0, le=100)
    architecture_consistency: int = Field(ge=0, le=100)
    technology_consistency: int = Field(ge=0, le=100)
    api_coverage: int = Field(ge=0, le=100)
    data_model_coverage: int = Field(ge=0, le=100)
    security_coverage: int = Field(ge=0, le=100)
    implementation_coverage: int = Field(ge=0, le=100)
    agent_rules_quality: int = Field(ge=0, le=100)
    definition_of_done: int = Field(ge=0, le=100)


class AgentReadinessResult(BaseModel):
    ready: bool
    score: int = Field(ge=0, le=100)
    checks: CheckScores
    errors: List[str] = Field(default_factory=list)
    warnings: List[ReadinessWarning] = Field(default_factory=list)
    assumptions: List[ReadinessAssumption] = Field(default_factory=list)
