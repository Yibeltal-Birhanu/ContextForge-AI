from app.models.artifact import ContextArtifact


_artifacts: dict[str, ContextArtifact] = {}


def save_artifact(artifact: ContextArtifact) -> None:
    _artifacts[artifact.project_id] = artifact


def get_artifact(project_id: str) -> ContextArtifact | None:
    return _artifacts.get(project_id)
