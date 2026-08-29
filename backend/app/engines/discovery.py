from app.ai.openrouter import generate_structured
from app.models.project import ProjectState, UserSelectedTechnology
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

    project = ProjectState(**result)
    project.user_selected_technologies = _sanitize_user_selected_technologies(
        project.user_selected_technologies
    )

    # ALWAYS extract technologies from the idea using pattern matching.
    # The LLM may miss some technologies or not extract them at all.
    idea_techs = _extract_technologies_from_text(idea)

    # Keep only recognized concrete technologies. LLM output can echo an
    # entire answer into the technologies field, so raw entries are unsafe.
    llm_techs = []
    for candidate in project.technologies or []:
        for tech in _extract_technologies_from_text(candidate):
            if tech not in llm_techs:
                llm_techs.append(tech)

    project.technologies = llm_techs
    existing_techs = set(t.lower() for t in project.technologies)
    for tech in idea_techs:
        if tech.lower() not in existing_techs:
            project.technologies.append(tech)
            existing_techs.add(tech.lower())

    if project.technologies:
        existing_ust = {t.name.lower() for t in project.user_selected_technologies}
        for tech in project.technologies:
            if tech.lower() not in existing_ust:
                project.user_selected_technologies.append(
                    UserSelectedTechnology(
                        name=tech,
                        purpose="user-specified in initial idea",
                        category=_classify_tech_for_extraction(tech),
                    )
                )
                existing_ust.add(tech.lower())

    return project


def _extract_technologies_from_text(text: str) -> list[str]:
    """Return only known concrete technology names found in free-form text."""
    from app.utils.tech_normalizer import TECH_ALIASES
    import re

    matches = []
    lowered = text.lower()
    occupied = []
    for alias, canonical in sorted(TECH_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        match = re.search(r"(?<![\w-])" + re.escape(alias) + r"(?![\w-])", lowered)
        if match and not any(match.start() < end and match.end() > start for start, end in occupied):
            if canonical not in matches:
                matches.append(canonical)
            occupied.append((match.start(), match.end()))
    return matches


def _extract_technologies_with_status(text: str) -> list[tuple[str, str]]:
    """Extract concrete technologies and infer lifecycle from nearby prose."""
    from app.utils.tech_normalizer import TECH_ALIASES
    import re

    found = []
    occupied = []
    for alias, canonical in sorted(TECH_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        match = re.search(r"(?<![\w-])" + re.escape(alias) + r"(?![\w-])", text.lower())
        if not match or any(match.start() < end and match.end() > start for start, end in occupied):
            continue
        sentence_start = max(
            text.rfind(marker, 0, match.start())
            for marker in (".", ";", "\n")
        ) + 1
        sentence_end_candidates = [
            position for marker in (".", ";", "\n")
            if (position := text.find(marker, match.end())) >= 0
        ]
        sentence_end = min(sentence_end_candidates, default=len(text))
        sentence = text[sentence_start:sentence_end].lower()
        status = "MVP_REQUIRED"
        if re.search(r"excluded|do not use|don't use|not using|not selected|out of scope|not required", sentence):
            status = "EXCLUDED"
        elif re.search(r"future|post[- ]mvp|later|phase 2", sentence):
            status = "FUTURE"
        elif re.search(r"alternative|alternatively|backup|or use", sentence):
            status = "ALTERNATIVE"
        if canonical not in {name for name, _ in found}:
            found.append((canonical, status))
        occupied.append((match.start(), match.end()))
    return found


def _classify_tech_for_extraction(tech_name: str) -> str:
    from app.utils.tech_normalizer import classify_tech
    return classify_tech(tech_name)


def _sanitize_user_selected_technologies(
    technologies: list[UserSelectedTechnology],
) -> list[UserSelectedTechnology]:
    """Keep only concrete aliases from model-produced technology entries."""
    sanitized = []
    seen = set()
    for technology in technologies:
        for name, status in _extract_technologies_with_status(technology.name):
            if name not in seen:
                sanitized.append(
                    UserSelectedTechnology(
                        name=name,
                        purpose=technology.purpose,
                        category=technology.category or _classify_tech_for_extraction(name),
                        status=technology.status if technology.status != "MVP_REQUIRED" else status,
                    )
                )
                seen.add(name)
    return sanitized


async def generate_questions(
    project: ProjectState,
    missing_fields: list[str],
    asked_questions: list[dict] | None = None,
    answered_fields: list[str] | None = None,
) -> list[dict]:

    asked_section = ""
    if asked_questions:
        asked_items = []
        for q in asked_questions:
            asked_items.append(
                f"- Field: {q.get('field', 'unknown')}\n"
                f"  Question: {q.get('question', 'unknown')}\n"
                f"  User answer: {q.get('answer', 'unknown')}"
            )
        asked_section = (
            "\n\nPreviously asked questions and user answers:\n"
            + "\n".join(asked_items)
        )

    answered_section = ""
    if answered_fields:
        answered_section = (
            f"\n\nFields the user has ALREADY answered:\n"
            f"{answered_fields}\n"
            f"DO NOT ask about any of these fields again."
        )

    user_message = f"""
Current project state:

{project.model_dump_json(indent=2)}

Missing fields:

{missing_fields}
{asked_section}
{answered_section}

Generate the most important questions that should be asked next.
Do NOT repeat any question that was already asked.
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

    # Handle user_selected_technologies: merge with existing list
    # rather than overwriting, to preserve previous selections
    from app.models.project import UserSelectedTechnology
    new_ust_raw = result.pop("user_selected_technologies", []) or []
    new_ust = _sanitize_user_selected_technologies(
        [UserSelectedTechnology(**t) for t in new_ust_raw]
    )

    # Merge: keep existing + add new (by name dedup)
    existing_names = {t.name.lower() for t in project.user_selected_technologies}
    merged = list(project.user_selected_technologies)
    for t in new_ust:
        if t.name.lower() not in existing_names:
            merged.append(t)
            existing_names.add(t.name.lower())

    result["user_selected_technologies"] = merged

    return ProjectState(**result)
