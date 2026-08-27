from app.ai.openrouter import generate_structured

from app.models.project import ProjectState
from app.models.requirements import RequirementsDocument
from app.models.architecture import ArchitectureDocument
from app.models.context import ImplementationContext

from app.prompts.context import CONTEXT_ENGINEERING_SYSTEM_PROMPT


async def generate_context(
    project: ProjectState,
    requirements: RequirementsDocument,
    architecture: ArchitectureDocument,
) -> ImplementationContext:

    user_message = f"""
PROJECT STATE:

{project.model_dump_json(indent=2)}


REQUIREMENTS:

{requirements.model_dump_json(indent=2)}


ARCHITECTURE:

{architecture.model_dump_json(indent=2)}


Create the final implementation context for an AI coding agent.
"""

    result = await generate_structured(
        system_prompt=CONTEXT_ENGINEERING_SYSTEM_PROMPT,
        user_message=user_message,
    )

    return ImplementationContext(**result)
