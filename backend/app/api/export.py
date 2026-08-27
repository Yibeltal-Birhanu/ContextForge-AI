from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.schemas.export import (
    ExportRequest,
    ExportResponse,
)

from app.services.artifact_store import (
    save_artifact,
    get_artifact,
)

router = APIRouter(
    prefix="/export",
    tags=["export"],
)


@router.post(
    "",
    response_model=ExportResponse,
)
def register_artifact(
    request: ExportRequest,
):

    artifact = get_artifact(
        request.project_id
    )

    if artifact is None:
        raise HTTPException(
            status_code=404,
            detail="Artifact not found.",
        )

    return ExportResponse(
        project_id=artifact.project_id,
        project_name=artifact.project_name,
        validation_score=artifact.validation_score,
        valid=artifact.valid,
    )


@router.get(
    "/{project_id}/markdown"
)
def download_markdown(
    project_id: str,
):

    artifact = get_artifact(
        project_id
    )

    if artifact is None:
        raise HTTPException(
            status_code=404,
            detail="Artifact not found.",
        )

    filename = (
        f"{artifact.project_name}"
        .replace(" ", "_")
        + ".md"
    )

    return Response(
        content=artifact.markdown,
        media_type="text/markdown",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            )
        },
    )


@router.get(
    "/{project_id}/txt"
)
def download_text(
    project_id: str,
):

    artifact = get_artifact(
        project_id
    )

    if artifact is None:
        raise HTTPException(
            status_code=404,
            detail="Artifact not found.",
        )

    filename = (
        f"{artifact.project_name}"
        .replace(" ", "_")
        + ".txt"
    )

    return Response(
        content=artifact.text,
        media_type="text/plain",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            )
        },
    )
