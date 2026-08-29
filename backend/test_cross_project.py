"""
Cross-project regression tests for ContextForge AI technology
extraction, normalization, provenance, and consistency.

Tests 5 different project types to ensure the system is
project-independent and does not hardcode HealthLink-specific behavior.
"""

import sys
import traceback


def run_test(name, func):
    """Run a test and report result."""
    try:
        func()
        print(f"  PASS: {name}")
        return True
    except Exception as e:
        print(f"  FAIL: {name}")
        print(f"    {e}")
        traceback.print_exc()
        return False


# ============================================================
# Helper: build a minimal project for testing
# ============================================================

def _make_project(name, desc, problem, features, techs, user_sel=None,
                  db=None, auth=None, integrations=None, platform=None):
    from app.models.project import ProjectState, UserSelectedTechnology
    ust = []
    if user_sel:
        for t in user_sel:
            ust.append(UserSelectedTechnology(**t))
    return ProjectState(
        name=name, description=desc, problem=problem,
        target_users=["Users"], core_features=features,
        technologies=techs, user_selected_technologies=ust,
        database=db, authentication=auth,
        integrations=integrations or [], platform=platform,
    )


def _make_arch(tech_stack, sys_arch="Client-server."):
    from app.models.architecture import ArchitectureDocument, TechnologyChoice
    return ArchitectureDocument(
        system_architecture=sys_arch, components=[],
        technology_stack=[
            TechnologyChoice(category=c, technology=t, reason=r)
            for c, t, r in tech_stack
        ],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )


def _make_ctx(tech_stack, arch_summary="Test.", title="Test"):
    from app.models.context import ImplementationContext, ImplementationPhase, AgentRule
    return ImplementationContext(
        project_title=title, project_summary="Test.", problem="Test.",
        target_users=["Users"], functional_requirements=["FR-001: Feature"],
        non_functional_requirements=[], architecture_summary=arch_summary,
        technology_stack=tech_stack,
        data_model=["Entity"], api_contract=["GET /api"],
        security_requirements=["JWT"],
        implementation_phases=[ImplementationPhase(phase=1, name="F", objective="Setup", tasks=["Setup"], deliverables=["App"])],
        agent_rules=[
            AgentRule(category="Architecture", rule="Monolith"),
            AgentRule(category="Security", rule="JWT"),
            AgentRule(category="Testing", rule="Tests"),
        ],
        definition_of_done=["Done"],
    )


def _make_reqs(features=None):
    from app.models.requirements import RequirementsDocument, Requirement
    feats = features or [("FR-001", "Feature")]
    return RequirementsDocument(
        functional_requirements=[
            Requirement(id=fid, title=t, desc="Test.", priority="MUST_HAVE")
            for fid, t in feats
        ]
    )


# ============================================================
# Tests 1-7: Generic words must NOT be technologies
# ============================================================

def test_generic_not_tech_backend():
    from app.utils.tech_normalizer import normalize_tech_name, NON_TECH_WORDS
    assert "backend" in NON_TECH_WORDS
    assert normalize_tech_name("backend") == ""

def test_generic_not_tech_web():
    from app.utils.tech_normalizer import normalize_tech_name, NON_TECH_WORDS
    assert "web" in NON_TECH_WORDS
    assert normalize_tech_name("web") == ""

def test_generic_not_tech_mobile():
    from app.utils.tech_normalizer import normalize_tech_name, NON_TECH_WORDS
    assert "mobile" in NON_TECH_WORDS
    assert normalize_tech_name("mobile") == ""

def test_generic_not_tech_api():
    from app.utils.tech_normalizer import normalize_tech_name, NON_TECH_WORDS
    assert "api" in NON_TECH_WORDS
    assert normalize_tech_name("api") == ""

def test_generic_not_tech_database():
    from app.utils.tech_normalizer import normalize_tech_name, NON_TECH_WORDS
    assert "database" in NON_TECH_WORDS
    assert normalize_tech_name("database") == ""

