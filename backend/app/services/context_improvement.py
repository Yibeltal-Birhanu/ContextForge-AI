from app.models.project import ProjectState
from app.models.pipeline import PipelineResult, PipelineStage, QualityInfo

from app.engines.discovery import apply_answers
from app.engines.requirements import generate_requirements
from app.engines.architecture import generate_architecture
from app.engines.context import generate_context
from app.engines.context_improvement import improve_context
from app.engines.artifact import create_artifact
from app.services.quality_gate import run_quality_gate
from app.services import project_store
from app.utils.tech_normalizer import (
    normalize_tech_name,
    normalize_tech_list,
    dedupe_technology_strings,
)


async def improve_project_context(
    project_data: dict,
    answers: dict,
    quality_checks: dict,
    project_id: str | None = None,
) -> PipelineResult:
    """
    Improve an existing context based on quality feedback.

    1. Reconstruct ProjectState from the project data
    2. Apply any new answers from the user
    3. Regenerate requirements, architecture, context
    4. Run targeted improvement on weak areas
    5. Revalidate
    6. Persist context and quality
    7. Create artifact if quality gate passes
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

    inactive = {
        normalize_tech_name(selected.name)
        for selected in project.user_selected_technologies
        if selected.status in {"FUTURE", "ALTERNATIVE", "EXCLUDED"}
    }
    improved_context.technology_stack = [
        technology for technology in improved_context.technology_stack
        if normalize_tech_name(technology) not in inactive
    ]
    improved_context.technology_stack = dedupe_technology_strings(
        improved_context.technology_stack
    )
    unique_techs = []
    seen_techs = set()
    for technology in improved_context.technology_stack:
        normalized = normalize_tech_name(technology)
        if normalized and normalized not in seen_techs:
            unique_techs.append(technology)
            seen_techs.add(normalized)
    improved_context.technology_stack = unique_techs
    context_techs = normalize_tech_list(improved_context.technology_stack)
    for selected in project.user_selected_technologies:
        if selected.status != "MVP_REQUIRED":
            continue
        selected_norm = normalize_tech_name(selected.name)
        if selected_norm and selected_norm not in context_techs:
            improved_context.technology_stack.append(selected.name)
            context_techs.add(selected_norm)

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

    if project_id:
        saved = project_store.get_context(project_id)
        saved_quality = (saved or {}).get("quality_result") or {}
        saved_score = saved_quality.get("overall_score")
        if (
            saved_score is not None
            and quality_info.overall_score < saved_score
            and saved.get("implementation_context")
        ):
            saved_artifact = project_store.get_latest_artifact(project_id)
            return PipelineResult(
                stage=(
                    PipelineStage.COMPLETE
                    if saved_artifact and saved_quality.get("ready_for_agent")
                    else PipelineStage.VALIDATION
                ),
                complete=bool(saved_artifact and saved_quality.get("ready_for_agent")),
                project=project,
                project_id=saved_artifact["id"] if saved_artifact else None,
                download_markdown=(
                    f"/export/{saved_artifact['id']}/markdown"
                    if saved_artifact else None
                ),
                download_txt=(
                    f"/export/{saved_artifact['id']}/txt"
                    if saved_artifact else None
                ),
                quality=QualityInfo(**saved_quality),
            )

    # Persist context and quality even if quality gate fails,
    # so the improved context is not lost.
    if project_id:
        project_store.save_context(
            project_id=project_id,
            requirements=requirements.model_dump(),
            architecture=architecture.model_dump(),
            implementation_context=improved_context.model_dump(),
            quality_result=quality_info.model_dump(),
        )
        # Update project state
        project_store.update_project(
            project_id,
            name=project.name or "Untitled Project",
            project_data=project.model_dump(),
            current_stage="improvement",
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

    if project_id:
        from app.engines.assembly import assemble_markdown
        markdown = assemble_markdown(
            context=improved_context,
            validation=validation,
        )
        stored = project_store.save_artifact(
            project_id=project_id,
            markdown=markdown,
            txt=markdown,
            quality_score=quality_gate.overall_score,
        )
        project_store.update_project(
            project_id,
            status="complete",
            current_stage="complete",
        )
        artifact_id = stored["id"]
    else:
        artifact = create_artifact(
            context=improved_context,
            validation=validation,
        )
        artifact_id = artifact.project_id

    return PipelineResult(
        stage=PipelineStage.COMPLETE,
        complete=True,
        project=project,
        project_id=artifact_id,
        download_markdown=f"/export/{artifact_id}/markdown",
        download_txt=f"/export/{artifact_id}/txt",
        quality=quality_info,
    )
