from uuid import uuid4

from app.models.context import ImplementationContext
from app.models.validation import ContextValidationResult
from app.models.artifact import ContextArtifact

from app.engines.assembly import assemble_markdown
from app.services.artifact_store import save_artifact


def create_artifact(
    context: ImplementationContext,
    validation: ContextValidationResult,
) -> ContextArtifact:

    if not validation.valid:
        raise ValueError(
            "Cannot create artifact from invalid context."
        )

    markdown = assemble_markdown(
        context=context,
        validation=validation,
    )

    artifact = ContextArtifact(
        project_id=str(uuid4()),
        project_name=context.project_title,
        markdown=markdown,
        text=markdown,
        validation_score=validation.score,
        valid=validation.valid,
    )

    save_artifact(artifact)

    return artifact
