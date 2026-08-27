from app.models.project import ProjectState
from app.models.requirements import RequirementsDocument
from app.models.architecture import ArchitectureDocument
from app.models.context import ImplementationContext
from app.models.agent_readiness import (
    AgentReadinessResult,
    CheckScores,
    ReadinessWarning,
    ReadinessAssumption,
)


def check_agent_readiness(
    project: ProjectState,
    requirements: RequirementsDocument,
    architecture: ArchitectureDocument,
    context: ImplementationContext,
) -> AgentReadinessResult:
    """Deterministic quality gate for AI agent readiness."""

    errors: list[str] = []
    warnings: list[ReadinessWarning] = []
    assumptions: list[ReadinessAssumption] = []

    # ============================================================
    # 1. Requirements Coverage
    # ============================================================
    req_coverage = _check_requirements_coverage(
        requirements, context, warnings
    )

    # ============================================================
    # 2. Architecture Consistency
    # ============================================================
    arch_consistency = _check_architecture_consistency(
        requirements, architecture, context, warnings
    )

    # ============================================================
    # 3. Technology Consistency
    # ============================================================
    tech_consistency = _check_technology_consistency(
        architecture, context, warnings
    )

    # ============================================================
    # 4. API Coverage
    # ============================================================
    api_coverage = _check_api_coverage(
        requirements, architecture, context, warnings
    )

    # ============================================================
    # 5. Data Model Coverage
    # ============================================================
    data_coverage = _check_data_model_coverage(
        requirements, architecture, context, warnings
    )

    # ============================================================
    # 6. Security Coverage
    # ============================================================
    sec_coverage = _check_security_coverage(
        requirements, architecture, context, warnings
    )

    # ============================================================
    # 7. Implementation Coverage
    # ============================================================
    impl_coverage = _check_implementation_coverage(
        requirements, context, warnings
    )

    # ============================================================
    # 8. Agent Rules Quality
    # ============================================================
    agent_rules = _check_agent_rules_quality(
        project, context, warnings
    )

    # ============================================================
    # 9. Definition of Done
    # ============================================================
    dod = _check_definition_of_done(
        requirements, context, warnings
    )

    # ============================================================
    # 10. Contradictions
    # ============================================================
    _check_contradictions(
        project, requirements, architecture, context,
        errors, warnings,
    )

    # ============================================================
    # 11. Duplicate Decisions
    # ============================================================
    _check_duplicate_decisions(
        architecture, context, warnings
    )

    # ============================================================
    # 12. Assumptions
    # ============================================================
    _check_assumptions(
        project, architecture, context, assumptions
    )

    # ============================================================
    # 13. Scope Check
    # ============================================================
    _check_scope(
        project, requirements, context, warnings
    )

    # ============================================================
    # Compute final score
    # ============================================================
    scores = CheckScores(
        requirements_coverage=req_coverage,
        architecture_consistency=arch_consistency,
        technology_consistency=tech_consistency,
        api_coverage=api_coverage,
        data_model_coverage=data_coverage,
        security_coverage=sec_coverage,
        implementation_coverage=impl_coverage,
        agent_rules_quality=agent_rules,
        definition_of_done=dod,
    )

    all_scores = [
        req_coverage,
        arch_consistency,
        tech_consistency,
        api_coverage,
        data_coverage,
        sec_coverage,
        impl_coverage,
        agent_rules,
        dod,
    ]

    avg_score = sum(all_scores) // len(all_scores)

    # Deduct for errors and warnings
    avg_score -= len(errors) * 5
    avg_score -= len(warnings) * 2
    avg_score = max(0, min(100, avg_score))

    ready = len(errors) == 0 and avg_score >= 70

    return AgentReadinessResult(
        ready=ready,
        score=avg_score,
        checks=scores,
        errors=errors,
        warnings=warnings,
        assumptions=assumptions,
    )


# ================================================================
# Individual checks
# ================================================================


def _check_requirements_coverage(
    requirements: RequirementsDocument,
    context: ImplementationContext,
    warnings: list,
) -> int:
    """Check every FR/NFR is represented in the context."""
    all_context = " ".join(
        context.functional_requirements
        + context.non_functional_requirements
    ).lower()

    total = (
        len(requirements.functional_requirements)
        + len(requirements.non_functional_requirements)
    )

    if total == 0:
        return 100

    covered = 0

    for req in requirements.functional_requirements:
        if (
            req.id.lower() in all_context
            or req.title.lower() in all_context
        ):
            covered += 1
        else:
            warnings.append(ReadinessWarning(
                category="requirements_coverage",
                message=(
                    f"FR {req.id} ({req.title}) "
                    "not represented in implementation context."
                ),
            ))

    for req in requirements.non_functional_requirements:
        if (
            req.id.lower() in all_context
            or req.title.lower() in all_context
        ):
            covered += 1
        else:
            warnings.append(ReadinessWarning(
                category="requirements_coverage",
                message=(
                    f"NFR {req.id} ({req.title}) "
                    "not represented in implementation context."
                ),
            ))

    return (covered * 100) // total


