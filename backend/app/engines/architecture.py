from app.ai.openrouter import generate_structured
from app.models.project import ProjectState
from app.models.requirements import RequirementsDocument
from app.models.architecture import ArchitectureDocument, TechnologyChoice
from app.utils.tech_normalizer import normalize_tech_name, normalize_tech_list
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

    # Normalize LLM output: endpoints may be returned as objects
    # instead of strings. Convert them to strings.
    if "api_design" in result:
        for group in result["api_design"]:
            if "endpoints" in group:
                normalized = []
                for ep in group["endpoints"]:
                    if isinstance(ep, dict):
                        method = ep.get("method", "GET")
                        path = ep.get("path", "")
                        desc = ep.get("description", "")
                        normalized.append(f"{method} {path} - {desc}")
                    else:
                        normalized.append(str(ep))
                group["endpoints"] = normalized

    # Normalize LLM output: important_fields may be returned as
    # objects instead of strings. The LLM uses varying key names:
    #   {"name": "id", "type": "BIGINT", "constraint": "PRIMARY KEY"}
    #   {"field": "id", "constraint": "PRIMARY KEY, BIGINT AUTO_INCREMENT"}
    #   {"column": "id", "definition": "BIGINT PRIMARY KEY"}
    #   {"index": "INDEX(...)", ...}
    #   {"primary_key": "(...)", ...}
    # Convert all variants to a single string.
    def _normalize_field(field):
        """Convert a single important_field entry to a string."""
        if isinstance(field, str):
            return field
        if field is None:
            return None
        # Convert any non-string (dict, Pydantic model, etc.) to string
        if not isinstance(field, dict):
            try:
                return str(field)
            except Exception:
                return None
        parts = []
        # Column name: try 'name', 'field', 'column'
        col_name = (
            field.get("name")
            or field.get("field")
            or field.get("column")
        )
        if col_name:
            parts.append(str(col_name))
        # Type: try 'type', 'data_type', 'datatype'
        col_type = (
            field.get("type")
            or field.get("data_type")
            or field.get("datatype")
        )
        if col_type:
            parts.append(str(col_type))
        # Constraint: try 'constraint', 'definition', 'constraints'
        col_constraint = (
            field.get("constraint")
            or field.get("definition")
            or field.get("constraints")
        )
        if col_constraint:
            parts.append(str(col_constraint))
        # Index/primary key: try 'index', 'primary_key'
        if not parts:
            index_val = field.get("index") or field.get("primary_key")
            if index_val:
                parts.append(str(index_val))
        if parts:
            return " ".join(parts)
        # Last resort: str representation
        try:
            return str(field)
        except Exception:
            return None

    if "data_architecture" in result:
        for entity in result["data_architecture"]:
            if "important_fields" in entity:
                normalized = []
                for field in entity["important_fields"]:
                    s = _normalize_field(field)
                    if s is not None:
                        normalized.append(s)
                entity["important_fields"] = normalized

    architecture = ArchitectureDocument(**result)
    inactive = {
        normalize_tech_name(selected.name)
        for selected in project.user_selected_technologies
        if selected.status in {"FUTURE", "ALTERNATIVE", "EXCLUDED"}
    }
    architecture.technology_stack = [
        choice for choice in architecture.technology_stack
        if normalize_tech_name(choice.technology) not in inactive
    ]
    unique_choices = []
    seen_techs = set()
    for choice in architecture.technology_stack:
        normalized = normalize_tech_name(choice.technology)
        if normalized and normalized not in seen_techs:
            unique_choices.append(choice)
            seen_techs.add(normalized)
    architecture.technology_stack = unique_choices
    architecture_techs = normalize_tech_list(
        [choice.technology for choice in architecture.technology_stack]
    )
    for selected in project.user_selected_technologies:
        if selected.status != "MVP_REQUIRED":
            continue
        selected_norm = normalize_tech_name(selected.name)
        if selected_norm and selected_norm not in architecture_techs:
            architecture.technology_stack.append(
                TechnologyChoice(
                    category=selected.category or "User selected",
                    technology=selected.name,
                    reason=f"User selected for {selected.purpose or 'the project'}",
                )
            )
            architecture_techs.add(selected_norm)

    return architecture