def test_generic_not_tech_ai():
    from app.utils.tech_normalizer import normalize_tech_name, NON_TECH_WORDS
    assert "ai" in NON_TECH_WORDS
    assert normalize_tech_name("AI") == ""

def test_generic_not_tech_otp():
    from app.utils.tech_normalizer import normalize_tech_name, NON_TECH_WORDS
    assert "otp" in NON_TECH_WORDS
    assert normalize_tech_name("OTP") == ""


# ============================================================
# Tests 8-14: Real technologies ARE classified correctly
# ============================================================

def test_real_tech_react():
    from app.utils.tech_normalizer import classify_tech
    assert classify_tech("React") == "FRONTEND_FRAMEWORK"

def test_real_tech_postgresql():
    from app.utils.tech_normalizer import classify_tech
    assert classify_tech("PostgreSQL") == "DATABASE"

def test_real_tech_openai():
    from app.utils.tech_normalizer import classify_tech
    assert classify_tech("OpenAI API") == "AI_PROVIDER"

def test_real_tech_telebirr():
    from app.utils.tech_normalizer import classify_tech
    assert classify_tech("Telebirr") == "PAYMENT_PROVIDER"

def test_real_tech_aws():
    from app.utils.tech_normalizer import classify_tech
    assert classify_tech("AWS") == "CLOUD_PROVIDER"

def test_real_tech_containers():
    from app.utils.tech_normalizer import classify_tech
    assert classify_tech("Containers") == "HOSTING"

def test_real_tech_django():
    from app.utils.tech_normalizer import classify_tech
    assert classify_tech("Django") == "BACKEND_FRAMEWORK"


# ============================================================
# Tests 15-20: JS/TS does NOT create false contradiction
# ============================================================

def test_jst_equivelant():
    from app.utils.tech_normalizer import tech_sets_match, normalize_tech_list
    # User says TypeScript, arch uses JavaScript — should match
    user = normalize_tech_list(["TypeScript"])
    arch = normalize_tech_list(["JavaScript"])
    match, missing, extra = tech_sets_match(user, arch)
    assert match, f"JS/TS should match: missing={missing}, extra={extra}"

def test_jst_both_preserved():
    from app.utils.tech_normalizer import tech_sets_match, normalize_tech_list
    # Both JS and TS present — should match
    user = normalize_tech_list(["TypeScript", "JavaScript"])
    arch = normalize_tech_list(["JavaScript", "TypeScript"])
    match, missing, extra = tech_sets_match(user, arch)
    assert match

def test_jst_not_substituted():
    from app.utils.tech_normalizer import find_substituted_technologies
    # TypeScript user-selected, JavaScript in arch — not a substitution
    subs = find_substituted_technologies(["TypeScript"], ["JavaScript"])
    assert len(subs) == 0, f"JS/TS should not be substitution: {subs}"


# ============================================================
# Tests 21-25: Project A — HealthLink
# ============================================================

