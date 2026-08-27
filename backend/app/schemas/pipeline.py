from pydantic import BaseModel


class StartProjectRequest(BaseModel):
    idea: str


class ContinueProjectRequest(BaseModel):
    project: dict
    answers: dict