def _check_architecture_consistency(
    requirements: RequirementsDocument,
    architecture: ArchitectureDocument,
    context: ImplementationContext,
    warnings: list,
) -> int:
    """Check architecture supports the requirements."""
    if not architecture.components:
        warnings.append(ReadinessWarning(
            category="architecture_consistency",
            message="No architecture components defined.",
        ))
        return 50

    if not architecture.system_architecture:
        warnings.append(ReadinessWarning(
            category="architecture_consistency",
            message="System architecture description is empty.",
        ))
        return 60

    # Check that key requirement areas have corresponding components
    score = 100
    fr_count = len(requirements.functional_requirements)

    if fr_count > 0 and len(architecture.components) < 2:
        score -= 20
        warnings.append(ReadinessWarning(
            category="architecture_consistency",
            message=(
                f"Only {len(architecture.components)} component(s) "
                f"for {fr_count} functional requirements."
            ),
        ))

    if not architecture.api_design:
        score -= 15
        warnings.append(ReadinessWarning(
            category="architecture_consistency",
            message="No API design defined in architecture.",
        ))

    if not architecture.data_architecture:
        score -= 15
        warnings.append(ReadinessWarning(
            category="architecture_consistency",
            message="No data architecture defined.",
        ))

    return max(0, score)


def _check_technology_consistency(
    architecture: ArchitectureDocument,
    context: ImplementationContext,
    warnings: list,
) -> int:
    """Check technology stack matches between architecture and context."""
    arch_techs = {
        tc.technology.lower()
        for tc in architecture.technology_stack
    }
    ctx_techs = {
        t.lower()
        for t in context.technology_stack
    }

    if not arch_techs and not ctx_techs:
        warnings.append(ReadinessWarning(
            category="technology_consistency",
            message="No technology stack defined in architecture or context.",
        ))
        return 40

    if not arch_techs:
        return 80

    if not ctx_techs:
        warnings.append(ReadinessWarning(
            category="technology_consistency",
            message="Context has no technology stack despite architecture defining one.",
        ))
        return 60

    # Technologies in architecture should appear in context
    missing_in_context = arch_techs - ctx_techs
    score = 100

    if missing_in_context:
        penalty = min(40, len(missing_in_context) * 8)
        score -= penalty
        warnings.append(ReadinessWarning(
            category="technology_consistency",
            message=(
                f"Technologies in architecture not in context: "
                f"{', '.join(sorted(missing_in_context))}"
            ),
        ))

    # Technologies in context that aren't in architecture
    extra_in_context = ctx_techs - arch_techs
    if extra_in_context:
        score -= 5
        warnings.append(ReadinessWarning(
            category="technology_consistency",
            message=(
                f"Extra technologies in context not in architecture: "
                f"{', '.join(sorted(extra_in_context))}"
            ),
        ))

    return max(0, min(100, score))


def _check_api_coverage(
    requirements: RequirementsDocument,
    architecture: ArchitectureDocument,
    context: ImplementationContext,
    warnings: list,
) -> int:
    """Check that important requirements have API support."""
    all_endpoints = " ".join(
        ep
        for group in architecture.api_design
        for ep in group.endpoints
    ).lower()

    all_api_text = " ".join(context.api_contract).lower()

    if not all_endpoints and not all_api_text:
        warnings.append(ReadinessWarning(
            category="api_coverage",
            message="No API endpoints defined in architecture or context.",
        ))
        return 40

    # Check that functional requirements have some API representation
    fr_count = len(requirements.functional_requirements)
    if fr_count == 0:
        return 100

    # Simple heuristic: check if requirement keywords appear near API keywords
    covered = 0
    for req in requirements.functional_requirements:
        req_words = set(req.title.lower().split()) - {
            "the", "a", "an", "and", "or", "for", "to", "of", "in",
        }
        if any(
            word in all_endpoints or word in all_api_text
            for word in req_words
            if len(word) > 3
        ):
            covered += 1

    if covered == 0 and fr_count > 2:
        warnings.append(ReadinessWarning(
            category="api_coverage",
            message=(
                "No functional requirements appear to have API support."
            ),
        ))

    return (covered * 100) // fr_count


