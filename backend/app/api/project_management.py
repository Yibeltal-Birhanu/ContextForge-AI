from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.project_store import (
    create_project,
    get_project,
    list_projects,
    update_project,
    delete_project,
    get_context,
    get_artifacts,
    get_latest_artifact,
)

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
)


# ============================================================
# Request/Response schemas
# ============================================================


class CreateProjectRequest(BaseModel):
    name: str
    idea: str
    description: str = ""


class UpdateProjectRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    current_stage: Optional[str] = None
    project_data: Optional[dict] = None


# ============================================================
# CRUD endpoints
# ============================================================


@router.get("")
async def list_all_projects():
    """List all projects."""
    try:
        projects = list_projects()
        return {"projects": projects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_new_project(request: CreateProjectRequest):
    """Create a new project."""
    try:
        project = create_project(
            name=request.name,
            idea=request.idea,
            description=request.description,
        )
        return project
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}")
async def get_project_detail(project_id: str):
    """Get a project with full details."""
    try:
        project = get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found.")

        context = get_context(project_id)
        artifacts = get_artifacts(project_id)
        latest_artifact = get_latest_artifact(project_id)

        return {
            "project": project,
            "context": context,
            "artifacts": artifacts,
            "latest_artifact": {
                "id": latest_artifact["id"],
                "quality_score": latest_artifact["quality_score"],
                "created_at": latest_artifact["created_at"],
            } if latest_artifact else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{project_id}")
async def update_project_detail(project_id: str, request: UpdateProjectRequest):
    """Update a project."""
    try:
        existing = get_project(project_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Project not found.")

        updated = update_project(
            project_id=project_id,
            name=request.name,
            description=request.description,
            status=request.status,
            current_stage=request.current_stage,
            project_data=request.project_data,
        )
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}")
async def delete_project_detail(project_id: str):
    """Delete a project and all associated data."""
    try:
        existing = get_project(project_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Project not found.")

        delete_project(project_id)
        return {"message": "Project deleted.", "project_id": project_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Context & artifact endpoints
# ============================================================


@router.get("/{project_id}/context")
async def get_project_context(project_id: str):
    """Get the full context for a project."""
    try:
        project = get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found.")

        context = get_context(project_id)
        if not context:
            raise HTTPException(status_code=404, detail="No context found for this project.")

        return context
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/artifacts")
async def get_project_artifacts(project_id: str):
    """Get all artifacts for a project."""
    try:
        project = get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found.")

        artifacts = get_artifacts(project_id)
        return {"artifacts": artifacts}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
