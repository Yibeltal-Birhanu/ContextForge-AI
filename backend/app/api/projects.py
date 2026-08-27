from fastapi import APIRouter, HTTPException

from app.schemas.pipeline import (
    StartProjectRequest,
    ContinueProjectRequest,
)
from app.schemas.context_improvement import (
    ImproveContextRequest,
)

from app.services.project_pipeline import (
    start_project,
    continue_project,
)
from app.services.context_improvement import (
    improve_project_context,
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


@router.post("/improve")
async def improve(
    request: ImproveContextRequest,
):
    try:
        result = await improve_project_context(
            project_data=request.project,
            answers=request.answers,
            quality_checks=request.quality_checks,
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
