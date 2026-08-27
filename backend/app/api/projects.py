from fastapi import APIRouter, HTTPException

from app.schemas.pipeline import (
    StartProjectRequest,
    ContinueProjectRequest,
)

from app.services.project_pipeline import (
    start_project,
    continue_project,
)

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
)


@router.post("/start")
async def start(
    request: StartProjectRequest,
):
    try:
        result = await start_project(
            request.idea,
        )
        return result.model_dump()
    except RuntimeError as e:
        error_msg = str(e)
        if "429" in error_msg:
            raise HTTPException(
                status_code=429,
                detail="AI service rate limit exceeded. Please wait a moment and try again.",
            )
        raise HTTPException(
            status_code=500,
            detail=f"AI service error: {error_msg}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}",
        )


@router.post("/continue")
async def continue_(
    request: ContinueProjectRequest,
):
    try:
        result = await continue_project(
            request.project,
            request.answers,
        )
        return result.model_dump()
    except RuntimeError as e:
        error_msg = str(e)
        if "429" in error_msg:
            raise HTTPException(
                status_code=429,
                detail="AI service rate limit exceeded. Please wait a moment and try again.",
            )
        raise HTTPException(
            status_code=500,
            detail=f"AI service error: {error_msg}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}",
        )
