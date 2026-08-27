from pydantic import BaseModel, Field
from typing import Optional, List


class ProjectState(BaseModel):

    name: Optional[str] = None

    description: Optional[str] = None

    problem: Optional[str] = None

    target_users: List[str] = Field(default_factory=list)

    core_features: List[str] = Field(default_factory=list)

    platform: Optional[str] = None

    technologies: List[str] = Field(default_factory=list)

    database: Optional[str] = None

    authentication: Optional[str] = None

    integrations: List[str] = Field(default_factory=list)

    constraints: List[str] = Field(default_factory=list)

    deployment: Optional[str] = None