def test_healthlink_tech_preservation():
    from app.models.project import ProjectState, UserSelectedTechnology
    from app.models.architecture import ArchitectureDocument, TechnologyChoice
    from app.models.context import ImplementationContext, ImplementationPhase, AgentRule
    from app.models.requirements import RequirementsDocument, Requirement
    from app.engines.agent_readiness import check_agent_readiness

    project = ProjectState(
        name="HealthLink", description="Health platform.", problem="Healthcare.",
        target_users=["Patients"], core_features=["AI guidance", "Maps"],
        user_selected_technologies=[
            UserSelectedTechnology(name="React", purpose="frontend", category="FRONTEND_FRAMEWORK"),
            UserSelectedTechnology(name="TypeScript", purpose="language", category="LANGUAGE"),
            UserSelectedTechnology(name="Node.js", purpose="backend", category="BACKEND_FRAMEWORK"),
            UserSelectedTechnology(name="PostgreSQL", purpose="database", category="DATABASE"),
            UserSelectedTechnology(name="OpenAI API", purpose="AI", category="AI_PROVIDER"),
            UserSelectedTechnology(name="Telebirr", purpose="payments", category="PAYMENT_PROVIDER"),
            UserSelectedTechnology(name="Africa's Talking", purpose="SMS", category="SMS_PROVIDER"),
        ],
    )

    architecture = ArchitectureDocument(
        system_architecture="Client-server.",
        components=[], technology_stack=[
            TechnologyChoice(category="Frontend", technology="React", reason="User"),
            TechnologyChoice(category="Language", technology="TypeScript", reason="User"),
            TechnologyChoice(category="Backend", technology="Node.js", reason="User"),
            TechnologyChoice(category="Database", technology="PostgreSQL", reason="User"),
            TechnologyChoice(category="AI", technology="OpenAI API", reason="User"),
            TechnologyChoice(category="Payments", technology="Telebirr", reason="User"),
            TechnologyChoice(category="SMS", technology="Africa's Talking", reason="User"),
        ],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )

    context = ImplementationContext(
        project_title="HealthLink", project_summary="Health.", problem="Healthcare.",
        target_users=["Patients"], functional_requirements=["FR-001: AI"],
        non_functional_requirements=[], architecture_summary="Test.",
        technology_stack=["React", "TypeScript", "Node.js", "PostgreSQL", "OpenAI API", "Telebirr", "Africa's Talking"],
        data_model=[], api_contract=[], security_requirements=[],
        implementation_phases=[ImplementationPhase(phase=1, name="F", objective="Setup", tasks=["Setup"], deliverables=["App"])],
        agent_rules=[AgentRule(category="Architecture", rule="Monolith"), AgentRule(category="Security", rule="JWT"), AgentRule(category="Testing", rule="Tests")],
        definition_of_done=["Done"],
    )

    reqs = RequirementsDocument(functional_requirements=[
        Requirement(id="FR-001", title="AI Guidance", description="AI", priority="MUST_HAVE"),
    ])

    result = check_agent_readiness(project, reqs, architecture, context)
    assert result.checks.technology_consistency >= 90, \
        f"HealthLink tech consistency {result.checks.technology_consistency}% < 90%"
    sub_warnings = [w for w in result.warnings if "CONTRADICTION" in w.message]
    assert len(sub_warnings) == 0, f"Unexpected contradictions: {[w.message for w in sub_warnings]}"


# ============================================================
# Tests 26-30: Project B — Inventory System (C#/.NET)
# ============================================================

def test_inventory_tech_preservation():
    from app.models.project import ProjectState, UserSelectedTechnology
    from app.models.architecture import ArchitectureDocument, TechnologyChoice
    from app.models.context import ImplementationContext, ImplementationPhase, AgentRule
    from app.models.requirements import RequirementsDocument, Requirement
    from app.engines.agent_readiness import check_agent_readiness

    project = ProjectState(
        name="Inventory System", description="Inventory management.", problem="Track stock.",
        target_users=["Warehouse staff"], core_features=["Stock tracking", "Reports"],
        user_selected_technologies=[
            UserSelectedTechnology(name="C#", purpose="language", category="LANGUAGE"),
            UserSelectedTechnology(name="ASP.NET Core", purpose="backend", category="BACKEND_FRAMEWORK"),
            UserSelectedTechnology(name="SQL Server", purpose="database", category="DATABASE"),
            UserSelectedTechnology(name="Entity Framework Core", purpose="ORM", category="ORM"),
        ],
    )

    architecture = ArchitectureDocument(
        system_architecture="Client-server with C# backend.",
        components=[], technology_stack=[
            TechnologyChoice(category="Language", technology="C#", reason="User"),
            TechnologyChoice(category="Backend", technology="ASP.NET Core", reason="User"),
            TechnologyChoice(category="Database", technology="SQL Server", reason="User"),
            TechnologyChoice(category="ORM", technology="Entity Framework Core", reason="User"),
        ],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )

    context = ImplementationContext(
        project_title="Inventory", project_summary="Inventory.", problem="Track stock.",
        target_users=["Staff"], functional_requirements=["FR-001: Stock"],
        non_functional_requirements=[], architecture_summary="C# backend.",
        technology_stack=["C#", "ASP.NET Core", "SQL Server", "Entity Framework Core"],
        data_model=[], api_contract=[], security_requirements=[],
        implementation_phases=[ImplementationPhase(phase=1, name="F", objective="Setup", tasks=["Setup"], deliverables=["App"])],
        agent_rules=[AgentRule(category="Architecture", rule="Monolith"), AgentRule(category="Security", rule="JWT"), AgentRule(category="Testing", rule="Tests")],
        definition_of_done=["Done"],
    )

    reqs = RequirementsDocument(functional_requirements=[
        Requirement(id="FR-001", title="Stock Tracking", description="Track.", priority="MUST_HAVE"),
    ])

    result = check_agent_readiness(project, reqs, architecture, context)
    assert result.checks.technology_consistency >= 90, \
        f"Inventory tech consistency {result.checks.technology_consistency}% < 90%"
    sub_warnings = [w for w in result.warnings if "CONTRADICTION" in w.message]
    assert len(sub_warnings) == 0, f"Unexpected: {[w.message for w in sub_warnings]}"


