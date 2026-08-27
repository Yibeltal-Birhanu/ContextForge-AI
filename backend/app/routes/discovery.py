from fastapi import APIRouter

from app.models.project import ProjectState
from app.schemas.discovery import (
    DiscoveryRequest,
    DiscoveryStartResponse,
    DiscoveryQuestion,
    DiscoveryContinueRequest,
    DiscoveryContinueResponse,
)

from app.engines.discovery import (
    understand_project,
    find_missing_fields,
    generate_questions,
    apply_answers,
)


router = APIRouter(
    prefix="/discovery",
    tags=["discovery"],
)


@router.post(
    "/start",
    response_model=DiscoveryStartResponse,
)
async def start_discovery(
    request: DiscoveryRequest,
):

    project = await understand_project(request.idea)

    missing_fields = find_missing_fields(project)

    questions = await generate_questions(
        project,
        missing_fields,
    )

    return DiscoveryStartResponse(
        project=project.model_dump(),
        missing_fields=missing_fields,
        questions=[
            DiscoveryQuestion(**question)
            for question in questions
        ],
    )


@router.post(
    "/continue",
    response_model=DiscoveryContinueResponse,
)
async def continue_discovery(
    request: DiscoveryContinueRequest,
):

    project = ProjectState(**request.project)

    answers = [
        answer.model_dump()
        for answer in request.answers
    ]

    updated_project = await apply_answers(
        project,
        answers,
    )

    missing_fields = find_missing_fields(
        updated_project
    )

    complete = len(missing_fields) == 0

    questions = []

    if not complete:
        questions = await generate_questions(
            updated_project,
            missing_fields,
        )

    return DiscoveryContinueResponse(
        project=updated_project.model_dump(),
        missing_fields=missing_fields,
        questions=[
            DiscoveryQuestion(**question)
            for question in questions
        ],
        complete=complete,
    )