def _check_data_model_coverage(
    requirements: RequirementsDocument,
    architecture: ArchitectureDocument,
    context: ImplementationContext,
    warnings: list,
) -> int:
    """Check that data model supports the features."""
    data_entities = " ".join(
        de.name.lower() + " " + de.purpose.lower()
        for de in architecture.data_architecture
    )

    ctx_data = " ".join(context.data_model).lower()

    if not data_entities and not ctx_data:
        warnings.append(ReadinessWarning(
            category="data_model_coverage",
            message="No data model defined.",
        ))
        return 40

    score = 100

    if not architecture.data_architecture:
        score -= 25
        warnings.append(ReadinessWarning(
            category="data_model_coverage",
            message="Architecture defines no data entities.",
        ))

    if not context.data_model:
        score -= 25
        warnings.append(ReadinessWarning(
            category="data_model_coverage",
            message="Context has no data model entries.",
        ))

    # Check entity count vs requirement count
    entity_count = len(architecture.data_architecture)
    fr_count = len(requirements.functional_requirements)

    if fr_count > 3 and entity_count < 2:
        score -= 20
        warnings.append(ReadinessWarning(
            category="data_model_coverage",
            message=(
                f"Only {entity_count} data entity/entities for "
                f"{fr_count} functional requirements."
            ),
        ))

    return max(0, min(100, score))


def _check_security_coverage(
    requirements: RequirementsDocument,
    architecture: ArchitectureDocument,
    context: ImplementationContext,
    warnings: list,
) -> int:
    """Check that sensitive functionality has security rules."""
    sec_areas = " ".join(
        s.area.lower() + " " + s.decision.lower()
        for s in architecture.security
    )

    ctx_sec = " ".join(context.security_requirements).lower()

    if not sec_areas and not ctx_sec:
        warnings.append(ReadinessWarning(
            category="security_coverage",
            message="No security requirements defined.",
        ))
        return 30

    score = 100

    if not architecture.security:
        score -= 30
        warnings.append(ReadinessWarning(
            category="security_coverage",
            message="Architecture has no security decisions.",
        ))

    if not context.security_requirements:
        score -= 30
        warnings.append(ReadinessWarning(
            category="security_coverage",
            message="Context has no security requirements.",
        ))

    # Check if auth-related features have security coverage
    has_auth = any(
        "auth" in req.title.lower()
        for req in requirements.functional_requirements
    )
    if has_auth and "auth" not in sec_areas and "auth" not in ctx_sec:
        score -= 15
        warnings.append(ReadinessWarning(
            category="security_coverage",
            message="Authentication feature exists but no auth security rules defined.",
        ))

    # Check if payment features have security coverage
    has_payment = any(
        "pay" in req.title.lower()
        for req in requirements.functional_requirements
    )
    if has_payment and "pay" not in sec_areas and "pay" not in ctx_sec:
        score -= 15
        warnings.append(ReadinessWarning(
            category="security_coverage",
            message="Payment feature exists but no payment security rules defined.",
        ))

    return max(0, min(100, score))


def _check_implementation_coverage(
    requirements: RequirementsDocument,
    context: ImplementationContext,
    warnings: list,
) -> int:
    """Check that requirements are represented in implementation phases."""
    if not context.implementation_phases:
        warnings.append(ReadinessWarning(
            category="implementation_coverage",
            message="No implementation phases defined.",
        ))
        return 30

    all_phase_text = " ".join(
        " ".join(phase.tasks) + " " + phase.objective
        for phase in context.implementation_phases
    ).lower()

    fr_count = len(requirements.functional_requirements)
    if fr_count == 0:
        return 100

    covered = 0
    for req in requirements.functional_requirements:
        req_words = set(req.title.lower().split()) - {
            "the", "a", "an", "and", "or", "for", "to", "of", "in",
        }
        if any(
            word in all_phase_text
            for word in req_words
            if len(word) > 3
        ):
            covered += 1

    if covered == 0 and fr_count > 2:
        warnings.append(ReadinessWarning(
            category="implementation_coverage",
            message=(
                "No functional requirements appear in implementation phases."
            ),
        ))

    return (covered * 100) // fr_count


