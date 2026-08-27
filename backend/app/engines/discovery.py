from app.ai.openrouter import generate_structured
from app.models.project import ProjectState
from app.prompts.discovery import PROJECT_DISCOVERY_SYSTEM_PROMPT
from app.prompts.questions import QUESTION_GENERATION_SYSTEM_PROMPT
from app.prompts.answers import ANSWER_PROCESSING_SYSTEM_PROMPT


REQUIRED_FIELDS = [
    "name",
    "description",
    "problem",
    "target_users",
    "core_features",
    "platform",
    "technologies",
    "database",
    "authentication",
    "integrations",
    "constraints",
    "deployment",
]


def find_missing_fields(project: ProjectState) -> list[str]:

    missing = []

    for field in REQUIRED_FIELDS:

        value = getattr(project, field)

        if value is None:
            missing.append(field)
        elif isinstance(value, list) and len(value) == 0:
            missing.append(field)

    return missing


async def understand_project(idea: str) -> ProjectState:

    result = await generate_structured(
        system_prompt=PROJECT_DISCOVERY_SYSTEM_PROMPT,
        user_message=idea
    )

    return ProjectState(**result)


async def generate_questions(
    project: ProjectState,
    missing_fields: list[str]
) -> list[dict]:

    user_message = f"""
Current project state:

{project.model_dump_json(indent=2)}

Missing fields:

{missing_fields}

Generate the most important questions that should be asked next.
"""

    result = await generate_structured(
        system_prompt=QUESTION_GENERATION_SYSTEM_PROMPT,
        user_message=user_message
    )

    return result["questions"]


async def apply_answers(
    project: ProjectState,
    answers: list[dict]
) -> ProjectState:

    user_message = f"""
Current ProjectState:

{project.model_dump_json(indent=2)}

User answers:

{answers}

Update the ProjectState using these answers.
"""

    result = await generate_structured(
        system_prompt=ANSWER_PROCESSING_SYSTEM_PROMPT,
        user_message=user_message
    )

    return ProjectState(**result)
