from app.models.project import ProjectState
from app.models.requirements import RequirementsDocument
from app.models.architecture import ArchitectureDocument
from app.models.context import ImplementationContext
from app.models.agent_readiness import AgentReadinessResult

from app.engines.agent_readiness import check_agent_readiness
from app.engines.validation import validate_context
from app.models.validation import ContextValidationResult


def assess_context_quality(
    project: ProjectState,
    requirements: RequirementsDocument,
    architecture: ArchitectureDocument,
    context: ImplementationContext,
) -> dict:
    """
    Full quality assessment pipeline:
    1. Run deterministic validation
    2. Run agent readiness checks
    3. Combine results into a quality report
    """

    # Step 1: Basic validation
    validation = validate_context(
        project, requirements, architecture, context,
    )

    # Step 2: Deep agent readiness
    readiness = check_agent_readiness(
        project, requirements, architecture, context,
    )

    # Step 3: Combine
    # If basic validation fails, readiness is automatically not ready
    if not validation.valid:
        readiness.ready = False
        readiness.score = min(readiness.score, validation.score)

    return {
        "validation": validation,
        "readiness": readiness,
        "overall_ready": validation.valid and readiness.ready,
        "overall_score": (
            (validation.score + readiness.score) // 2
        ),
    }


def generate_quality_summary(
    result: dict,
) -> str:
    """Generate a human-readable quality summary."""
    validation = result["validation"]
    readiness = result["readiness"]
    overall_ready = result["overall_ready"]
    overall_score = result["overall_score"]

    lines = []

    if overall_ready:
        lines.append(f"[OK] Context is READY for AI coding agent (Score: {overall_score}/100)")
    else:
        lines.append(f"[FAIL] Context is NOT ready (Score: {overall_score}/100)")

    lines.append("")
    lines.append("## Validation")
    lines.append(f"- Score: {validation.score}/100")
    lines.append(f"- Valid: {'Yes' if validation.valid else 'No'}")
    lines.append(f"- Issues: {len(validation.issues)}")

    lines.append("")
    lines.append("## Agent Readiness Checks")
    lines.append(f"- Requirements Coverage: {readiness.checks.requirements_coverage}%")
    lines.append(f"- Architecture Consistency: {readiness.checks.architecture_consistency}%")
    lines.append(f"- Technology Consistency: {readiness.checks.technology_consistency}%")
    lines.append(f"- API Coverage: {readiness.checks.api_coverage}%")
    lines.append(f"- Data Model Coverage: {readiness.checks.data_model_coverage}%")
    lines.append(f"- Security Coverage: {readiness.checks.security_coverage}%")
    lines.append(f"- Implementation Coverage: {readiness.checks.implementation_coverage}%")
    lines.append(f"- Agent Rules Quality: {readiness.checks.agent_rules_quality}%")
    lines.append(f"- Definition of Done: {readiness.checks.definition_of_done}%")

    if readiness.errors:
        lines.append("")
        lines.append("## Errors")
        for error in readiness.errors:
            lines.append(f"- [ERROR] {error}")

    if readiness.warnings:
        lines.append("")
        lines.append("## Warnings")
        for w in readiness.warnings:
            lines.append(f"- [WARN] [{w.category}] {w.message}")

    if readiness.assumptions:
        lines.append("")
        lines.append("## AI Assumptions")
        for a in readiness.assumptions:
            icon = "[INFO]" if a.severity == "info" else "[WARN]" if a.severity == "warning" else "[CRIT]"
            lines.append(f"- {icon} [{a.area}] {a.assumption}")

    return "\n".join(lines)