# ============================================================
# Tests 31-35: Project C — AI/ML System (Python)
# ============================================================

def test_aiml_tech_preservation():
    from app.models.project import ProjectState, UserSelectedTechnology
    from app.models.architecture import ArchitectureDocument, TechnologyChoice
    from app.models.context import ImplementationContext, ImplementationPhase, AgentRule
    from app.models.requirements import RequirementsDocument, Requirement
    from app.engines.agent_readiness import check_agent_readiness

    project = ProjectState(
        name="AI System", description="ML prediction system.", problem="Predict demand.",
        target_users=["Data scientists"], core_features=["Prediction", "Training"],
        user_selected_technologies=[
            UserSelectedTechnology(name="Python", purpose="language", category="LANGUAGE"),
            UserSelectedTechnology(name="FastAPI", purpose="backend", category="BACKEND_FRAMEWORK"),
            UserSelectedTechnology(name="scikit-learn", purpose="ML", category="AI_PROVIDER"),
            UserSelectedTechnology(name="PostgreSQL", purpose="database", category="DATABASE"),
        ],
    )

    architecture = ArchitectureDocument(
        system_architecture="Python ML backend.",
        components=[], technology_stack=[
            TechnologyChoice(category="Language", technology="Python", reason="User"),
            TechnologyChoice(category="Backend", technology="FastAPI", reason="User"),
            TechnologyChoice(category="ML", technology="scikit-learn", reason="User"),
            TechnologyChoice(category="Database", technology="PostgreSQL", reason="User"),
        ],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )

    context = ImplementationContext(
        project_title="AI System", project_summary="ML.", problem="Predict.",
        target_users=["Data scientists"], functional_requirements=["FR-001: Prediction"],
        non_functional_requirements=[], architecture_summary="Python ML.",
        technology_stack=["Python", "FastAPI", "scikit-learn", "PostgreSQL"],
        data_model=[], api_contract=[], security_requirements=[],
        implementation_phases=[ImplementationPhase(phase=1, name="F", objective="Setup", tasks=["Setup"], deliverables=["App"])],
        agent_rules=[AgentRule(category="Architecture", rule="Monolith"), AgentRule(category="Security", rule="JWT"), AgentRule(category="Testing", rule="Tests")],
        definition_of_done=["Done"],
    )

    reqs = RequirementsDocument(functional_requirements=[
        Requirement(id="FR-001", title="Prediction", description="Predict.", priority="MUST_HAVE"),
    ])

    result = check_agent_readiness(project, reqs, architecture, context)
    assert result.checks.technology_consistency >= 90, \
        f"AI/ML tech consistency {result.checks.technology_consistency}% < 90%"
    sub_warnings = [w for w in result.warnings if "CONTRADICTION" in w.message]
    assert len(sub_warnings) == 0, f"Unexpected: {[w.message for w in sub_warnings]}"


