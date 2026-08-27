from pydantic import BaseModel, Field
from typing import List


class AcceptanceCriterion(BaseModel):
    description: str


class Requirement(BaseModel):

    id: str

    title: str

    description: str

    priority: str

    actors: List[str] = Field(default_factory=list)

    acceptance_criteria: List[AcceptanceCriterion] = Field(
        default_factory=list
    )


class RequirementsDocument(BaseModel):

    functional_requirements: List[Requirement] = Field(
        default_factory=list
    )

    non_functional_requirements: List[Requirement] = Field(
        default_factory=list
    )
