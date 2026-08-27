from app.models.project import ProjectState
from app.models.pipeline import PipelineResult, PipelineStage, QualityInfo

from app.engines.discovery import apply_answers
from app.engines.requirements import generate_requirements
from app.engines.architecture import generate_architecture
from app.engines.context import generate_context
from app.engines.context_improvement import improve_context
from app.engines.artifact import create_artifact
from app.services.quality_gate import run_quality_gate


async def improve_project_context(
    project_data: dict,
    answers: dict,
    quality_checks: dict,
) -> PipelineResult:
    """
    Improve an existing context based on quality feedback.

    1. Reconstruct ProjectState from the project data
    2. Apply any new answers from the user
    3. Regenerate requirements, architecture, context
    4. Run targeted improvement on weak areas
    5. Revalidate
    6. Create artifact if quality gate passes
    """

    # Reconstruct project
    project = ProjectState(**project_data)

    # Apply any new answers
    if answers:
        answer_list = [
            {"field": field, "answer": str(value)}
            for field, value in answers.items()
        ]
        project = await apply_answers(project, answer_list)

    # Regenerate pipeline outputs
    requirements = await generate_requirements(project)
    architecture = await generate_architecture(project, requirements)
    base_context = await generate_context(project, requirements, architecture)

    # Run targeted improvement
    improved_context = await improve_context(
        project, requirements, architecture,
        base_context, quality_checks,
    )

    # Revalidate
    quality_gate = run_quality_gate(
        project, requirements, architecture, improved_context,
    )

    quality_info = QualityInfo(
        overall_score=quality_gate.overall_score,
        validation_score=quality_gate.validation_score,
        readiness_score=quality_gate.readiness_score,
        ready_for_agent=quality_gate.ready_for_agent,
        checks=quality_gate.checks,
        warnings_count=len(quality_gate.warnings),
        assumptions_count=len(quality_gate.assumptions),
        warnings=quality_gate.warnings,
        assumptions=quality_gate.assumptions,
        errors=quality_gate.errors,
        rejection_reasons=quality_gate.rejection_reasons,
    )

    # If still failing, return without artifact
    if not quality_gate.passed:
        return PipelineResult(
            stage=PipelineStage.VALIDATION,
            complete=False,
            project=project,
            quality=quality_info,
        )

    # Quality gate passed — create artifact
    from app.models.validation import ContextValidationResult
    validation = ContextValidationResult(
        valid=True,
        score=quality_gate.validation_score,
    )

    artifact = create_artifact(
        context=improved_context,
        validation=validation,
    )

    return PipelineResult(
        stage=PipelineStage.COMPLETE,
        complete=True,
        project=project,
        project_id=artifact.project_id,
        download_markdown=f"/export/{artifact.project_id}/markdown",
        download_txt=f"/export/{artifact.project_id}/txt",
        quality=quality_info,
    )