# ============================================================
# Tests 36-40: Project D — Mobile App (Flutter)
# ============================================================

def test_flutter_tech_preservation():
    from app.models.project import ProjectState, UserSelectedTechnology
    from app.models.architecture import ArchitectureDocument, TechnologyChoice
    from app.models.context import ImplementationContext, ImplementationPhase, AgentRule
    from app.models.requirements import RequirementsDocument, Requirement
    from app.engines.agent_readiness import check_agent_readiness

    project = ProjectState(
        name="Mobile App", description="Mobile app.", problem="On-the-go access.",
        target_users=["Mobile users"], core_features=["Browse", "Order"],
        user_selected_technologies=[
            UserSelectedTechnology(name="Flutter", purpose="mobile framework", category="FRONTEND_FRAMEWORK"),
            UserSelectedTechnology(name="Dart", purpose="language", category="LANGUAGE"),
            UserSelectedTechnology(name="Firebase", purpose="backend", category="DATABASE"),
        ],
    )

    architecture = ArchitectureDocument(
        system_architecture="Flutter mobile with Firebase.",
        components=[], technology_stack=[
            TechnologyChoice(category="Mobile", technology="Flutter", reason="User"),
            TechnologyChoice(category="Language", technology="Dart", reason="User"),
            TechnologyChoice(category="Backend", technology="Firebase", reason="User"),
        ],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )

    context = ImplementationContext(
        project_title="Mobile App", project_summary="Mobile.", problem="Access.",
        target_users=["Users"], functional_requirements=["FR-001: Browse"],
        non_functional_requirements=[], architecture_summary="Flutter + Firebase.",
        technology_stack=["Flutter", "Dart", "Firebase"],
        data_model=[], api_contract=[], security_requirements=[],
        implementation_phases=[ImplementationPhase(phase=1, name="F", objective="Setup", tasks=["Setup"], deliverables=["App"])],
        agent_rules=[AgentRule(category="Architecture", rule="Monolith"), AgentRule(category="Security", rule="JWT"), AgentRule(category="Testing", rule="Tests")],
        definition_of_done=["Done"],
    )

    reqs = RequirementsDocument(functional_requirements=[
        Requirement(id="FR-001", title="Browse", description="Browse.", priority="MUST_HAVE"),
    ])

    result = check_agent_readiness(project, reqs, architecture, context)
    assert result.checks.technology_consistency >= 90, \
        f"Flutter tech consistency {result.checks.technology_consistency}% < 90%"
    sub_warnings = [w for w in result.warnings if "CONTRADICTION" in w.message]
    assert len(sub_warnings) == 0, f"Unexpected: {[w.message for w in sub_warnings]}"


# ============================================================
# Tests 41-45: Project E — Django Application
# ============================================================

