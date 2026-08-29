from pydantic import BaseModel, Field
from typing import Optional, List


class UserSelectedTechnology(BaseModel):
    """A technology explicitly selected by the user during discovery.

    Unlike AI-selected technologies (which may be freely chosen by the
    architecture engine), user-selected technologies MUST be preserved
    through Requirements -> Architecture -> Context without substitution.
    """
    name: str
    purpose: str = ""
    category: str = ""  # e.g. AI_PROVIDER, PAYMENT_PROVIDER, etc.
    status: str = "MVP_REQUIRED"  # MVP_REQUIRED, FUTURE, ALTERNATIVE, or EXCLUDED


class ProjectState(BaseModel):

    name: Optional[str] = None

    description: Optional[str] = None

    problem: Optional[str] = None

    target_users: List[str] = Field(default_factory=list)

    core_features: List[str] = Field(default_factory=list)

    platform: Optional[str] = None

    technologies: List[str] = Field(default_factory=list)

    # Technologies explicitly selected by the user (not inferred by AI).
    # These MUST be preserved through the entire pipeline.
    user_selected_technologies: List[UserSelectedTechnology] = Field(
        default_factory=list
    )

    database: Optional[str] = None

    authentication: Optional[str] = None

    integrations: List[str] = Field(default_factory=list)

    constraints: List[str] = Field(default_factory=list)

    deployment: Optional[str] = None