def _check_agent_rules_quality(
    project: ProjectState,
    context: ImplementationContext,
    warnings: list,
) -> int:
    """Check agent rules quality and relevance."""
    if not context.agent_rules:
        warnings.append(ReadinessWarning(
            category="agent_rules",
            message="No AI coding agent rules defined.",
        ))
        return 20

    score = 100

    # Check minimum number of rules
    if len(context.agent_rules) < 3:
        score -= 20
        warnings.append(ReadinessWarning(
            category="agent_rules",
            message=f"Only {len(context.agent_rules)} agent rule(s). Recommend at least 3.",
        ))

    # Check rule categories cover key areas
    categories = {r.category.lower() for r in context.agent_rules}
    important_categories = {"security", "architecture", "testing"}

    missing = important_categories - categories
    if missing:
        penalty = len(missing) * 10
        score -= penalty
        warnings.append(ReadinessWarning(
            category="agent_rules",
            message=f"Missing rule categories: {', '.join(sorted(missing))}",
        ))

    # Check rules aren't too short (likely low quality)
    short_rules = sum(
        1 for r in context.agent_rules if len(r.rule) < 20
    )
    if short_rules > 0:
        score -= short_rules * 5
        warnings.append(ReadinessWarning(
            category="agent_rules",
            message=f"{short_rules} rule(s) are very short (< 20 chars).",
        ))

    return max(0, min(100, score))


def _check_definition_of_done(
    requirements: RequirementsDocument,
    context: ImplementationContext,
    warnings: list,
) -> int:
    """Check definition of done covers major requirements."""
    if not context.definition_of_done:
        warnings.append(ReadinessWarning(
            category="definition_of_done",
            message="Definition of done is empty.",
        ))
        return 20

    score = 100

    # Minimum criteria count
    fr_count = len(requirements.functional_requirements)
    if fr_count > 0 and len(context.definition_of_done) < fr_count // 2:
        score -= 15
        warnings.append(ReadinessWarning(
            category="definition_of_done",
            message=(
                f"Only {len(context.definition_of_done)} completion criteria "
                f"for {fr_count} functional requirements."
            ),
        ))

    # Check criteria are specific (not too generic)
    generic_phrases = [
        "complete", "done", "finished", "working",
    ]
    generic_count = sum(
        1 for d in context.definition_of_done
        if any(
            d.strip().lower().rstrip(".").endswith(phrase)
            or d.strip().lower().lstrip("- [ ]").strip() in generic_phrases
            for phrase in generic_phrases
        )
    )
    if generic_count > 0:
        score -= generic_count * 5

    return max(0, min(100, score))


def _check_contradictions(
    project: ProjectState,
    requirements: RequirementsDocument,
    architecture: ArchitectureDocument,
    context: ImplementationContext,
    errors: list,
    warnings: list,
) -> None:
    """Detect conflicting decisions across documents."""
    # Check if project technologies contradict architecture
    if project.technologies:
        arch_techs = {
            tc.technology.lower() for tc in architecture.technology_stack
        }
        for tech in project.technologies:
            if tech.lower() not in arch_techs:
                # Check if it's mentioned differently
                tech_words = set(tech.lower().split())
                found = any(
                    tech_words <= set(tc.technology.lower().split())
                    for tc in architecture.technology_stack
                )
                if not found:
                    warnings.append(ReadinessWarning(
                        category="contradiction",
                        message=(
                            f"Project specified '{tech}' but architecture "
                            "does not include it in the technology stack."
                        ),
                    ))

    # Check if platform info contradicts
    if project.platform:
        arch_text = architecture.system_architecture.lower()
        platform_words = set(project.platform.lower().split()) - {
            "the", "a", "an", "and", "or", "both",
        }
        if platform_words and not any(
            word in arch_text for word in platform_words if len(word) > 3
        ):
            warnings.append(ReadinessWarning(
                category="contradiction",
                message=(
                    f"Project platform '{project.platform}' "
                    "not reflected in architecture summary."
                ),
            ))

    # Check deployment contradictions
    if project.deployment:
        deploy_text = " ".join(
            d.environment.lower() + " " + d.reason.lower()
            for d in architecture.deployment
        )
        if deploy_text and not any(
            word in deploy_text
            for word in project.deployment.lower().split()
            if len(word) > 3
        ):
            warnings.append(ReadinessWarning(
                category="contradiction",
                message=(
                    f"Project deployment preference '{project.deployment}' "
                    "not reflected in architecture deployment plan."
                ),
            ))


