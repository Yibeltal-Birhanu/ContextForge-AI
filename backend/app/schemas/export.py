from pydantic import BaseModel


class ExportRequest(BaseModel):
    project_id: str


class ExportResponse(BaseModel):
    project_id: str
    project_name: str
    validation_score: int
    valid: bool
