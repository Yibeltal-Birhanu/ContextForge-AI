from app.models.project import ProjectState
from app.models.pipeline import PipelineResult, PipelineStage

from app.engines.discovery import (
    understand_project,
    find_missing_fields,
    generate_questions,
    apply_answers,
)
from app.engines.requirements import generate_requirements
from app.engines.architecture import generate_architecture
from app.engines.context import generate_context
from app.engines.validation import validate_context
from app.engines.artifact import create_artifact


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

    validation = validate_context(
        project,
        requirements,
        architecture,
        context,
    )

    if not validation.valid:

        return PipelineResult(
            stage=PipelineStage.VALIDATION,
            complete=False,
            project=project,
            missing_fields=["validation_failed"],
            questions=[],
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
    )
