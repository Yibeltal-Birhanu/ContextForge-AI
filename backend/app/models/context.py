from pydantic import BaseModel, Field
from typing import List


class ImplementationPhase(BaseModel):
    phase: int
    name: str
    objective: str
    tasks: List[str] = Field(default_factory=list)
    deliverables: List[str] = Field(default_factory=list)


class AgentRule(BaseModel):
    category: str
    rule: str


class ImplementationContext(BaseModel):

    project_title: str

    project_summary: str

    problem: str

    target_users: List[str] = Field(
        default_factory=list
    )

    functional_requirements: List[str] = Field(
        default_factory=list
    )

    non_functional_requirements: List[str] = Field(
        default_factory=list
    )

    architecture_summary: str

    technology_stack: List[str] = Field(
        default_factory=list
    )

    data_model: List[str] = Field(
        default_factory=list
    )

    api_contract: List[str] = Field(
        default_factory=list
    )

    security_requirements: List[str] = Field(
        default_factory=list
    )

    implementation_phases: List[ImplementationPhase] = Field(
        default_factory=list
    )

    agent_rules: List[AgentRule] = Field(
        default_factory=list
    )

    definition_of_done: List[str] = Field(
        default_factory=list
    )
