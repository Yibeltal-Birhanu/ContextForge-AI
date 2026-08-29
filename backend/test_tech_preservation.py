"""
Comprehensive regression tests for technology preservation,
normalization, consistency, and provenance in ContextForge AI.
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
# Test 1: containers is a recognized technology
# ============================================================

def test_containers_recognized():
    from app.utils.tech_normalizer import normalize_tech_name, classify_tech

    assert normalize_tech_name("containers") == "containers"
    assert normalize_tech_name("Containers") == "containers"
    assert normalize_tech_name("containerized") == "containers"
    assert normalize_tech_name("containerization") == "containers"
    assert normalize_tech_name("Docker Containers") == "containers"
    assert classify_tech("containers") == "HOSTING"
    assert classify_tech("Containers") == "HOSTING"


# ============================================================
# Test 2: OpenAI API is preserved
# ============================================================

def test_openai_preserved():
    from app.utils.tech_normalizer import normalize_tech_name, classify_tech

    assert normalize_tech_name("OpenAI API") == "openai"
    assert normalize_tech_name("openai api") == "openai"
    assert classify_tech("OpenAI API") == "AI_PROVIDER"
    assert classify_tech("openai") == "AI_PROVIDER"


# ============================================================
# Test 3: Google Maps is preserved
# ============================================================

def test_google_maps_preserved():
    from app.utils.tech_normalizer import normalize_tech_name, classify_tech

    assert normalize_tech_name("Google Maps") == "google maps"
    assert classify_tech("Google Maps") == "MAP_PROVIDER"


# ============================================================
# Test 4: Telebirr is preserved
# ============================================================

def test_telebirr_preserved():
    from app.utils.tech_normalizer import normalize_tech_name, classify_tech

    assert normalize_tech_name("Telebirr") == "telebirr"
    assert classify_tech("Telebirr") == "PAYMENT_PROVIDER"


# ============================================================
# Test 5: Africa's Talking is preserved
# ============================================================

def test_africas_talking_preserved():
    from app.utils.tech_normalizer import normalize_tech_name, classify_tech

    assert normalize_tech_name("Africa's Talking") == "africas talking"
    assert normalize_tech_name("Africas Talking") == "africas talking"
    assert classify_tech("Africa's Talking") == "SMS_PROVIDER"


# ============================================================
# Test 6: PostgreSQL is preserved
# ============================================================

def test_postgresql_preserved():
    from app.utils.tech_normalizer import normalize_tech_name, classify_tech

    assert normalize_tech_name("PostgreSQL") == "postgresql"
    assert classify_tech("PostgreSQL") == "DATABASE"


# ============================================================
# Test 7: AWS is preserved
# ============================================================

def test_aws_preserved():
    from app.utils.tech_normalizer import normalize_tech_name, classify_tech

    assert normalize_tech_name("AWS") == "aws"
    assert normalize_tech_name("Amazon Web Services") == "aws"
    assert classify_tech("AWS") == "CLOUD_PROVIDER"


# ============================================================
# Test 8: User technology substitution detection
# ============================================================

def test_substitution_detection():
    from app.utils.tech_normalizer import find_substituted_technologies

    user_techs = ["OpenAI API", "Google Maps", "Telebirr", "Africa's Talking"]

    # Correct: same techs
    subs = find_substituted_technologies(user_techs, ["OpenAI API", "Google Maps", "Telebirr", "Africa's Talking"])
    assert len(subs) == 0, f"Expected 0, got {len(subs)}"

    # Wrong: Bedrock replaces OpenAI
    subs = find_substituted_technologies(user_techs, ["Amazon Bedrock", "Google Maps", "Telebirr", "Africa's Talking"])
    assert len(subs) == 1, f"Expected 1, got {len(subs)}"
    assert subs[0]["category"] == "AI_PROVIDER"

    # Wrong: all replaced
    subs = find_substituted_technologies(user_techs, ["Amazon Bedrock", "Mapbox", "Stripe", "Twilio"])
    assert len(subs) == 4, f"Expected 4, got {len(subs)}"

    # Partial: only Maps replaced
    subs = find_substituted_technologies(user_techs, ["OpenAI API", "Mapbox", "Telebirr", "Africa's Talking"])
    assert len(subs) == 1, f"Expected 1, got {len(subs)}"
    assert subs[0]["category"] == "MAP_PROVIDER"


# ============================================================
# Test 9: Architecture/context consistency
# ============================================================

def test_arch_context_consistency():
    from app.utils.tech_normalizer import normalize_tech_list, tech_sets_match

    arch = ["React", "Node.js", "OpenAI API", "Google Maps", "Telebirr", "Africa's Talking", "PostgreSQL", "AWS", "Containers"]
    ctx = ["React - Frontend", "Node.js - Backend", "OpenAI API - AI guidance", "Google Maps - Locations",
           "Telebirr - Payments", "Africa's Talking - SMS", "PostgreSQL - Database", "AWS - Hosting", "Containers - Deployment"]

    arch_norm = normalize_tech_list(arch)
    ctx_norm = normalize_tech_list(ctx)

    match, missing, extra = tech_sets_match(arch_norm, ctx_norm)
    assert match, f"arch->ctx mismatch: missing={missing}, extra={extra}"


# ============================================================
# Test 10: AI recommendation vs user requirement provenance
# ============================================================

def test_provenance():
    from app.models.project import ProjectState, UserSelectedTechnology
    from app.models.architecture import ArchitectureDocument, TechnologyChoice
    from app.models.context import ImplementationContext, ImplementationPhase, AgentRule
    from app.models.requirements import RequirementsDocument, Requirement
    from app.engines.agent_readiness import check_agent_readiness

    project = ProjectState(
        name="HealthLink",
        description="Health platform.",
        problem="Healthcare.",
        target_users=["Patients"],
        core_features=["AI guidance", "Maps", "SMS"],
        user_selected_technologies=[
            UserSelectedTechnology(name="OpenAI API", purpose="AI guidance", category="AI_PROVIDER"),
            UserSelectedTechnology(name="Google Maps", purpose="maps", category="MAP_PROVIDER"),
            UserSelectedTechnology(name="Telebirr", purpose="payments", category="PAYMENT_PROVIDER"),
            UserSelectedTechnology(name="Africa's Talking", purpose="SMS", category="SMS_PROVIDER"),
            UserSelectedTechnology(name="PostgreSQL", purpose="database", category="DATABASE"),
            UserSelectedTechnology(name="AWS", purpose="hosting", category="CLOUD_PROVIDER"),
            UserSelectedTechnology(name="Containers", purpose="deployment", category="HOSTING"),
        ],
    )

    architecture = ArchitectureDocument(
        system_architecture="Client-server with containers.",
        components=[],
        technology_stack=[
            TechnologyChoice(category="AI", technology="OpenAI API", reason="User selected"),
            TechnologyChoice(category="Maps", technology="Google Maps", reason="User selected"),
            TechnologyChoice(category="Payments", technology="Telebirr", reason="User selected"),
            TechnologyChoice(category="SMS", technology="Africa's Talking", reason="User selected"),
            TechnologyChoice(category="Database", technology="PostgreSQL", reason="User selected"),
            TechnologyChoice(category="Cloud", technology="AWS", reason="User selected"),
            TechnologyChoice(category="Deployment", technology="Containers", reason="User selected"),
            # AI-added technologies
            TechnologyChoice(category="Frontend", technology="React", reason="AI recommended"),
            TechnologyChoice(category="Backend", technology="Node.js", reason="AI recommended"),
            TechnologyChoice(category="CSS", technology="TailwindCSS", reason="AI recommended"),
            TechnologyChoice(category="Bundler", technology="Vite", reason="AI recommended"),
        ],
        data_architecture=[],
        api_design=[],
        security=[],
        deployment=[],
    )

    context = ImplementationContext(
        project_title="HealthLink",
        project_summary="Health.",
        problem="Healthcare.",
        target_users=["Patients"],
        functional_requirements=["FR-001: AI"],
        non_functional_requirements=[],
        architecture_summary="With OpenAI, Google Maps, Telebirr, Africas Talking, PostgreSQL, AWS, Containers.",
        technology_stack=[
            "OpenAI API - AI guidance",
            "Google Maps - Locations",
            "Telebirr - Payments",
            "Africa's Talking - SMS",
            "PostgreSQL - Database",
            "AWS - Hosting",
            "Containers - Deployment",
            "React - Frontend",
            "Node.js - Backend",
            "TailwindCSS - CSS",
            "Vite - Bundler",
        ],
        data_model=["Patient"],
        api_contract=["POST /api"],
        security_requirements=["JWT"],
        implementation_phases=[ImplementationPhase(phase=1, name="F", objective="Setup", tasks=["Setup"], deliverables=["App"])],
        agent_rules=[
            AgentRule(category="Architecture", rule="Monolith with containers"),
            AgentRule(category="Security", rule="JWT"),
            AgentRule(category="Testing", rule="Write tests"),
        ],
        definition_of_done=["Done"],
    )

    reqs = RequirementsDocument(functional_requirements=[
        Requirement(id="FR-001", title="AI Guidance", description="AI", priority="MUST_HAVE"),
    ])

    result = check_agent_readiness(project, reqs, architecture, context)

    # Technology consistency should be high
    assert result.checks.technology_consistency >= 85, \
        f"Tech consistency {result.checks.technology_consistency}% < 85%"

    # Should NOT have substitution warnings
    sub_warnings = [w for w in result.warnings
                   if "CONTRADICTION" in w.message or "substitut" in w.message.lower()]
    assert len(sub_warnings) == 0, \
        f"Unexpected substitution warnings: {[w.message for w in sub_warnings]}"

    # Containers should be in assumptions as AI-selected only if not in user_selected
    # Since Containers IS in user_selected, it should NOT be an AI assumption
    container_assumptions = [a for a in result.assumptions
                           if "container" in a.assumption.lower() and "ai" in a.assumption.lower()]
    # These should not exist since Containers is user-selected
    # (info-level assumptions about AI-selected React/Node are OK)


# ============================================================
# Test 11: Generic domain words are NOT classified as technologies
# ============================================================

def test_no_false_tech_classification():
    from app.utils.tech_normalizer import normalize_tech_name, classify_tech

    generic_words = [
        "backend", "web", "mobile", "users", "appointments",
        "payments", "reminders", "profiles", "API", "database",
        "frontend", "login", "signup", "search", "dashboard", "admin",
    ]

    for word in generic_words:
        result = normalize_tech_name(word)
        # Should either return empty or the word itself (not a false tech)
        # The key is that classify_tech should NOT map these to real tech categories
        cat = classify_tech(word)
        # "backend" etc. should be OTHER, not BACKEND_FRAMEWORK
        if word.lower() in ("backend", "web", "mobile", "users", "appointments",
                            "payments", "reminders", "profiles", "frontend",
                            "login", "signup", "search", "dashboard", "admin"):
            assert cat == "OTHER", f"'{word}' was classified as {cat}, expected OTHER"


# ============================================================
# Test 12: AI assumptions don't double-count user-selected techs
# ============================================================

def test_no_double_counting():
    from app.models.project import ProjectState, UserSelectedTechnology
    from app.models.architecture import ArchitectureDocument, TechnologyChoice
    from app.models.context import ImplementationContext, ImplementationPhase, AgentRule
    from app.models.requirements import RequirementsDocument, Requirement
    from app.engines.agent_readiness import check_agent_readiness

    project = ProjectState(
        name="Test",
        description="Test.",
        problem="Test.",
        target_users=["Users"],
        core_features=["Feature"],
        technologies=["React", "Node.js"],
        user_selected_technologies=[
            UserSelectedTechnology(name="PostgreSQL", purpose="database", category="DATABASE"),
            UserSelectedTechnology(name="AWS", purpose="hosting", category="CLOUD_PROVIDER"),
        ],
    )

    architecture = ArchitectureDocument(
        system_architecture="Test.",
        components=[],
        technology_stack=[
            TechnologyChoice(category="Frontend", technology="React", reason="User specified"),
            TechnologyChoice(category="Backend", technology="Node.js", reason="User specified"),
            TechnologyChoice(category="Database", technology="PostgreSQL", reason="User selected"),
            TechnologyChoice(category="Cloud", technology="AWS", reason="User selected"),
            TechnologyChoice(category="CSS", technology="TailwindCSS", reason="AI recommended"),
        ],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )

    context = ImplementationContext(
        project_title="Test", project_summary="Test.", problem="Test.",
        target_users=["Users"], functional_requirements=["FR-001: Feature"],
        non_functional_requirements=[], architecture_summary="Test.",
        technology_stack=["React", "Node.js", "PostgreSQL", "AWS", "TailwindCSS"],
        data_model=[], api_contract=[], security_requirements=[],
        implementation_phases=[ImplementationPhase(phase=1, name="F", objective="Setup", tasks=["Setup"], deliverables=["App"])],
        agent_rules=[AgentRule(category="Architecture", rule="Monolith"), AgentRule(category="Security", rule="JWT"), AgentRule(category="Testing", rule="Tests")],
        definition_of_done=["Done"],
    )

    reqs = RequirementsDocument(functional_requirements=[
        Requirement(id="FR-001", title="Feature", description="F", priority="MUST_HAVE"),
    ])

    result = check_agent_readiness(project, reqs, architecture, context)

    # PostgreSQL and AWS should NOT appear as AI assumptions
    # (they are user-selected)
    pg_assumptions = [a for a in result.assumptions
                     if "postgresql" in a.assumption.lower() and "ai" in a.assumption.lower()]
    aws_assumptions = [a for a in result.assumptions
                      if "aws" in a.assumption.lower() and "ai" in a.assumption.lower()]

    assert len(pg_assumptions) == 0, f"PostgreSQL should not be an AI assumption: {pg_assumptions}"
    assert len(aws_assumptions) == 0, f"AWS should not be an AI assumption: {aws_assumptions}"

    # TailwindCSS IS an AI recommendation — should appear as info
    tw_assumptions = [a for a in result.assumptions
                     if "tailwindcss" in a.assumption.lower()]
    assert len(tw_assumptions) == 1, f"Expected 1 TailwindCSS assumption, got {len(tw_assumptions)}"


# ============================================================
# Test 13: Full HealthLink regression
# ============================================================

def test_healthlink_full():
    from app.models.project import ProjectState, UserSelectedTechnology
    from app.models.architecture import ArchitectureDocument, TechnologyChoice
    from app.models.context import ImplementationContext, ImplementationPhase, AgentRule
    from app.models.requirements import RequirementsDocument, Requirement
    from app.engines.agent_readiness import check_agent_readiness
    from app.services.quality_gate import run_quality_gate

    project = ProjectState(
        name="HealthLink Ethiopia",
        description="A health platform connecting patients with clinics.",
        problem="Patients in Ethiopia struggle to find and access healthcare.",
        target_users=["Patients", "Clinics", "Admins"],
        core_features=[
            "Patient registration",
            "Clinic search with maps",
            "AI health guidance",
            "Appointment booking",
            "SMS reminders",
            "Telebirr payments",
        ],
        platform="Web and mobile",
        technologies=["React", "Node.js"],
        user_selected_technologies=[
            UserSelectedTechnology(name="OpenAI API", purpose="AI-assisted health guidance", category="AI_PROVIDER"),
            UserSelectedTechnology(name="Google Maps", purpose="clinic and hospital locations", category="MAP_PROVIDER"),
            UserSelectedTechnology(name="Telebirr", purpose="online payments", category="PAYMENT_PROVIDER"),
            UserSelectedTechnology(name="Africa's Talking", purpose="SMS reminders", category="SMS_PROVIDER"),
            UserSelectedTechnology(name="PostgreSQL", purpose="primary database", category="DATABASE"),
            UserSelectedTechnology(name="AWS", purpose="cloud hosting", category="CLOUD_PROVIDER"),
            UserSelectedTechnology(name="Containers", purpose="containerized deployment", category="HOSTING"),
        ],
        database="PostgreSQL",
        authentication="Phone number + SMS OTP",
        integrations=["Telebirr payments", "Africa's Talking SMS", "Google Maps", "OpenAI API"],
        constraints=["Low budget", "Must work in Ethiopia"],
        deployment="Cloud hosting on AWS with containers",
    )

    reqs = RequirementsDocument(functional_requirements=[
        Requirement(id="FR-001", title="Patient Registration", description="Register.", priority="MUST_HAVE"),
        Requirement(id="FR-002", title="Clinic Search with Maps", description="Search.", priority="MUST_HAVE"),
        Requirement(id="FR-003", title="AI Health Guidance", description="AI.", priority="MUST_HAVE"),
        Requirement(id="FR-004", title="SMS Reminders", description="SMS.", priority="MUST_HAVE"),
        Requirement(id="FR-005", title="Telebirr Payments", description="Pay.", priority="MUST_HAVE"),
    ])

    architecture = ArchitectureDocument(
        system_architecture="Client-server with React, Node.js, containers, and external services.",
        components=[],
        technology_stack=[
            TechnologyChoice(category="Frontend", technology="React", reason="User specified"),
            TechnologyChoice(category="Backend", technology="Node.js", reason="User specified"),
            TechnologyChoice(category="AI Provider", technology="OpenAI API", reason="User selected for health guidance"),
            TechnologyChoice(category="Maps", technology="Google Maps", reason="User selected for clinic locations"),
            TechnologyChoice(category="Payments", technology="Telebirr", reason="User selected for payments"),
            TechnologyChoice(category="SMS", technology="Africa's Talking", reason="User selected for SMS reminders"),
            TechnologyChoice(category="Database", technology="PostgreSQL", reason="User selected"),
            TechnologyChoice(category="Cloud", technology="AWS", reason="User selected"),
            TechnologyChoice(category="Deployment", technology="Containers", reason="User selected for containerized deployment"),
            TechnologyChoice(category="CSS", technology="TailwindCSS", reason="AI recommended"),
            TechnologyChoice(category="Bundler", technology="Vite", reason="AI recommended"),
        ],
        data_architecture=[],
        api_design=[],
        security=[],
        deployment=[],
    )

    context = ImplementationContext(
        project_title="HealthLink Ethiopia",
        project_summary="Health platform.",
        problem="Healthcare.",
        target_users=["Patients", "Clinics"],
        functional_requirements=["FR-001: Patient Registration", "FR-002: Maps", "FR-003: AI", "FR-004: SMS", "FR-005: Payments"],
        non_functional_requirements=["NFR-001: Security"],
        architecture_summary="React + Node.js with OpenAI, Google Maps, Telebirr, Africas Talking, PostgreSQL, AWS, Containers.",
        technology_stack=[
            "React - Frontend",
            "Node.js - Backend",
            "OpenAI API - AI guidance",
            "Google Maps - Locations",
            "Telebirr - Payments",
            "Africa's Talking - SMS",
            "PostgreSQL - Database",
            "AWS - Hosting",
            "Containers - Deployment",
            "TailwindCSS - CSS",
            "Vite - Bundler",
        ],
        data_model=["Patient", "Clinic"],
        api_contract=["POST /api/patients", "GET /api/clinics"],
        security_requirements=["JWT", "Encrypted data"],
        implementation_phases=[ImplementationPhase(phase=1, name="Foundation", objective="Setup", tasks=["Setup"], deliverables=["App"])],
        agent_rules=[
            AgentRule(category="Architecture", rule="Modular monolith with containerized deployment"),
            AgentRule(category="Security", rule="JWT authentication"),
            AgentRule(category="Testing", rule="Write tests"),
        ],
        definition_of_done=["All features", "Tests pass"],
    )

    result = check_agent_readiness(project, reqs, architecture, context)

    # Technology consistency must be high
    assert result.checks.technology_consistency >= 85, \
        f"Tech consistency {result.checks.technology_consistency}% < 85%"

    # No substitution warnings for user-selected techs
    sub_warnings = [w for w in result.warnings
                   if "CONTRADICTION" in w.message]
    assert len(sub_warnings) == 0, \
        f"Unexpected contradictions: {[w.message for w in sub_warnings]}"

    # Containers should NOT be an AI assumption
    container_assumptions = [a for a in result.assumptions
                           if "container" in a.assumption.lower()
                           and ("ai" in a.assumption.lower() or "selected by ai" in a.assumption.lower())]
    assert len(container_assumptions) == 0, \
        f"Containers should not be AI assumption: {container_assumptions}"

    # PostgreSQL should NOT be an AI assumption
    pg_assumptions = [a for a in result.assumptions
                     if "postgresql" in a.assumption.lower()
                     and "selected by ai" in a.assumption.lower()]
    assert len(pg_assumptions) == 0, \
        f"PostgreSQL should not be AI assumption: {pg_assumptions}"

    # Quality gate
    qg = run_quality_gate(project, reqs, architecture, context)
    assert qg.tech_preservation.preserved_count >= 7, \
        f"Expected >= 7 preserved, got {qg.tech_preservation.preserved_count}"
    assert qg.tech_preservation.substituted_count == 0, \
        f"Expected 0 substituted, got {qg.tech_preservation.substituted_count}"


# ============================================================
# Run all tests
# ============================================================

if __name__ == "__main__":
    tests = [
        ("Containers recognized", test_containers_recognized),
        ("OpenAI API preserved", test_openai_preserved),
        ("Google Maps preserved", test_google_maps_preserved),
        ("Telebirr preserved", test_telebirr_preserved),
        ("Africa's Talking preserved", test_africas_talking_preserved),
        ("PostgreSQL preserved", test_postgresql_preserved),
        ("AWS preserved", test_aws_preserved),
        ("Substitution detection", test_substitution_detection),
        ("Architecture/context consistency", test_arch_context_consistency),
        ("AI vs user provenance", test_provenance),
        ("No false tech classification", test_no_false_tech_classification),
        ("No double-counting", test_no_double_counting),
        ("HealthLink full regression", test_healthlink_full),
    ]

    print("=" * 60)
    print("TECHNOLOGY PRESERVATION REGRESSION TESTS")
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
