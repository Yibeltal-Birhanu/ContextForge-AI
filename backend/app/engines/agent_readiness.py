import re

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
from app.utils.tech_normalizer import (
    normalize_tech_list,
    normalize_tech_name,
    tech_sets_match,
    classify_tech,
    find_substituted_technologies,
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
        project, architecture, context, warnings
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

    _check_context_isolation(
        project, requirements, architecture, context, warnings
    )

    # ============================================================
    # 14. Concurrency & Safety
    # ============================================================
    _check_concurrency_safety(
        project, requirements, architecture, context, warnings
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
    project: ProjectState,
    architecture: ArchitectureDocument,
    context: ImplementationContext,
    warnings: list,
) -> int:
    """Check technology stack consistency using canonical normalization."""

    # Normalize all technology lists to canonical sets
    arch_raw = [tc.technology for tc in architecture.technology_stack]
    ctx_raw = context.technology_stack
    proj_raw = project.technologies or []

    arch_norm = normalize_tech_list(arch_raw)
    ctx_norm = normalize_tech_list(ctx_raw)
    proj_norm = normalize_tech_list(proj_raw)

    # Note: We do NOT add generic "ai" to proj_norm.
    # "AI" is a concept, not a technology.  The concrete technology
    # would be "OpenAI API", "Amazon Bedrock", etc.
    # Checking for AI tech presence is done separately below.

    if not arch_norm and not ctx_norm:
        warnings.append(ReadinessWarning(
            category="technology_consistency",
            message="No technology stack defined in architecture or context.",
        ))
        return 40

    if not arch_norm:
        return 80

    if not ctx_norm:
        warnings.append(ReadinessWarning(
            category="technology_consistency",
            message="Context has no technology stack despite architecture defining one.",
        ))
        return 60

    score = 100

    # Check 1: Technologies in architecture should appear in context (normalized)
    _, missing_in_ctx, extra_in_ctx = tech_sets_match(arch_norm, ctx_norm)
    if missing_in_ctx:
        penalty = min(30, len(missing_in_ctx) * 6)
        score -= penalty
        warnings.append(ReadinessWarning(
            category="technology_consistency",
            message=(
                f"Technologies in architecture not in context: "
                f"{', '.join(sorted(missing_in_ctx))}"
            ),
        ))

    if extra_in_ctx:
        score -= 5
        warnings.append(ReadinessWarning(
            category="technology_consistency",
            message=(
                f"Extra technologies in context not in architecture: "
                f"{', '.join(sorted(extra_in_ctx))}"
            ),
        ))

    # Check 3: User-selected technologies MUST be in architecture (no substitution)
    user_selected_names = [t.name for t in project.user_selected_technologies]
    if user_selected_names:
        user_sel_norm = normalize_tech_list(user_selected_names)

        # Check each user-selected tech is present in architecture
        for ust in project.user_selected_technologies:
            ust_norm = normalize_tech_name(ust.name)
            if ust_norm and ust_norm not in arch_norm:
                # Check if it's in context as fallback
                if ust_norm in ctx_norm:
                    warnings.append(ReadinessWarning(
                        category="technology_consistency",
                        message=(
                            f"User-selected '{ust.name}' ({ust.purpose}) "
                            "is in context but missing from architecture."
                        ),
                    ))
                    score -= 5
                else:
                    score -= 15
                    warnings.append(ReadinessWarning(
                        category="technology_consistency",
                        message=(
                            f"MISSING: User-selected '{ust.name}' "
                            f"({ust.purpose}) is not in architecture or context."
                        ),
                    ))

        # Check for SILENT SUBSTITUTION: architecture uses different tech
        # in same category as user-selected tech
        substitutions = find_substituted_technologies(
            user_selected_names,
            [tc.technology for tc in architecture.technology_stack],
        )
        for sub in substitutions:
            score -= 20
            warnings.append(ReadinessWarning(
                category="technology_consistency",
                message=(
                    f"CONTRADICTION: User selected {sub['user_techs']} "
                    f"({sub['category']}) but architecture uses "
                    f"{sub['arch_techs']} instead. "
                    f"User-selected technologies must not be silently replaced."
                ),
            ))

        # Also check context for substitution
        ctx_substitutions = find_substituted_technologies(
            user_selected_names,
            ctx_raw,
        )
        for sub in ctx_substitutions:
            # Only report if not already caught in architecture check
            already_reported = any(
                s["category"] == sub["category"] and s["user_techs"] == sub["user_techs"]
                for s in substitutions
            )
            if not already_reported:
                score -= 15
                warnings.append(ReadinessWarning(
                    category="technology_consistency",
                    message=(
                        f"User selected {sub['user_techs']} "
                        f"({sub['category']}) but context uses "
                        f"{sub['arch_techs']} instead."
                    ),
                ))

    elif proj_norm:
        # Fallback: project.technologies but no user_selected_technologies
        _, missing_from_arch, _ = tech_sets_match(proj_norm, arch_norm)

        if missing_from_arch:
            penalty = min(25, len(missing_from_arch) * 8)
            score -= penalty
            warnings.append(ReadinessWarning(
                category="technology_consistency",
                message=(
                    f"User-specified technologies not in architecture: "
                    f"{', '.join(sorted(missing_from_arch))}"
                ),
            ))

    # Check 4: Project AI mentions should have AI tech in architecture
    # Only check for concrete AI technologies, not the generic concept "ai"
    project_text = " ".join([
        (project.description or "").lower(),
        (project.problem or "").lower(),
        " ".join(f.lower() for f in project.core_features),
        " ".join(t.lower() for t in project.technologies),
    ])
    ai_keywords = ["artificial intelligence", "machine learning", "deep learning", "nlp"]
    project_mentions_ai = any(kw in project_text for kw in ai_keywords)
    if project_mentions_ai:
        arch_text = " ".join(tc.technology.lower() + " " + tc.reason.lower()
                           for tc in architecture.technology_stack)
        concrete_ai_techs = ["openai", "anthropic", "tensorflow", "pytorch",
                           "huggingface", "langchain", "bedrock", "vertex"]
        ai_in_arch = any(kw in arch_text for kw in concrete_ai_techs)
        if not ai_in_arch:
            score -= 15
            warnings.append(ReadinessWarning(
                category="technology_consistency",
                message="Project mentions AI capabilities but no concrete AI technology found in architecture.",
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
    from app.utils.tech_normalizer import _are_equivalent

    # Check if project technologies contradict architecture
    if project.technologies:
        arch_techs = normalize_tech_list(
            [tc.technology for tc in architecture.technology_stack]
        )
        for tech in project.technologies:
            tech_norm = normalize_tech_name(tech)
            if tech_norm not in arch_techs:
                # Check if it's mentioned differently
                tech_words = set(tech_norm.split())
                found = any(
                    tech_words <= set(tc.technology.lower().split())
                    for tc in architecture.technology_stack
                )
                if not found:
                    # Check tech equivalents (e.g. TypeScript/JavaScript)
                    arch_norm_set = normalize_tech_list(
                        [tc.technology for tc in architecture.technology_stack]
                    )
                    tech_canonical = normalize_tech_name(tech)
                    is_equivalent = any(
                        _are_equivalent(tech_canonical, a)
                        for a in arch_norm_set
                    )
                    if not is_equivalent:
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

    # Check AI contradiction — only for CONCRETE AI technologies
    # "AI" is a concept, not a technology.  Check if the user explicitly
    # named an AI provider (OpenAI, Bedrock, etc.) and it's missing.
    if project.technologies:
        ai_providers = {"openai", "anthropic", "tensorflow", "pytorch",
                       "huggingface", "langchain", "amazon bedrock",
                       "aws bedrock", "google vertex ai", "azure openai"}
        project_ai_techs = [
            t for t in project.technologies
            if t.lower().strip() in ai_providers
            or normalize_tech_name(t) in ai_providers
        ]
        if project_ai_techs:
            arch_norm = normalize_tech_list(
                [tc.technology for tc in architecture.technology_stack]
            )
            for ai_tech in project_ai_techs:
                ai_norm = normalize_tech_name(ai_tech)
                if ai_norm and ai_norm not in arch_norm:
                    # Check if it's in context as fallback
                    ctx_norm = normalize_tech_list(context.technology_stack)
                    if ai_norm not in ctx_norm:
                        warnings.append(ReadinessWarning(
                            category="contradiction",
                            message=(
                                f"Project specified AI technology '{ai_tech}' "
                                "but it is not in architecture or context."
                            ),
                        ))

    # Check database contradiction using normalized tech comparison
    if project.database and project.database.lower() not in ["not decided", "none", "no preference"]:
        arch_norm = normalize_tech_list([tc.technology for tc in architecture.technology_stack])
        ctx_norm = normalize_tech_list(context.technology_stack)
        db_norm = normalize_tech_list([project.database])
        all_norm = arch_norm | ctx_norm
        _, missing_db, _ = tech_sets_match(db_norm, all_norm)
        if missing_db:
            warnings.append(ReadinessWarning(
                category="contradiction",
                message=(
                    f"Project specified database '{project.database}' "
                    "but architecture does not reference it."
                ),
            ))

    # Check user-selected technology substitution (semantic, not string)
    if project.user_selected_technologies:
        user_techs = [t.name for t in project.user_selected_technologies]
        arch_techs = [tc.technology for tc in architecture.technology_stack]
        substitutions = find_substituted_technologies(user_techs, arch_techs)
        for sub in substitutions:
            warnings.append(ReadinessWarning(
                category="contradiction",
                message=(
                    f"User explicitly selected {sub['user_techs']} "
                    f"for {sub['category']} but architecture uses "
                    f"{sub['arch_techs']} instead. "
                    f"User-selected technologies MUST NOT be silently replaced."
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
    # Build the set of user-selected technology normalized names
    user_sel_norm = {
        normalize_tech_name(t.name)
        for t in project.user_selected_technologies
    }

    # Also include database and deployment if user specified them
    if project.database and project.database.lower() not in (
        "not decided", "none", "unknown",
    ):
        user_sel_norm.add(normalize_tech_name(project.database))

    # Check if technology choices were made by AI
    # Only report as AI assumption if NOT in user-selected or user-specified techs
    if architecture.technology_stack:
        for tc in architecture.technology_stack:
            tc_norm = normalize_tech_name(tc.technology)

            # Skip if this is a user-selected technology
            if tc_norm in user_sel_norm:
                continue

            # Skip if it matches a user-specified technology (exact or fuzzy)
            is_user_tech = False
            if project.technologies:
                for ut in project.technologies:
                    ut_norm = normalize_tech_name(ut)
                    if ut_norm == tc_norm or tc_norm in ut_norm or ut_norm in tc_norm:
                        is_user_tech = True
                        break
            if is_user_tech:
                continue

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
            # Don't report if already covered by user-selected check above
            tc_norm = normalize_tech_name(tc.technology)
            if tc_norm not in user_sel_norm:
                assumptions.append(ReadinessAssumption(
                    area="database",
                    assumption=(
                        f"{tc.technology} was selected as database "
                        f"by AI (reason: {tc.reason})"
                    ),
                    severity="info",
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
                severity="info",
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
                    severity="info",
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

    constraint_text = " ".join(project.constraints).lower()
    simplicity_requested = any(
        phrase in constraint_text
        for phrase in ("mvp", "simple", "low-cost", "low cost", "limited budget")
    )
    if simplicity_requested and fr_count > 12:
        warnings.append(ReadinessWarning(
            category="scope",
            message=(
                f"MVP/simple-scope constraint with {fr_count} functional "
                "requirements. Mark a smaller must-have set for the MVP."
            ),
        ))

    if fr_count > 0:
        priorities = {
            requirement.priority.upper()
            for requirement in requirements.functional_requirements
        }
        if not priorities.intersection({"MUST_HAVE", "MUST", "P0", "HIGH"}):
            warnings.append(ReadinessWarning(
                category="scope",
                message="Functional requirements have no explicit MVP must-have priority.",
            ))

    context_entry_count = sum(
        len(values) for values in (
            context.functional_requirements,
            context.non_functional_requirements,
            context.data_model,
            context.api_contract,
            context.security_requirements,
            context.definition_of_done,
        )
    )
    context_size = len(context.model_dump_json())
    if context_entry_count > 80 or context_size > 50000:
        warnings.append(ReadinessWarning(
            category="scope",
            message=(
                f"Implementation context is large ({context_entry_count} entries, "
                f"{context_size} characters). Consider splitting or removing "
                "non-essential detail."
            ),
        ))


def _check_context_isolation(
    project: ProjectState,
    requirements: RequirementsDocument,
    architecture: ArchitectureDocument,
    context: ImplementationContext,
    warnings: list,
) -> None:
    """Detect high-confidence domain vocabulary leaking between projects."""
    project_text = " ".join([
        project.name or "",
        project.description or "",
        project.problem or "",
        " ".join(project.core_features),
        " ".join(project.target_users),
    ]).lower()
    generated_text = " ".join([
        context.project_summary,
        context.problem,
        " ".join(context.target_users),
        " ".join(context.functional_requirements),
        " ".join(context.data_model),
        " ".join(context.api_contract),
    ]).lower()
    domain_groups = {
        "healthcare": {"patient", "patients", "clinic", "clinics", "doctor", "doctors"},
        "agriculture": {"farmer", "farmers", "crop", "crops", "supplier", "suppliers"},
        "education": {"student", "students", "course", "courses", "teacher", "teachers"},
        "commerce": {"product", "products", "cart", "checkout", "order", "orders"},
    }
    project_domains = {
        domain for domain, terms in domain_groups.items()
        if any(re.search(rf"\b{re.escape(term)}\b", project_text) for term in terms)
    }
    leaked = []
    for domain, terms in domain_groups.items():
        if domain in project_domains:
            continue
        if any(re.search(rf"\b{re.escape(term)}\b", generated_text) for term in terms):
            leaked.append(domain)
    if leaked:
        warnings.append(ReadinessWarning(
            category="context_isolation",
            message=(
                "Generated context contains domain vocabulary not found in the "
                f"project: {', '.join(sorted(leaked))}. Verify cross-project isolation."
            ),
        ))


def _check_concurrency_safety(
    project: ProjectState,
    requirements: RequirementsDocument,
    architecture: ArchitectureDocument,
    context: ImplementationContext,
    warnings: list,
) -> None:
    """Check that concurrency-critical patterns are addressed.

    For projects involving bookings, payments, or background jobs,
    verify that the architecture and context describe the correct
    safety mechanisms (locking, idempotency, job claiming).
    """
    # Combine all relevant text
    all_arch_text = (
        architecture.system_architecture + " "
        + " ".join(c.responsibility + " " + " ".join(c.technologies)
                    for c in architecture.components) + " "
        + " ".join(d.environment + " " + d.reason
                    for d in architecture.deployment)
    ).lower()

    all_ctx_text = (
        " ".join(context.functional_requirements) + " "
        + " ".join(context.non_functional_requirements) + " "
        + " ".join(context.security_requirements) + " "
        + " ".join(r.rule for r in context.agent_rules) + " "
        + " ".join(phase.objective + " " + " ".join(phase.tasks)
                    for phase in context.implementation_phases)
    ).lower()

    all_text = all_arch_text + " " + all_ctx_text

    # --- A. Booking / Reservation systems ---
    has_booking = any(
        word in all_text
        for word in ["booking", "appointment", "reservation",
                     "schedule", "slot"]
    )
    if has_booking:
        has_locking = any(
            word in all_text
            for word in ["for update", "select for update",
                         "row lock", "pessimistic lock",
                         "unique constraint", "unique key",
                         "database-level constraint"]
        )
        if not has_locking:
            warnings.append(ReadinessWarning(
                category="concurrency_safety",
                message=(
                    "Project has booking/reservation features but "
                    "architecture does not describe a locking strategy. "
                    "Double-booking is likely without database-level locking "
                    "(SELECT ... FOR UPDATE or UNIQUE constraints)."
                ),
            ))

    # --- B. Payment processing ---
    has_payment = any(
        word in all_text
        for word in ["payment", "pay", "checkout", "transaction",
                     "webhook", "callback"]
    )
    if has_payment:
        has_idempotency = any(
            word in all_text
            for word in ["idempoten", "dedup", "duplicate",
                         "unique constraint", "provider reference",
                         "transaction reference"]
        )
        if not has_idempotency:
            warnings.append(ReadinessWarning(
                category="concurrency_safety",
                message=(
                    "Project has payment features but architecture "
                    "does not describe webhook idempotency. "
                    "Duplicate payment processing is likely without "
                    "idempotent handlers and unique constraints."
                ),
            ))

        has_state_machine = any(
            word in all_text
            for word in ["initiated", "pending", "completed",
                         "failed", "refunded", "status machine",
                         "state machine", "payment status"]
        )
        if not has_state_machine:
            warnings.append(ReadinessWarning(
                category="concurrency_safety",
                message=(
                    "Payment processing lacks a clear status state machine. "
                    "Define explicit payment states and transitions."
                ),
            ))

    # --- C. Background jobs with multi-replica deployment ---
    has_bg_jobs = any(
        word in all_text
        for word in ["cron", "scheduler", "background", "worker",
                     "reminder", "periodic", "recurring"]
    )
    has_multi_replica = any(
        word in all_text
        for word in ["fargate", "kubernetes", "k8s", "ecs",
                     "horizontal", "scaling", "replica",
                     "multiple instance", "load balanc"]
    )
    if has_bg_jobs and has_multi_replica:
        has_safe_scheduling = any(
            word in all_text
            for word in ["for update skip locked", "job claim",
                         "distributed lock", "leader elect",
                         "eventbridge scheduler", "single replica",
                         "single instance", "database-based job"]
        )
        uses_inprocess_cron = any(
            word in all_text
            for word in ["node-cron", "setinterval", "setinterval",
                         "in-process cron", "setTimeout"]
        ) and not has_safe_scheduling

        if uses_inprocess_cron:
            warnings.append(ReadinessWarning(
                category="concurrency_safety",
                message=(
                    "CRITICAL: In-process cron/scheduler detected with "
                    "multi-replica deployment. Each replica will fire "
                    "scheduled jobs independently, causing duplicate "
                    "processing (e.g. duplicate SMS, duplicate emails). "
                    "Use database-based job claiming (SELECT ... FOR UPDATE "
                    "SKIP LOCKED) or a managed scheduler instead."
                ),
            ))
        elif not has_safe_scheduling:
            warnings.append(ReadinessWarning(
                category="concurrency_safety",
                message=(
                    "Project has background jobs and multi-replica "
                    "deployment but does not describe a safe scheduling "
                    "strategy. Verify that job deduplication is addressed."
                ),
            ))

    # --- D. Healthcare / sensitive data ---
    has_sensitive_data = any(
        word in all_text
        for word in ["patient", "health", "medical", "clinical",
                     "diagnosis", "health record"]
    )
    if has_sensitive_data:
        has_audit = any(
            word in all_text
            for word in ["audit", "audit log", "activity log",
                         "access log"]
        )
        if not has_audit:
            warnings.append(ReadinessWarning(
                category="concurrency_safety",
                message=(
                    "Project handles sensitive health data but "
                    "architecture does not describe audit logging. "
                    "Healthcare applications require comprehensive "
                    "audit trails for compliance."
                ),
            ))

        has_encryption = any(
            word in all_text
            for word in ["encrypt", "aes", "at rest", "in transit",
                         "tls", "ssl", "kms"]
        )
        if not has_encryption:
            warnings.append(ReadinessWarning(
                category="concurrency_safety",
                message=(
                    "Project handles sensitive health data but "
                    "architecture does not describe encryption "
                    "strategy (at rest and in transit)."
                ),
            ))

    # --- E. AI integrations requiring disclaimer ---
    has_ai = any(
        word in all_text
        for word in ["ai", "artificial intelligence", "machine learning",
                     "openai", "bedrock", "llm", "gpt", "claude"]
    )
    if has_ai and has_sensitive_data:
        has_disclaimer = any(
            word in all_text
            for word in ["disclaimer", "not medical advice",
                         "not professional advice",
                         "general information",
                         "consult a professional"]
        )
        if not has_disclaimer:
            warnings.append(ReadinessWarning(
                category="concurrency_safety",
                message=(
                    "AI integration in healthcare context lacks a "
                    "disclaimer strategy. The AI component MUST include "
                    "a disclaimer that it is not medical advice and that "
                    "users should consult qualified professionals."
                ),
            ))

    # --- F. Secrets management ---
    has_external_apis = any(
        word in all_text
        for word in ["api key", "api credential", "secret",
                     "token", "webhook"]
    )
    if has_external_apis:
        has_secrets_mgmt = any(
            word in all_text
            for word in ["secrets manager", "vault", "secret manager",
                         "aws secrets", "environment variable"]
        )
        if not has_secrets_mgmt:
            warnings.append(ReadinessWarning(
                category="concurrency_safety",
                message=(
                    "Project uses external APIs but does not describe "
                    "a secrets management strategy. API keys and "
                    "credentials must be stored securely."
                ),
            ))