def test_django_tech_preservation():
    from app.models.project import ProjectState, UserSelectedTechnology
    from app.models.architecture import ArchitectureDocument, TechnologyChoice
    from app.models.context import ImplementationContext, ImplementationPhase, AgentRule
    from app.models.requirements import RequirementsDocument, Requirement
    from app.engines.agent_readiness import check_agent_readiness

    project = ProjectState(
        name="Django App", description="Web app.", problem="Data management.",
        target_users=["Admins"], core_features=["CRUD", "Reports"],
        user_selected_technologies=[
            UserSelectedTechnology(name="Python", purpose="language", category="LANGUAGE"),
            UserSelectedTechnology(name="Django", purpose="backend", category="BACKEND_FRAMEWORK"),
            UserSelectedTechnology(name="PostgreSQL", purpose="database", category="DATABASE"),
            UserSelectedTechnology(name="Redis", purpose="caching", category="CACHE"),
        ],
    )

    architecture = ArchitectureDocument(
        system_architecture="Django web app.",
        components=[], technology_stack=[
            TechnologyChoice(category="Language", technology="Python", reason="User"),
            TechnologyChoice(category="Backend", technology="Django", reason="User"),
            TechnologyChoice(category="Database", technology="PostgreSQL", reason="User"),
            TechnologyChoice(category="Cache", technology="Redis", reason="User"),
        ],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )

    context = ImplementationContext(
        project_title="Django App", project_summary="Web.", problem="Data.",
        target_users=["Admins"], functional_requirements=["FR-001: CRUD"],
        non_functional_requirements=[], architecture_summary="Django.",
        technology_stack=["Python", "Django", "PostgreSQL", "Redis"],
        data_model=[], api_contract=[], security_requirements=[],
        implementation_phases=[ImplementationPhase(phase=1, name="F", objective="Setup", tasks=["Setup"], deliverables=["App"])],
        agent_rules=[AgentRule(category="Architecture", rule="Monolith"), AgentRule(category="Security", rule="JWT"), AgentRule(category="Testing", rule="Tests")],
        definition_of_done=["Done"],
    )

    reqs = RequirementsDocument(functional_requirements=[
        Requirement(id="FR-001", title="CRUD", description="CRUD.", priority="MUST_HAVE"),
    ])

    result = check_agent_readiness(project, reqs, architecture, context)
    assert result.checks.technology_consistency >= 90, \
        f"Django tech consistency {result.checks.technology_consistency}% < 90%"
    sub_warnings = [w for w in result.warnings if "CONTRADICTION" in w.message]
    assert len(sub_warnings) == 0, f"Unexpected: {[w.message for w in sub_warnings]}"


# ============================================================
# Tests 46-50: AI assumption does NOT flag user-selected techs
# ============================================================

def test_no_double_counting_user_selected():
    from app.models.project import ProjectState, UserSelectedTechnology
    from app.models.architecture import ArchitectureDocument, TechnologyChoice
    from app.models.context import ImplementationContext, ImplementationPhase, AgentRule
    from app.models.requirements import RequirementsDocument, Requirement
    from app.engines.agent_readiness import check_agent_readiness

    project = ProjectState(
        name="Test", description="Test.", problem="Test.",
        target_users=["Users"], core_features=["Feature"],
        user_selected_technologies=[
            UserSelectedTechnology(name="React", purpose="frontend", category="FRONTEND_FRAMEWORK"),
            UserSelectedTechnology(name="Node.js", purpose="backend", category="BACKEND_FRAMEWORK"),
            UserSelectedTechnology(name="PostgreSQL", purpose="database", category="DATABASE"),
        ],
    )

    architecture = ArchitectureDocument(
        system_architecture="Test.",
        components=[], technology_stack=[
            TechnologyChoice(category="Frontend", technology="React", reason="User"),
            TechnologyChoice(category="Backend", technology="Node.js", reason="User"),
            TechnologyChoice(category="Database", technology="PostgreSQL", reason="User"),
            TechnologyChoice(category="CSS", technology="TailwindCSS", reason="AI recommended"),
        ],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )

    context = ImplementationContext(
        project_title="Test", project_summary="Test.", problem="Test.",
        target_users=["Users"], functional_requirements=["FR-001: Feature"],
        non_functional_requirements=[], architecture_summary="Test.",
        technology_stack=["React", "Node.js", "PostgreSQL", "TailwindCSS"],
        data_model=[], api_contract=[], security_requirements=[],
        implementation_phases=[ImplementationPhase(phase=1, name="F", objective="Setup", tasks=["Setup"], deliverables=["App"])],
        agent_rules=[AgentRule(category="Architecture", rule="Monolith"), AgentRule(category="Security", rule="JWT"), AgentRule(category="Testing", rule="Tests")],
        definition_of_done=["Done"],
    )

    reqs = RequirementsDocument(functional_requirements=[
        Requirement(id="FR-001", title="Feature", description="F", priority="MUST_HAVE"),
    ])

    result = check_agent_readiness(project, reqs, architecture, context)

    # User-selected techs should NOT be AI assumptions
    for tech in ["React", "Node.js", "PostgreSQL"]:
        assumptions = [a for a in result.assumptions
                      if tech.lower() in a.assumption.lower()
                      and "selected by ai" in a.assumption.lower()]
        assert len(assumptions) == 0, f"{tech} should not be AI assumption: {assumptions}"


