from app.ai.openrouter import generate_structured
from app.models.project import ProjectState
from app.models.requirements import RequirementsDocument
from app.prompts.requirements import REQUIREMENTS_SYSTEM_PROMPT


async def generate_requirements(
    project: ProjectState,
) -> RequirementsDocument:

    user_message = f"""
ProjectState:

{project.model_dump_json(indent=2)}

Transform this project into an implementation-ready
requirements specification.
"""

    result = await generate_structured(
        system_prompt=REQUIREMENTS_SYSTEM_PROMPT,
        user_message=user_message,
    )

    return RequirementsDocument(**result)
