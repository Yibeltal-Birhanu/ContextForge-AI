from app.ai.openrouter import generate_structured

from app.models.project import ProjectState
from app.models.requirements import RequirementsDocument
from app.models.architecture import ArchitectureDocument
from app.models.context import ImplementationContext
from app.utils.tech_normalizer import (
    normalize_tech_name,
    normalize_tech_list,
    dedupe_technology_strings,
)

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

Only include domain-specific rules supported by the ProjectState and
RequirementsDocument. Do not include healthcare-specific actors or terms
unless this project explicitly involves healthcare.
"""

    result = await generate_structured(
        system_prompt=CONTEXT_ENGINEERING_SYSTEM_PROMPT,
        user_message=user_message,
    )

    # Normalize list fields that LLM may return as objects instead of strings
    _normalize_string_lists(result)
    result["technology_stack"] = dedupe_technology_strings(
        result.get("technology_stack", [])
    )
    inactive = {
        normalize_tech_name(selected.name)
        for selected in project.user_selected_technologies
        if selected.status in {"FUTURE", "ALTERNATIVE", "EXCLUDED"}
    }
    result["technology_stack"] = [
        technology for technology in result.get("technology_stack", [])
        if normalize_tech_name(technology) not in inactive
    ]
    unique_techs = []
    seen_techs = set()
    for technology in result["technology_stack"]:
        normalized = normalize_tech_name(technology)
        if normalized and normalized not in seen_techs:
            unique_techs.append(technology)
            seen_techs.add(normalized)
    result["technology_stack"] = unique_techs

    for selected in project.user_selected_technologies:
        if selected.status != "MVP_REQUIRED":
            continue
        selected_norm = normalize_tech_name(selected.name)
        context_techs = normalize_tech_list(result.get("technology_stack", []))
        if selected_norm and selected_norm not in context_techs:
            result.setdefault("technology_stack", []).append(selected.name)

    return ImplementationContext(**result)


def _normalize_string_lists(data: dict) -> None:
    """Convert list fields that should be List[str] but may contain dicts."""
    string_list_fields = [
        "functional_requirements", "non_functional_requirements",
        "technology_stack", "data_model", "api_contract",
        "security_requirements", "definition_of_done",
        "target_users",
    ]
    for field in string_list_fields:
        if field in data and isinstance(data[field], list):
            normalized = []
            for item in data[field]:
                if isinstance(item, dict):
                    # Try to create a readable string from the dict
                    if "method" in item and "path" in item:
                        desc = item.get("description", item.get("purpose", ""))
                        normalized.append(f"{item['method']} {item['path']} - {desc}")
                    elif "id" in item and "title" in item:
                        normalized.append(f"{item['id']}: {item['title']} - {item.get('description', '')}")
                    elif "name" in item and "purpose" in item:
                        normalized.append(f"{item['name']}: {item['purpose']}")
                    else:
                        # Fallback: join all values
                        normalized.append(" - ".join(str(v) for v in item.values()))
                else:
                    normalized.append(str(item))
            data[field] = normalized
