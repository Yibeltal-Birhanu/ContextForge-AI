from app.models.project import ProjectState
from app.models.requirements import RequirementsDocument
from app.models.architecture import ArchitectureDocument
from app.models.context import ImplementationContext
from app.models.validation import (
    ContextValidationResult,
    ValidationIssue,
)


def validate_context(
    project: ProjectState,
    requirements: RequirementsDocument,
    architecture: ArchitectureDocument,
    context: ImplementationContext,
) -> ContextValidationResult:

    issues: list[ValidationIssue] = []

    # ---------------------------------------------------------
    # Basic completeness
    # ---------------------------------------------------------

    if not context.project_title:
        issues.append(
            ValidationIssue(
                category="project",
                severity="error",
                message="Project title is missing.",
            )
        )

    if not context.project_summary:
        issues.append(
            ValidationIssue(
                category="project",
                severity="error",
                message="Project summary is missing.",
            )
        )

    # ---------------------------------------------------------
    # Requirement coverage
    # ---------------------------------------------------------

    context_requirements = " ".join(
        context.functional_requirements
        + context.non_functional_requirements
    ).lower()

    for requirement in requirements.functional_requirements:

        if (
            requirement.id.lower()
            not in context_requirements
            and requirement.title.lower()
            not in context_requirements
        ):
            issues.append(
                ValidationIssue(
                    category="requirements",
                    severity="error",
                    message=(
                        f"{requirement.id} "
                        f"({requirement.title}) "
                        "is not represented in the context."
                    ),
                )
            )

    for requirement in requirements.non_functional_requirements:

        if (
            requirement.id.lower()
            not in context_requirements
            and requirement.title.lower()
            not in context_requirements
        ):
            issues.append(
                ValidationIssue(
                    category="requirements",
                    severity="warning",
                    message=(
                        f"{requirement.id} "
                        f"({requirement.title}) "
                        "may not be represented in the context."
                    ),
                )
            )

    # ---------------------------------------------------------
    # Architecture coverage
    # ---------------------------------------------------------

    if not context.architecture_summary:
        issues.append(
            ValidationIssue(
                category="architecture",
                severity="error",
                message="Architecture summary is missing.",
            )
        )

    if not context.technology_stack:
        issues.append(
            ValidationIssue(
                category="architecture",
                severity="error",
                message="Technology stack is missing.",
            )
        )

    if not context.data_model:
        issues.append(
            ValidationIssue(
                category="architecture",
                severity="warning",
                message="Data model is empty.",
            )
        )

    if not context.api_contract:
        issues.append(
            ValidationIssue(
                category="architecture",
                severity="warning",
                message="API contract is empty.",
            )
        )

    # ---------------------------------------------------------
    # Security
    # ---------------------------------------------------------

    if not context.security_requirements:
        issues.append(
            ValidationIssue(
                category="security",
                severity="error",
                message="Security requirements are missing.",
            )
        )

    # ---------------------------------------------------------
    # Implementation plan
    # ---------------------------------------------------------

    if not context.implementation_phases:

        issues.append(
            ValidationIssue(
                category="implementation",
                severity="error",
                message="No implementation phases were generated.",
            )
        )

    # ---------------------------------------------------------
    # Agent rules
    # ---------------------------------------------------------

    if not context.agent_rules:

        issues.append(
            ValidationIssue(
                category="agent",
                severity="warning",
                message="No AI coding-agent rules were generated.",
            )
        )

    # ---------------------------------------------------------
    # Definition of done
    # ---------------------------------------------------------

    if not context.definition_of_done:

        issues.append(
            ValidationIssue(
                category="completion",
                severity="error",
                message="Definition of done is missing.",
            )
        )

    # ---------------------------------------------------------
    # Score
    # ---------------------------------------------------------

    error_count = sum(
        1
        for issue in issues
        if issue.severity == "error"
    )

    warning_count = sum(
        1
        for issue in issues
        if issue.severity == "warning"
    )

    score = 100

    score -= error_count * 12
    score -= warning_count * 4

    score = max(0, min(100, score))

    valid = error_count == 0

    return ContextValidationResult(
        valid=valid,
        score=score,
        issues=issues,
    )
