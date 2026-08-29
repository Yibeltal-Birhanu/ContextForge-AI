import json
from uuid import uuid4
from datetime import datetime
from typing import Optional

from app.database import get_db


def create_project(
    name: str,
    idea: str,
    description: str = "",
    project_data: dict = None,
) -> dict:
    """Create a new project."""
    project_id = str(uuid4())
    now = datetime.utcnow().isoformat()

    conn = get_db()
    conn.execute(
        """INSERT INTO projects (id, name, idea, description, status, current_stage, project_data, created_at, updated_at)
           VALUES (?, ?, ?, ?, 'discovery', 'discovery', ?, ?, ?)""",
        (project_id, name, idea, description, json.dumps(project_data or {}), now, now),
    )
    conn.commit()

    project = get_project(project_id)
    conn.close()
    return project


def get_project(project_id: str) -> Optional[dict]:
    """Get a project by ID."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM projects WHERE id = ?", (project_id,)
    ).fetchone()
    conn.close()

    if not row:
        return None

    return _row_to_dict(row)


def list_projects() -> list[dict]:
    """List all projects, newest first."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM projects ORDER BY updated_at DESC"
    ).fetchall()
    conn.close()

    return [_row_to_dict(row) for row in rows]


def update_project(
    project_id: str,
    name: str = None,
    idea: str = None,
    description: str = None,
    status: str = None,
    current_stage: str = None,
    project_data: dict = None,
) -> Optional[dict]:
    """Update a project."""
    conn = get_db()
    now = datetime.utcnow().isoformat()

    updates = []
    params = []

    if name is not None:
        updates.append("name = ?")
        params.append(name)
    if idea is not None:
        updates.append("idea = ?")
        params.append(idea)
    if description is not None:
        updates.append("description = ?")
        params.append(description)
    if status is not None:
        updates.append("status = ?")
        params.append(status)
    if current_stage is not None:
        updates.append("current_stage = ?")
        params.append(current_stage)
    if project_data is not None:
        updates.append("project_data = ?")
        params.append(json.dumps(project_data))

    if not updates:
        conn.close()
        return get_project(project_id)

    updates.append("updated_at = ?")
    params.append(now)
    params.append(project_id)

    conn.execute(
        f"UPDATE projects SET {', '.join(updates)} WHERE id = ?",
        params,
    )
    conn.commit()

    project = get_project(project_id)
    conn.close()
    return project


def delete_project(project_id: str) -> bool:
    """Delete a project and all associated data."""
    conn = get_db()
    cursor = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


# ============================================================
# Context operations
# ============================================================


def save_context(
    project_id: str,
    requirements: dict = None,
    architecture: dict = None,
    implementation_context: dict = None,
    validation_result: dict = None,
    readiness_result: dict = None,
    quality_result: dict = None,
) -> None:
    """Save or update project context."""
    conn = get_db()
    now = datetime.utcnow().isoformat()

    existing = conn.execute(
        "SELECT id FROM project_contexts WHERE project_id = ?",
        (project_id,),
    ).fetchone()

    if existing:
        updates = []
        params = []
        if requirements is not None:
            updates.append("requirements = ?")
            params.append(json.dumps(requirements))
        if architecture is not None:
            updates.append("architecture = ?")
            params.append(json.dumps(architecture))
        if implementation_context is not None:
            updates.append("implementation_context = ?")
            params.append(json.dumps(implementation_context))
        if validation_result is not None:
            updates.append("validation_result = ?")
            params.append(json.dumps(validation_result))
        if readiness_result is not None:
            updates.append("readiness_result = ?")
            params.append(json.dumps(readiness_result))
        if quality_result is not None:
            updates.append("quality_result = ?")
            params.append(json.dumps(quality_result))

        if updates:
            updates.append("updated_at = ?")
            params.append(now)
            params.append(project_id)
            conn.execute(
                f"UPDATE project_contexts SET {', '.join(updates)} WHERE project_id = ?",
                params,
            )
    else:
        conn.execute(
            """INSERT INTO project_contexts
               (project_id, requirements, architecture, implementation_context, validation_result, readiness_result, quality_result, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                project_id,
                json.dumps(requirements) if requirements else None,
                json.dumps(architecture) if architecture else None,
                json.dumps(implementation_context) if implementation_context else None,
                json.dumps(validation_result) if validation_result else None,
                json.dumps(readiness_result) if readiness_result else None,
                json.dumps(quality_result) if quality_result else None,
                now,
            ),
        )

    conn.commit()
    conn.close()


def get_context(project_id: str) -> Optional[dict]:
    """Get project context."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM project_contexts WHERE project_id = ?",
        (project_id,),
    ).fetchone()
    conn.close()

    if not row:
        return None

    return {
        "project_id": row["project_id"],
        "requirements": json.loads(row["requirements"]) if row["requirements"] else None,
        "architecture": json.loads(row["architecture"]) if row["architecture"] else None,
        "implementation_context": json.loads(row["implementation_context"]) if row["implementation_context"] else None,
        "validation_result": json.loads(row["validation_result"]) if row["validation_result"] else None,
        "readiness_result": json.loads(row["readiness_result"]) if row["readiness_result"] else None,
        "quality_result": json.loads(row["quality_result"]) if row["quality_result"] else None,
        "updated_at": row["updated_at"],
    }