# ============================================================
# Tests 51-55: Technology sets match correctly
# ============================================================

def test_sets_match_identical():
    from app.utils.tech_normalizer import tech_sets_match, normalize_tech_list
    a = normalize_tech_list(["React", "Node.js", "PostgreSQL"])
    b = normalize_tech_list(["React", "Node.js", "PostgreSQL"])
    match, _, _ = tech_sets_match(a, b)
    assert match

def test_sets_match_fuzzy():
    from app.utils.tech_normalizer import tech_sets_match, normalize_tech_list
    a = normalize_tech_list(["AWS Fargate"])
    b = normalize_tech_list(["Fargate"])
    match, _, _ = tech_sets_match(a, b)
    assert match

def test_sets_detect_real_mismatch():
    from app.utils.tech_normalizer import tech_sets_match, normalize_tech_list
    a = normalize_tech_list(["React"])
    b = normalize_tech_list(["Vue"])
    match, missing, extra = tech_sets_match(a, b)
    assert not match
    assert "react" in missing
    assert "vue" in extra

def test_sets_match_empty():
    from app.utils.tech_normalizer import tech_sets_match
    match, _, _ = tech_sets_match(set(), set())
    assert match

def test_sets_match_superset():
    from app.utils.tech_normalizer import tech_sets_match, normalize_tech_list
    a = normalize_tech_list(["React", "Node.js"])
    b = normalize_tech_list(["React", "Node.js", "PostgreSQL"])
    # Context has extra items — tech_sets_match reports them as extra_in_b
    # but since there's no fuzzy mismatch, it's technically a match issue
    match, missing, extra = tech_sets_match(a, b)
    # arch has 0 missing from ctx, ctx has 1 extra — that's OK for superset
    assert len(missing) == 0  # No arch tech missing from ctx


# ============================================================
# Tests 56-60: Substitution detection
# ============================================================

def test_substitution_openai_bedrock():
    from app.utils.tech_normalizer import find_substituted_technologies
    subs = find_substituted_technologies(["OpenAI API"], ["Amazon Bedrock"])
    assert len(subs) == 1
    assert subs[0]["category"] == "AI_PROVIDER"

def test_substitution_none_different_category():
    from app.utils.tech_normalizer import find_substituted_technologies
    subs = find_substituted_technologies(["React"], ["PostgreSQL"])
    # Different categories — not a substitution
    assert len(subs) == 0

def test_substitution_stripe_telebirr():
    from app.utils.tech_normalizer import find_substituted_technologies
    subs = find_substituted_technologies(["Telebirr"], ["Stripe"])
    assert len(subs) == 1
    assert subs[0]["category"] == "PAYMENT_PROVIDER"

def test_substitution_none_when_same():
    from app.utils.tech_normalizer import find_substituted_technologies
    subs = find_substituted_technologies(["PostgreSQL"], ["PostgreSQL"])
    assert len(subs) == 0

def test_substitution_multiple():
    from app.utils.tech_normalizer import find_substituted_technologies
    subs = find_substituted_technologies(
        ["OpenAI API", "Telebirr"],
        ["Amazon Bedrock", "Stripe"]
    )
    assert len(subs) == 2


# ============================================================
# Tests 61-65: Normalize handles various formats
# ============================================================

def test_normalize_react_version():
    from app.utils.tech_normalizer import normalize_tech_name
    assert normalize_tech_name("React 18") == "react"
    assert normalize_tech_name("React 19") == "react"

