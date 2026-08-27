from pydantic import BaseModel
from typing import List


class DiscoveryRequest(BaseModel):

    idea: str


class DiscoveryQuestion(BaseModel):
    field: str
    question: str
    reason: str


class DiscoveryQuestionsResponse(BaseModel):
    questions: List[DiscoveryQuestion]


class DiscoveryStartResponse(BaseModel):
    project: dict
    missing_fields: list[str]
    questions: list[DiscoveryQuestion]


class DiscoveryAnswer(BaseModel):
    field: str
    answer: str


class DiscoveryContinueRequest(BaseModel):
    project: dict
    answers: list[DiscoveryAnswer]


class DiscoveryContinueResponse(BaseModel):
    project: dict
    missing_fields: list[str]
    questions: list[DiscoveryQuestion]
    complete: bool
