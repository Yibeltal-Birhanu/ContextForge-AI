from pydantic import BaseModel, Field
from typing import List

from app.models.project import ProjectState
from app.models.requirements import RequirementsDocument
from app.models.architecture import ArchitectureDocument
from app.models.context import ImplementationContext

from app.services.context_quality import assess_context_quality


# Quality gate threshold
QUALITY_GATE_THRESHOLD = 80


class QualityGateResult(BaseModel):
    passed: bool
    validation_score: int = Field(ge=0, le=100)
    readiness_score: int = Field(ge=0, le=100)
    overall_score: int = Field(ge=0, le=100)
    ready_for_agent: bool
    checks: dict = Field(default_factory=dict)
    warnings: List[dict] = Field(default_factory=list)
    assumptions: List[dict] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    rejection_reasons: List[str] = Field(default_factory=list)


def run_quality_gate(
    project: ProjectState,
    requirements: RequirementsDocument,
    architecture: ArchitectureDocument,
    context: ImplementationContext,
) -> QualityGateResult:
    """
    Run the full quality gate:
    1. Validation (structural completeness)
    2. Agent readiness (13 checks)
    3. Pass/fail decision
    """

    quality = assess_context_quality(
        project, requirements, architecture, context,
    )

    validation = quality["validation"]
    readiness = quality["readiness"]
    overall_score = quality["overall_score"]
    overall_ready = quality["overall_ready"]

    rejection_reasons = []

    # Gate rule 1: Validation must pass
    if validation.score < QUALITY_GATE_THRESHOLD:
        rejection_reasons.append(
            f"Validation score ({validation.score}/100) "
            f"is below threshold ({QUALITY_GATE_THRESHOLD})"
        )

    # Gate rule 2: Readiness must pass
    if readiness.score < QUALITY_GATE_THRESHOLD:
        rejection_reasons.append(
            f"Agent readiness score ({readiness.score}/100) "
            f"is below threshold ({QUALITY_GATE_THRESHOLD})"
        )

    # Gate rule 3: No critical contradictions
    critical_assumptions = [
        a for a in readiness.assumptions
        if a.severity == "critical"
    ]
    if critical_assumptions:
        for a in critical_assumptions:
            rejection_reasons.append(
                f"Critical assumption: [{a.area}] {a.assumption}"
            )

    # Gate rule 4: No readiness errors
    if readiness.errors:
        for error in readiness.errors:
            rejection_reasons.append(f"Readiness error: {error}")

    # Overall gate decision
    passed = (
        overall_score >= QUALITY_GATE_THRESHOLD
        and len(rejection_reasons) == 0
    )

    # Build checks dict from readiness scores
    checks = {
        "requirements_coverage": readiness.checks.requirements_coverage,
        "architecture_consistency": readiness.checks.architecture_consistency,
        "technology_consistency": readiness.checks.technology_consistency,
        "api_coverage": readiness.checks.api_coverage,
        "data_model_coverage": readiness.checks.data_model_coverage,
        "security_coverage": readiness.checks.security_coverage,
        "implementation_coverage": readiness.checks.implementation_coverage,
        "agent_rules_quality": readiness.checks.agent_rules_quality,
        "definition_of_done": readiness.checks.definition_of_done,
    }

    # Convert warnings to dicts
    warnings = [
        {"category": w.category, "message": w.message}
        for w in readiness.warnings
    ]

    # Convert assumptions to dicts
    assumptions = [
        {
            "area": a.area,
            "assumption": a.assumption,
            "severity": a.severity,
        }
        for a in readiness.assumptions
    ]

    return QualityGateResult(
        passed=passed,
        validation_score=validation.score,
        readiness_score=readiness.score,
        overall_score=overall_score,
        ready_for_agent=overall_ready and passed,
        checks=checks,
        warnings=warnings,
        assumptions=assumptions,
        errors=readiness.errors,
        rejection_reasons=rejection_reasons,
    )