def test_normalize_nextjs():
    from app.utils.tech_normalizer import normalize_tech_name
    assert normalize_tech_name("Next.js 14") == "next.js"
    assert normalize_tech_name("Next.js 15") == "next.js"

def test_normalize_compound():
    from app.utils.tech_normalizer import normalize_tech_list
    result = normalize_tech_list(["React - Frontend", "Node.js - Backend"])
    assert "react" in result
    assert "node.js" in result

def test_normalize_empty():
    from app.utils.tech_normalizer import normalize_tech_name
    assert normalize_tech_name("") == ""
    assert normalize_tech_name("   ") == ""

def test_normalize_docker_compose():
    from app.utils.tech_normalizer import normalize_tech_name
    assert normalize_tech_name("Docker Compose") == "docker compose"


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    tests = [
        # Generic words NOT technologies (7)
        ("Generic: backend", test_generic_not_tech_backend),
        ("Generic: web", test_generic_not_tech_web),
        ("Generic: mobile", test_generic_not_tech_mobile),
        ("Generic: API", test_generic_not_tech_api),
        ("Generic: database", test_generic_not_tech_database),
        ("Generic: AI", test_generic_not_tech_ai),
        ("Generic: OTP", test_generic_not_tech_otp),
        # Real technologies classified (7)
        ("Real: React", test_real_tech_react),
        ("Real: PostgreSQL", test_real_tech_postgresql),
        ("Real: OpenAI", test_real_tech_openai),
        ("Real: Telebirr", test_real_tech_telebirr),
        ("Real: AWS", test_real_tech_aws),
        ("Real: Containers", test_real_tech_containers),
        ("Real: Django", test_real_tech_django),
        # JS/TS (3)
        ("JS/TS: equivalent", test_jst_equivelant),
        ("JS/TS: both preserved", test_jst_both_preserved),
        ("JS/TS: not substituted", test_jst_not_substituted),
        # Project A: HealthLink (1)
        ("Project A: HealthLink", test_healthlink_tech_preservation),
        # Project B: Inventory (1)
        ("Project B: Inventory C#/.NET", test_inventory_tech_preservation),
        # Project C: AI/ML (1)
        ("Project C: AI/ML Python", test_aiml_tech_preservation),
        # Project D: Flutter (1)
        ("Project D: Flutter Mobile", test_flutter_tech_preservation),
        # Project E: Django (1)
        ("Project E: Django App", test_django_tech_preservation),
        # No double counting (1)
        ("No double counting user-selected", test_no_double_counting_user_selected),
        # Tech sets match (5)
        ("Sets: identical", test_sets_match_identical),
        ("Sets: fuzzy", test_sets_match_fuzzy),
        ("Sets: real mismatch", test_sets_detect_real_mismatch),
        ("Sets: empty", test_sets_match_empty),
        ("Sets: superset", test_sets_match_superset),
        # Substitution (5)
        ("Sub: OpenAI->Bedrock", test_substitution_openai_bedrock),
        ("Sub: different categories", test_substitution_none_different_category),
        ("Sub: Telebirr->Stripe", test_substitution_stripe_telebirr),
        ("Sub: same tech", test_substitution_none_when_same),
        ("Sub: multiple", test_substitution_multiple),
        # Normalize (5)
        ("Norm: React version", test_normalize_react_version),
        ("Norm: Next.js", test_normalize_nextjs),
        ("Norm: compound", test_normalize_compound),
        ("Norm: empty", test_normalize_empty),
        ("Norm: Docker Compose", test_normalize_docker_compose),
    ]

    print("=" * 60)
    print("CROSS-PROJECT REGRESSION TESTS")
    print("=" * 60)

    results = []
    for name, func in tests:
        results.append(run_test(name, func))

    passed = sum(results)
    total = len(results)

    print(f"\n{'=' * 60}")
    print(f"RESULTS: {passed}/{total} passed")
    print(f"{'=' * 60}")

    if passed < total:
        sys.exit(1)
    else:
        print("ALL TESTS PASSED")
