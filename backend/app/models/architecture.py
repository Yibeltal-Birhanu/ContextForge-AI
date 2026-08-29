from pydantic import BaseModel, Field
from typing import List


class ArchitectureComponent(BaseModel):
    name: str
    responsibility: str
    technologies: List[str] = Field(default_factory=list)


class TechnologyChoice(BaseModel):
    category: str
    technology: str
    reason: str
    status: str = "MVP_REQUIRED"


class DataEntity(BaseModel):
    name: str
    purpose: str
    important_fields: List[str] = Field(default_factory=list)


class APIGroup(BaseModel):
    name: str
    purpose: str
    endpoints: List[str] = Field(default_factory=list)


class SecurityDecision(BaseModel):
    area: str
    decision: str
    reason: str


class DeploymentPlan(BaseModel):
    environment: str
    services: List[str] = Field(default_factory=list)
    reason: str


class ArchitectureDocument(BaseModel):

    system_architecture: str

    components: List[ArchitectureComponent] = Field(
        default_factory=list
    )

    technology_stack: List[TechnologyChoice] = Field(
        default_factory=list
    )

    data_architecture: List[DataEntity] = Field(
        default_factory=list
    )

    api_design: List[APIGroup] = Field(
        default_factory=list
    )

    security: List[SecurityDecision] = Field(
        default_factory=list
    )

    deployment: List[DeploymentPlan] = Field(
        default_factory=list
    )
