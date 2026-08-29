from pydantic import BaseModel, Field
from typing import List

from app.models.project import ProjectState
from app.models.requirements import RequirementsDocument
from app.models.architecture import ArchitectureDocument
from app.models.context import ImplementationContext
from app.utils.tech_normalizer import normalize_tech_name, DEV_TOOLS

from app.services.context_quality import assess_context_quality


# Quality gate threshold
QUALITY_GATE_THRESHOLD = 80


class TechPreservationReport(BaseModel):
    """Report on user-selected technology preservation."""
    user_selected_count: int = 0
    preserved_count: int = 0
    missing_count: int = 0
    substituted_count: int = 0
    preserved: List[str] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)
    substituted: List[dict] = Field(default_factory=list)
    ai_assumptions: List[str] = Field(default_factory=list)


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
    tech_preservation: TechPreservationReport = Field(
        default_factory=TechPreservationReport
    )


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

    # Gate rule 5: User-selected technologies must not be substituted
    tech_report = _build_tech_preservation_report(
        project, architecture, context,
    )
    if tech_report.substituted_count > 0:
        for sub in tech_report.substituted:
            rejection_reasons.append(
                f"Technology substitution detected: "
                f"User selected {sub.get('user_techs', [])} "
                f"({sub.get('category', 'unknown')}) but architecture uses "
                f"{sub.get('arch_techs', [])} instead. "
                f"User-selected technologies MUST NOT be silently replaced."
            )

    # Gate rule 6: User-selected technologies must not be dropped
    # Development tools (Git, GitHub) are excluded from rejection
    # because they are not runtime architecture components.
    if tech_report.missing_count > 0:
        for missing_tech in tech_report.missing:
            missing_norm = normalize_tech_name(missing_tech)
            if missing_norm in DEV_TOOLS:
                continue  # Dev tools don't need architecture representation
            rejection_reasons.append(
                f"User-selected technology '{missing_tech}' is missing from "
                f"both architecture and context. "
                f"User-selected technologies MUST be preserved."
            )

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

    # Build technology preservation report
    tech_report = _build_tech_preservation_report(
        project, architecture, context,
    )

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
        tech_preservation=tech_report,
    )


def _build_tech_preservation_report(
    project: ProjectState,
    architecture: ArchitectureDocument,
    context: ImplementationContext,
) -> TechPreservationReport:
    """Build a detailed report on user-selected technology preservation."""
    from app.utils.tech_normalizer import find_substituted_technologies

    user_techs = [
        technology for technology in project.user_selected_technologies
        if technology.status == "MVP_REQUIRED"
    ]
    if not user_techs:
        return TechPreservationReport()

    arch_tech_names = [tc.technology for tc in architecture.technology_stack]
    ctx_tech_names = context.technology_stack
    all_arch_norm = set()
    for t in arch_tech_names + ctx_tech_names:
        all_arch_norm.add(normalize_tech_name(t))

    preserved = []
    missing = []
    substituted = []

    user_names = [t.name for t in user_techs]

    # Find substitutions
    substitutions = find_substituted_technologies(user_names, arch_tech_names)
    ctx_substitutions = find_substituted_technologies(user_names, ctx_tech_names)
    all_substitutions = substitutions + [
        s for s in ctx_substitutions
        if not any(
            ss["category"] == s["category"] and ss["user_techs"] == s["user_techs"]
            for ss in substitutions
        )
    ]

    substituted_names = set()
    for sub in all_substitutions:
        substituted.append({
            "user_techs": sub["user_techs"],
            "arch_techs": sub["arch_techs"],
            "category": sub["category"],
        })
        for name in sub["user_techs"]:
            substituted_names.add(name.lower())

    dev_tools_missing = []
    for ust in user_techs:
        ust_norm = normalize_tech_name(ust.name)
        if ust.name.lower() in substituted_names:
            continue  # already counted as substituted
        if ust_norm and ust_norm in all_arch_norm:
            preserved.append(ust.name)
        elif ust_norm in DEV_TOOLS:
            dev_tools_missing.append(ust.name)
        else:
            missing.append(ust.name)

    # AI assumptions (technologies in architecture not in user selection)
    user_norm = {normalize_tech_name(t.name) for t in user_techs}
    ai_assumptions = []
    for tc in architecture.technology_stack:
        tc_norm = normalize_tech_name(tc.technology)
        if tc_norm and tc_norm not in user_norm:
            ai_assumptions.append(f"{tc.technology} (AI-selected: {tc.reason})")

    return TechPreservationReport(
        user_selected_count=len(user_techs),
        preserved_count=len(preserved),
        missing_count=len(missing),
        substituted_count=len(substituted),
        preserved=preserved,
        missing=missing,
        substituted=substituted,
        ai_assumptions=ai_assumptions,
    )
