from app.models.project import ProjectState
from app.models.pipeline import PipelineResult, PipelineStage, QualityInfo

from app.engines.discovery import (
    understand_project,
    find_missing_fields,
    generate_questions,
    apply_answers,
)
from app.engines.requirements import generate_requirements
from app.engines.architecture import generate_architecture
from app.engines.context import generate_context
from app.engines.artifact import create_artifact
from app.services.quality_gate import run_quality_gate
from app.services import project_store


async def start_project(
    idea: str,
) -> PipelineResult:

    project = await understand_project(idea)

    missing_fields = find_missing_fields(project)

    if missing_fields:

        questions = await generate_questions(
            project,
            missing_fields,
        )

        return PipelineResult(
            stage=PipelineStage.DISCOVERY,
            complete=False,
            project=project,
            missing_fields=missing_fields,
            questions=questions,
        )

    return await _complete_pipeline(project)


async def continue_project(
    project_data: dict,
    answers: dict,
) -> PipelineResult:

    project = ProjectState(**project_data)

    answer_list = [
        {"field": field, "answer": str(value)}
        for field, value in answers.items()
    ]

    updated_project = await apply_answers(
        project,
        answer_list,
    )

    missing_fields = find_missing_fields(updated_project)

    if missing_fields:

        questions = await generate_questions(
            updated_project,
            missing_fields,
        )

        return PipelineResult(
            stage=PipelineStage.DISCOVERY,
            complete=False,
            project=updated_project,
            missing_fields=missing_fields,
            questions=questions,
        )

    return await _complete_pipeline(updated_project)


async def _complete_pipeline(
    project: ProjectState,
) -> PipelineResult:

    requirements = await generate_requirements(project)

    architecture = await generate_architecture(
        project,
        requirements,
    )

    context = await generate_context(
        project,
        requirements,
        architecture,
    )

    # Run quality gate (validation + agent readiness)
    quality_gate = run_quality_gate(
        project, requirements, architecture, context,
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

    # If quality gate fails, do not create artifact
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
        context=context,
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


# ============================================================
# Persistent pipeline functions
# ============================================================


async def start_persistent_project(
    project_id: str,
    idea: str,
) -> PipelineResult:
    """Start discovery and persist state to database."""

    # Update project with idea
    project_store.update_project(
        project_id,
        idea=idea,
        current_stage="discovery",
    )

    # Run discovery
    result = await start_project(idea)

    # Persist the project state
    if result.project:
        project_store.update_project(
            project_id,
            name=result.project.name or "Untitled Project",
            project_data=result.project.model_dump(),
        )

    return result


async def continue_persistent_project(
    project_id: str,
    project_data: dict,
    answers: dict,
) -> PipelineResult:
    """Continue discovery and persist state to database."""

    # Run continuation
    result = await continue_project(project_data, answers)

    # Persist updated project state
    if result.project:
        project_store.update_project(
            project_id,
            name=result.project.name or "Untitled Project",
            project_data=result.project.model_dump(),
            current_stage=result.stage.value,
        )

    # If complete, persist context and artifact
    if result.complete and result.project_id:
        project_store.update_project(
            project_id,
            status="complete",
            current_stage="complete",
        )

    return result


async def improve_persistent_project(
    project_id: str,
    project_data: dict,
    answers: dict,
    quality_checks: dict,
) -> PipelineResult:
    """Improve context and persist to database."""

    from app.services.context_improvement import improve_project_context

    result = await improve_project_context(
        project_data=project_data,
        answers=answers,
        quality_checks=quality_checks,
    )

    # Persist updated project state
    if result.project:
        project_store.update_project(
            project_id,
            name=result.project.name or "Untitled Project",
            project_data=result.project.model_dump(),
            current_stage=result.stage.value,
        )

    # If complete after improvement, persist
    if result.complete and result.project_id:
        project_store.update_project(
            project_id,
            status="complete",
            current_stage="complete",
        )

    return result