def _check_duplicate_decisions(
    architecture: ArchitectureDocument,
    context: ImplementationContext,
    warnings: list,
) -> None:
    """Detect repeated or conflicting technology choices."""
    # Check for duplicate technologies
    tech_names = [tc.technology.lower() for tc in architecture.technology_stack]
    seen = set()
    duplicates = set()
    for tech in tech_names:
        if tech in seen:
            duplicates.add(tech)
        seen.add(tech)

    if duplicates:
        warnings.append(ReadinessWarning(
            category="duplicate_decisions",
            message=(
                f"Duplicate technologies in architecture stack: "
                f"{', '.join(sorted(duplicates))}"
            ),
        ))

    # Check for duplicate API groups
    group_names = [g.name.lower() for g in architecture.api_design]
    seen_groups = set()
    dup_groups = set()
    for name in group_names:
        if name in seen_groups:
            dup_groups.add(name)
        seen_groups.add(name)

    if dup_groups:
        warnings.append(ReadinessWarning(
            category="duplicate_decisions",
            message=(
                f"Duplicate API groups in architecture: "
                f"{', '.join(sorted(dup_groups))}"
            ),
        ))


def _check_assumptions(
    project: ProjectState,
    architecture: ArchitectureDocument,
    context: ImplementationContext,
    assumptions: list,
) -> None:
    """Identify AI-inferred decisions not explicitly specified by user."""
    # Check if technology choices were made by AI
    if project.technologies and architecture.technology_stack:
        user_techs = {
            t.lower() for t in project.technologies
        }
        for tc in architecture.technology_stack:
            if tc.technology.lower() not in user_techs:
                assumptions.append(ReadinessAssumption(
                    area="technology",
                    assumption=(
                        f"{tc.technology} was selected by AI "
                        f"(reason: {tc.reason})"
                    ),
                    severity="info",
                ))

    # Check if database was decided by AI
    if not project.database or project.database.lower() in (
        "not decided", "none", "unknown",
    ):
        # Architecture chose a database
        db_techs = [
            tc for tc in architecture.technology_stack
            if tc.category.lower() in ("database", "data")
        ]
        for tc in db_techs:
            assumptions.append(ReadinessAssumption(
                area="database",
                assumption=(
                    f"{tc.technology} was selected as database "
                    f"by AI (reason: {tc.reason})"
                ),
                severity="warning",
            ))

    # Check if deployment was decided by AI
    if not project.deployment or project.deployment.lower() in (
        "not decided", "none", "unknown",
    ):
        if architecture.deployment:
            assumptions.append(ReadinessAssumption(
                area="deployment",
                assumption=(
                    f"Deployment plan ({architecture.deployment[0].environment}) "
                    "was designed by AI without user specification."
                ),
                severity="warning",
            ))

    # Check if constraints were ignored
    if project.constraints:
        ctx_text = " ".join(
            context.architecture_summary
            + context.project_summary
        ).lower()
        for constraint in project.constraints:
            if not any(
                word in ctx_text
                for word in constraint.lower().split()
                if len(word) > 3
            ):
                assumptions.append(ReadinessAssumption(
                    area="constraint",
                    assumption=(
                        f"User constraint '{constraint}' "
                        "may not be reflected in the context."
                    ),
                    severity="critical",
                ))


def _check_scope(
    project: ProjectState,
    requirements: RequirementsDocument,
    context: ImplementationContext,
    warnings: list,
) -> None:
    """Compare scope against implied team/deadline/budget constraints."""
    fr_count = len(requirements.functional_requirements)
    nfr_count = len(requirements.non_functional_requirements)
    phase_count = len(context.implementation_phases)

    # Check scope vs constraints
    if project.constraints:
        constraint_text = " ".join(project.constraints).lower()
        is_large_team = any(
            word in constraint_text
            for word in ["large team", "many developers", "big team"]
        )
        is_short_deadline = any(
            word in constraint_text
            for word in ["urgent", "asap", "deadline", "short time", "quick"]
        )

        if is_short_deadline and fr_count > 8:
            warnings.append(ReadinessWarning(
                category="scope",
                message=(
                    f"Tight deadline constraint with {fr_count} "
                    "functional requirements. Consider reducing scope."
                ),
            ))

    # Check phase count vs requirement count
    if fr_count > 5 and phase_count < 3:
        warnings.append(ReadinessWarning(
            category="scope",
            message=(
                f"Only {phase_count} implementation phase(s) for "
                f"{fr_count} functional requirements. "
                "Phases may be too coarse."
            ),
        ))

    # Check for missing non-functional requirements
    if fr_count > 3 and nfr_count == 0:
        warnings.append(ReadinessWarning(
            category="scope",
            message="No non-functional requirements defined despite having functional ones.",
        ))
