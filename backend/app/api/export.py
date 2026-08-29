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
from app.services.project_store import get_artifact_content

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

    artifact = get_artifact(project_id) or get_artifact_content(project_id)

    if artifact is None:
        raise HTTPException(
            status_code=404,
            detail="Artifact not found.",
        )

    filename = f"contextforge_{project_id}.md"

    markdown = artifact.markdown if hasattr(artifact, "markdown") else artifact["markdown"]
    return Response(
        content=markdown,
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

    artifact = get_artifact(project_id) or get_artifact_content(project_id)

    if artifact is None:
        raise HTTPException(
            status_code=404,
            detail="Artifact not found.",
        )

    filename = f"contextforge_{project_id}.txt"

    text = artifact.text if hasattr(artifact, "text") else artifact["txt"]
    return Response(
        content=text,
        media_type="text/plain",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            )
        },
    )
