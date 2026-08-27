from pathlib import Path

from app.models.context import ImplementationContext
from app.models.validation import ContextValidationResult
from app.engines.assembly import assemble_markdown


def build_markdown_file(
    context: ImplementationContext,
    validation: ContextValidationResult,
) -> tuple[str, bytes]:

    markdown = assemble_markdown(
        context=context,
        validation=validation,
    )

    filename = _safe_filename(
        context.project_title
    )

    return (
        f"{filename}.md",
        markdown.encode("utf-8"),
    )


def build_text_file(
    context: ImplementationContext,
    validation: ContextValidationResult,
) -> tuple[str, bytes]:

    markdown = assemble_markdown(
        context=context,
        validation=validation,
    )

    filename = _safe_filename(
        context.project_title
    )

    return (
        f"{filename}.txt",
        markdown.encode("utf-8"),
    )


def _safe_filename(name: str) -> str:

    safe = "".join(
        character
        if character.isalnum()
        else "_"
        for character in name
    )

    safe = safe.strip("_")

    return safe or "contextforge_project"