# ============================================================
# Artifact operations
# ============================================================


def save_artifact(
    project_id: str,
    markdown: str,
    txt: str,
    quality_score: int = 0,
) -> dict:
    """Save a project artifact."""
    artifact_id = str(uuid4())
    now = datetime.utcnow().isoformat()

    conn = get_db()
    conn.execute(
        """INSERT INTO project_artifacts (id, project_id, markdown, txt, quality_score, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (artifact_id, project_id, markdown, txt, quality_score, now),
    )
    conn.commit()
    conn.close()

    return {
        "id": artifact_id,
        "project_id": project_id,
        "quality_score": quality_score,
        "created_at": now,
    }


def get_artifacts(project_id: str) -> list[dict]:
    """Get all artifacts for a project."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM project_artifacts WHERE project_id = ? ORDER BY created_at DESC",
        (project_id,),
    ).fetchall()
    conn.close()

    return [
        {
            "id": row["id"],
            "project_id": row["project_id"],
            "quality_score": row["quality_score"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def get_artifact_content(artifact_id: str) -> Optional[dict]:
    """Get full artifact content (markdown + txt)."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM project_artifacts WHERE id = ?",
        (artifact_id,),
    ).fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row["id"],
        "project_id": row["project_id"],
        "markdown": row["markdown"],
        "txt": row["txt"],
        "quality_score": row["quality_score"],
        "created_at": row["created_at"],
    }


def get_latest_artifact(project_id: str) -> Optional[dict]:
    """Get the most recent artifact for a project."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM project_artifacts WHERE project_id = ? ORDER BY created_at DESC LIMIT 1",
        (project_id,),
    ).fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row["id"],
        "project_id": row["project_id"],
        "markdown": row["markdown"],
        "txt": row["txt"],
        "quality_score": row["quality_score"],
        "created_at": row["created_at"],
    }# ============================================================
# State save/resume (for discovery continuation)
# ============================================================


def save_project_state(
    project_id: str,
    project_data: dict,
    status: str = None,
    current_stage: str = None,
    name: str = None,
) -> Optional[dict]:
    """Save full project state after each pipeline step.

    This allows resuming a project that was interrupted mid-discovery.
    """
    return update_project(
        project_id=project_id,
        name=name,
        status=status,
        current_stage=current_stage,
        project_data=project_data,
    )


def get_project_state(project_id: str) -> Optional[dict]:
    """Get the saved project state for resumption."""
    project = get_project(project_id)
    if not project:
        return None
    return {
        "project": project,
        "project_data": project.get("project_data") or {},
        "status": project.get("status"),
        "current_stage": project.get("current_stage"),
    }


# ============================================================
# Helpers
# ============================================================

def _row_to_dict(row) -> dict:
    """Convert a sqlite3.Row to a dict."""
    data = dict(row)
    if data.get("project_data"):
        data["project_data"] = json.loads(data["project_data"])
    return data
