from pydantic import BaseModel


class StartProjectRequest(BaseModel):
    idea: str
    project_id: str | None = None


class ContinueProjectRequest(BaseModel):
    project: dict
    answers: dict
    conversation_history: list[dict] = []
    project_id: str | None = None
