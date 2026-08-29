from app.ai.openrouter import generate_structured
from app.models.project import ProjectState
from app.models.requirements import RequirementsDocument
from app.models.architecture import ArchitectureDocument
from app.models.context import ImplementationContext
from app.prompts.improvement import (
    CONTEXT_IMPROVEMENT_SYSTEM_PROMPT,
    build_improvement_prompt,
)


async def improve_context(
    project: ProjectState,
    requirements: RequirementsDocument,
    architecture: ArchitectureDocument,
    current_context: ImplementationContext,
    quality_checks: dict,
) -> ImplementationContext:
    """
    Improve the context targeting specific weak areas.

    Uses the quality check scores to identify which sections
    need improvement and sends targeted instructions to the AI.
    """

    # Build the list of issues to fix
    issues = _identify_issues(
        current_context, quality_checks,
    )

    if not issues:
        # Nothing to improve
        return current_context

    # Build the improvement prompt
    user_message = build_improvement_prompt(
        context_json=current_context.model_dump_json(indent=2),
        issues=issues,
        project_json=project.model_dump_json(indent=2),
        requirements_json=requirements.model_dump_json(indent=2),
        architecture_json=architecture.model_dump_json(indent=2),
    )

    # Call the AI to improve
    result = await generate_structured(
        system_prompt=CONTEXT_IMPROVEMENT_SYSTEM_PROMPT,
        user_message=user_message,
    )

    return ImplementationContext(**result)


def _identify_issues(
    context: ImplementationContext,
    quality_checks: dict,
) -> list[str]:
    """
    Convert quality check scores into specific improvement instructions.

    Only generates issues for checks below threshold.
    """
    THRESHOLD = 85
    issues = []

    checks = quality_checks.get("checks", {})

    # API Coverage
    api_score = checks.get("api_coverage", 100)
    if api_score < THRESHOLD:
        issues.append(
            f"API Coverage is {api_score}%. "
            f"The api_contract section needs more endpoints. "
            f"Review all functional requirements and ensure each "
            f"has corresponding API endpoints defined."
        )

    # Implementation Coverage
    impl_score = checks.get("implementation_coverage", 100)
    if impl_score < THRESHOLD:
        issues.append(
            f"Implementation Coverage is {impl_score}%. "
            f"The implementation_phases section is incomplete. "
            f"Review all functional requirements and ensure each "
            f"is covered by at least one implementation phase with "
            f"concrete tasks and deliverables."
        )

    # Security Coverage
    sec_score = checks.get("security_coverage", 100)
    if sec_score < THRESHOLD:
        issues.append(
            f"Security Coverage is {sec_score}%. "
            f"The security_requirements section needs more entries. "
            f"Review all features for security implications: "
            f"authentication, payment, data protection, input validation, "
            f"rate limiting, and access control."
        )

    # Data Model Coverage
    data_score = checks.get("data_model_coverage", 100)
    if data_score < THRESHOLD:
        issues.append(
            f"Data Model Coverage is {data_score}%. "
            f"The data_model section needs more entities. "
            f"Review all features and ensure the data model "
            f"includes entities to support them."
        )

    # Agent Rules Quality
    rules_score = checks.get("agent_rules_quality", 100)
    if rules_score < THRESHOLD:
        issues.append(
            f"Agent Rules Quality is {rules_score}%. "
            f"The agent_rules section needs improvement. "
            f"Add rules covering: architecture constraints, "
            f"security practices, testing requirements, "
            f"coding standards, and deployment procedures."
        )

    # Definition of Done
    dod_score = checks.get("definition_of_done", 100)
    if dod_score < THRESHOLD:
        issues.append(
            f"Definition of Done is {dod_score}%. "
            f"The definition_of_done section needs more criteria. "
            f"Add completion criteria for each major requirement."
        )

    # Requirements Coverage
    req_score = checks.get("requirements_coverage", 100)
    if req_score < THRESHOLD:
        issues.append(
            f"Requirements Coverage is {req_score}%. "
            f"Some requirements are not represented in the context. "
            f"Review all FR and NFR items and ensure they appear "
            f"in the appropriate context sections."
        )

    # Architecture Consistency
    arch_score = checks.get("architecture_consistency", 100)
    if arch_score < THRESHOLD:
        issues.append(
            f"Architecture Consistency is {arch_score}%. "
            f"The context may not fully reflect the architecture. "
            f"Review components, technology stack, and data architecture."
        )

    # Technology Consistency
    tech_score = checks.get("technology_consistency", 100)
    if tech_score < THRESHOLD:
        issues.append(
            f"Technology Consistency is {tech_score}%. "
            f"The technology_stack may not match the architecture. "
            f"Ensure all technologies from the architecture are present."
        )

    return issues
