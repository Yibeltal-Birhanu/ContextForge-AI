from app.ai.openrouter import generate_structured
from app.models.project import ProjectState
from app.models.requirements import RequirementsDocument
from app.models.architecture import ArchitectureDocument
from app.prompts.architecture import ARCHITECTURE_SYSTEM_PROMPT


async def generate_architecture(
    project: ProjectState,
    requirements: RequirementsDocument,
) -> ArchitectureDocument:

    user_message = f"""
PROJECT STATE:

{project.model_dump_json(indent=2)}


REQUIREMENTS:

{requirements.model_dump_json(indent=2)}


Design the technical architecture for this project.
"""

    result = await generate_structured(
        system_prompt=ARCHITECTURE_SYSTEM_PROMPT,
        user_message=user_message,
    )

    return ArchitectureDocument(**result)
