from pydantic import BaseModel, Field
from typing import List


class ValidationIssue(BaseModel):
    category: str
    severity: str
    message: str


class ContextValidationResult(BaseModel):
    valid: bool

    score: int = Field(
        ge=0,
        le=100
    )

    issues: List[ValidationIssue] = Field(
        default_factory=list
    )
