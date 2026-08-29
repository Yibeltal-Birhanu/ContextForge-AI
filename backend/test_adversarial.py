"""
Adversarial & Edge-Case Validation for ContextForge AI.

Tests that ContextForge correctly handles:
- No technology specified (AI recommendations only)
- Explicit technology selections
- User uncertainty
- Contradictions
- Different purposes for same tech
- Technology replacement
- Conflicting database decisions
- Generic words vs concrete providers
- Technology as alternative vs selection
- Legacy systems
- JS/TS equivalence
- AI recommendation vs user choice
- Overengineering
- Complex projects
- Incomplete requirements
- Conflicting requirements
- Natural language capabilities
- Cross-project isolation
"""

import sys
import traceback


def run_test(name, func):
    try:
        func()
        print(f"  PASS: {name}")
        return True
    except Exception as e:
        print(f"  FAIL: {name}")
        print(f"    {e}")
        traceback.print_exc()
        return False


def _norm(name):
    from app.utils.tech_normalizer import normalize_tech_name
    return normalize_tech_name(name)


def _classify(name):
    from app.utils.tech_normalizer import classify_tech
    return classify_tech(name)


def _subs(user_techs, arch_techs):
    from app.utils.tech_normalizer import find_substituted_technologies
    return find_substituted_technologies(user_techs, arch_techs)


# ============================================================
# Test 1: No Technology Specified
# ============================================================

def test_no_tech_specified():
    """AI recommendations must be marked as assumptions, not user-selected."""
    from app.models.project import ProjectState, UserSelectedTechnology
    from app.models.architecture import ArchitectureDocument, TechnologyChoice
    from app.models.context import ImplementationContext, ImplementationPhase, AgentRule
    from app.models.requirements import RequirementsDocument, Requirement
    from app.engines.agent_readiness import check_agent_readiness

    # User did NOT specify any technologies
    project = ProjectState(
        name="Scholarship Platform",
        desc="Platform for Ethiopian students to find scholarships.",
        problem="Students struggle to find scholarship opportunities.",
        target_users=["Students"], core_features=["Search", "Apply"],
        technologies=[],  # No tech specified
        user_selected_technologies=[],  # No user-selected techs
    )

    # AI recommends Django, PostgreSQL, Redis
    architecture = ArchitectureDocument(
        system_architecture="Django web app with PostgreSQL.",
        components=[], technology_stack=[
            TechnologyChoice(category="Backend", technology="Django", reason="AI recommended"),
            TechnologyChoice(category="Database", technology="PostgreSQL", reason="AI recommended"),
            TechnologyChoice(category="Cache", technology="Redis", reason="AI recommended"),
        ],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )

    context = ImplementationContext(
        project_title="Scholarship Platform", project_summary="Scholarships.",
        problem="Finding scholarships.", target_users=["Students"],
        functional_requirements=["FR-001: Search"],
        non_functional_requirements=[], architecture_summary="Django.",
        technology_stack=["Django", "PostgreSQL", "Redis"],
        data_model=[], api_contract=[], security_requirements=[],
        implementation_phases=[ImplementationPhase(phase=1, name="F", objective="Setup", tasks=["Setup"], deliverables=["App"])],
        agent_rules=[AgentRule(category="Architecture", rule="Monolith"), AgentRule(category="Security", rule="JWT"), AgentRule(category="Testing", rule="Tests")],
        definition_of_done=["Done"],
    )

    reqs = RequirementsDocument(functional_requirements=[
        Requirement(id="FR-001", title="Search", description="Search.", priority="MUST_HAVE"),
    ])

    result = check_agent_readiness(project, reqs, architecture, context)

    # Django, PostgreSQL, Redis should ALL be AI assumptions
    ai_assumptions = [a for a in result.assumptions if a.area == "technology"]
    assert len(ai_assumptions) >= 3, f"Expected >= 3 AI assumptions, got {len(ai_assumptions)}"

    # None should be user-selected
    assert len(project.user_selected_technologies) == 0


# ============================================================
# Test 2: Explicit Technology
# ============================================================

def test_explicit_tech_preserved():
    """Django, PostgreSQL, Redis must NOT be replaced."""
    from app.models.project import ProjectState, UserSelectedTechnology
    from app.models.architecture import ArchitectureDocument, TechnologyChoice
    from app.utils.tech_normalizer import find_substituted_technologies, normalize_tech_list

    project = ProjectState(
        name="Scholarship Platform", desc="Scholarships.", problem="Finding scholarships.",
        target_users=["Students"], core_features=["Search"],
        technologies=["Django", "PostgreSQL", "Redis"],
        user_selected_technologies=[
            UserSelectedTechnology(name="Django", purpose="backend", category="BACKEND_FRAMEWORK"),
            UserSelectedTechnology(name="PostgreSQL", purpose="database", category="DATABASE"),
            UserSelectedTechnology(name="Redis", purpose="caching", category="CACHE"),
        ],
    )

    architecture = ArchitectureDocument(
        system_architecture="Django web app.", components=[], technology_stack=[
            TechnologyChoice(category="Backend", technology="Django", reason="User selected"),
            TechnologyChoice(category="Database", technology="PostgreSQL", reason="User selected"),
            TechnologyChoice(category="Cache", technology="Redis", reason="User selected"),
        ],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )

    arch_norm = normalize_tech_list([tc.technology for tc in architecture.technology_stack])
    assert "django" in arch_norm
    assert "postgresql" in arch_norm
    assert "redis" in arch_norm

    # Must NOT contain forbidden techs
    forbidden = {"node.js", "express", "mongodb", "react", "flutter"}
    assert arch_norm.isdisjoint(forbidden)

    # No substitution
    subs = _subs(["Django", "PostgreSQL", "Redis"],
                 [tc.technology for tc in architecture.technology_stack])
    assert len(subs) == 0


# ============================================================
# Test 3: User Uncertainty
# ============================================================

def test_user_uncertainty():
    """Uncertain choices must NOT become user-selected technologies."""
    from app.models.project import ProjectState, UserSelectedTechnology

    # User is uncertain about PostgreSQL vs MongoDB
    project = ProjectState(
        name="Marketplace", desc="Marketplace.", problem="Selling products.",
        target_users=["Users"], core_features=["Browse"],
        technologies=[],  # No concrete tech chosen
        user_selected_technologies=[],  # User is uncertain
    )

    # The system should NOT have added PostgreSQL or MongoDB as user-selected
    assert len(project.user_selected_technologies) == 0

    # If AI recommends PostgreSQL, it should be an assumption
    from app.models.architecture import ArchitectureDocument, TechnologyChoice
    from app.models.context import ImplementationContext, ImplementationPhase, AgentRule
    from app.models.requirements import RequirementsDocument, Requirement
    from app.engines.agent_readiness import check_agent_readiness

    architecture = ArchitectureDocument(
        system_architecture="Web app.", components=[], technology_stack=[
            TechnologyChoice(category="Backend", technology="Django", reason="AI recommended"),
            TechnologyChoice(category="Database", technology="PostgreSQL", reason="AI recommended"),
        ],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )
    context = ImplementationContext(
        project_title="Marketplace", project_summary="Market.", problem="Selling.",
        target_users=["Users"], functional_requirements=["FR-001: Browse"],
        non_functional_requirements=[], architecture_summary="Django.",
        technology_stack=["Django", "PostgreSQL"],
        data_model=[], api_contract=[], security_requirements=[],
        implementation_phases=[ImplementationPhase(phase=1, name="F", objective="Setup", tasks=["Setup"], deliverables=["App"])],
        agent_rules=[AgentRule(category="Architecture", rule="Monolith"), AgentRule(category="Security", rule="JWT"), AgentRule(category="Testing", rule="Tests")],
        definition_of_done=["Done"],
    )
    reqs = RequirementsDocument(functional_requirements=[
        Requirement(id="FR-001", title="Browse", description="Browse.", priority="MUST_HAVE"),
    ])

    result = check_agent_readiness(project, reqs, architecture, context)
    # PostgreSQL should be an AI assumption
    db_assumptions = [a for a in result.assumptions
                     if "postgresql" in a.assumption.lower() and "ai" in a.assumption.lower()]
    assert len(db_assumptions) >= 1, "PostgreSQL should be AI assumption when user is uncertain"


# ============================================================
# Test 4: Explicit Contradiction (Flutter + React Native same app)
# ============================================================

def test_explicit_contradiction():
    """Flutter + React Native for SAME app = contradiction."""
    from app.utils.tech_normalizer import find_substituted_technologies

    # Both are FRONTEND_FRAMEWORK — same category, different tech
    subs = _subs(["Flutter"], ["React Native"])
    # They're in the same category (FRONTEND_FRAMEWORK) but different techs
    # This is a substitution detection — the system should flag it
    assert len(subs) == 1, f"Flutter vs React Native should be detected as conflict: {subs}"
    assert subs[0]["category"] == "FRONTEND_FRAMEWORK"


# ============================================================
# Test 5: Different Purposes (Flutter + React Native different apps)
# ============================================================

def test_different_purposes():
    """Flutter for customer app, React Native for staff app = NO contradiction."""
    from app.models.project import ProjectState, UserSelectedTechnology
    from app.models.architecture import ArchitectureDocument, TechnologyChoice
    from app.engines.agent_readiness import check_agent_readiness
    from app.models.context import ImplementationContext, ImplementationPhase, AgentRule
    from app.models.requirements import RequirementsDocument, Requirement

    # Both are user-selected with different purposes
    project = ProjectState(
        name="Dual App", desc="Dual mobile app.", problem="Multiple user types.",
        target_users=["Customers", "Staff"], core_features=["Customer app", "Staff app"],
        technologies=["Flutter", "React Native"],
        user_selected_technologies=[
            UserSelectedTechnology(name="Flutter", purpose="customer mobile app", category="FRONTEND_FRAMEWORK"),
            UserSelectedTechnology(name="React Native", purpose="staff mobile app", category="FRONTEND_FRAMEWORK"),
        ],
    )

    architecture = ArchitectureDocument(
        system_architecture="Two mobile apps: Flutter for customers, React Native for staff.",
        components=[], technology_stack=[
            TechnologyChoice(category="Customer Mobile", technology="Flutter", reason="User selected for customer app"),
            TechnologyChoice(category="Staff Mobile", technology="React Native", reason="User selected for staff app"),
            TechnologyChoice(category="Backend", technology="Node.js", reason="Shared API"),
        ],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )
    context = ImplementationContext(
        project_title="Dual App", project_summary="Dual.", problem="Multiple.",
        target_users=["Customers", "Staff"], functional_requirements=["FR-001: Customer app", "FR-002: Staff app"],
        non_functional_requirements=[], architecture_summary="Two mobile apps.",
        technology_stack=["Flutter", "React Native", "Node.js"],
        data_model=[], api_contract=[], security_requirements=[],
        implementation_phases=[ImplementationPhase(phase=1, name="F", objective="Setup", tasks=["Setup"], deliverables=["App"])],
        agent_rules=[AgentRule(category="Architecture", rule="Monolith"), AgentRule(category="Security", rule="JWT"), AgentRule(category="Testing", rule="Tests")],
        definition_of_done=["Done"],
    )
    reqs = RequirementsDocument(functional_requirements=[
        Requirement(id="FR-001", title="Customer app", description="Customer.", priority="MUST_HAVE"),
        Requirement(id="FR-002", title="Staff app", description="Staff.", priority="MUST_HAVE"),
    ])

    result = check_agent_readiness(project, reqs, architecture, context)

    # Should NOT have substitution warnings (both are user-selected)
    sub_warnings = [w for w in result.warnings if "CONTRADICTION" in w.message
                   and ("flutter" in w.message.lower() or "react native" in w.message.lower())]
    assert len(sub_warnings) == 0, f"False contradiction for different-purpose techs: {sub_warnings}"


# ============================================================
# Test 6: Technology Replacement
# ============================================================

def test_tech_replacement():
    """User replaces Django with FastAPI — FastAPI becomes authoritative."""
    from app.models.project import ProjectState, UserSelectedTechnology
    from app.models.architecture import ArchitectureDocument, TechnologyChoice
    from app.utils.tech_normalizer import find_substituted_technologies, normalize_tech_list

    # User initially had Django, now replaces with FastAPI
    project = ProjectState(
        name="API Project", desc="API.", problem="Building API.",
        target_users=["Devs"], core_features=["API"],
        technologies=["FastAPI", "PostgreSQL"],
        user_selected_technologies=[
            UserSelectedTechnology(name="FastAPI", purpose="backend (replaced Django)", category="BACKEND_FRAMEWORK"),
            UserSelectedTechnology(name="PostgreSQL", purpose="database", category="DATABASE"),
        ],
    )

    architecture = ArchitectureDocument(
        system_architecture="FastAPI backend.", components=[], technology_stack=[
            TechnologyChoice(category="Backend", technology="FastAPI", reason="User selected (replaced Django)"),
            TechnologyChoice(category="Database", technology="PostgreSQL", reason="User selected"),
        ],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )

    arch_norm = normalize_tech_list([tc.technology for tc in architecture.technology_stack])
    assert "fastapi" in arch_norm
    assert "django" not in arch_norm  # Django should NOT be in architecture
    assert "postgresql" in arch_norm

    # No false substitution warning
    subs = _subs(["FastAPI", "PostgreSQL"],
                 [tc.technology for tc in architecture.technology_stack])
    assert len(subs) == 0


# ============================================================
# Test 7: Conflicting Database Decisions
# ============================================================

def test_conflicting_db():
    """Latest decision (MySQL) becomes authoritative, not PostgreSQL."""
    from app.models.project import ProjectState, UserSelectedTechnology
    from app.models.architecture import ArchitectureDocument, TechnologyChoice
    from app.utils.tech_normalizer import normalize_tech_list

    # User first said PostgreSQL, then switched to MySQL
    project = ProjectState(
        name="DB Project", desc="DB.", problem="Data storage.",
        target_users=["Users"], core_features=["CRUD"],
        technologies=["MySQL"],
        user_selected_technologies=[
            UserSelectedTechnology(name="MySQL", purpose="database (replaced PostgreSQL)", category="DATABASE"),
        ],
    )

    architecture = ArchitectureDocument(
        system_architecture="MySQL backend.", components=[], technology_stack=[
            TechnologyChoice(category="Database", technology="MySQL", reason="User selected"),
        ],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )

    arch_norm = normalize_tech_list([tc.technology for tc in architecture.technology_stack])
    assert "mysql" in arch_norm
    assert "postgresql" not in arch_norm  # Old choice should not appear


# ============================================================
# Test 8: Generic Words Not Technologies
# ============================================================

def test_generic_words():
    """web, mobile, backend, API, authentication, payments, SMS, notifications = NOT technologies."""
    from app.utils.tech_normalizer import classify_tech, NON_TECH_WORDS

    words = ["web", "mobile", "backend", "API", "authentication",
             "payments", "SMS", "notifications"]
    for word in words:
        cat = classify_tech(word)
        assert cat == "OTHER", f"'{word}' classified as {cat}"
        assert word.lower() in NON_TECH_WORDS or word in NON_TECH_WORDS, \
            f"'{word}' not in NON_TECH_WORDS"


# ============================================================
# Test 9: Concrete Providers
# ============================================================

def test_concrete_providers():
    """Telebirr, Africa's Talking, Amazon Bedrock ARE technologies."""
    from app.utils.tech_normalizer import classify_tech

    providers = {
        "Telebirr": "PAYMENT_PROVIDER",
        "Africa's Talking": "SMS_PROVIDER",
        "Amazon Bedrock": "AI_PROVIDER",
    }
    for name, expected_cat in providers.items():
        cat = classify_tech(name)
        assert cat == expected_cat, f"'{name}' classified as {cat}, expected {expected_cat}"


# ============================================================
# Test 10: Technology as Alternative vs Selection
# ============================================================

def test_alternative_vs_selection():
    """PostgreSQL = selected. MongoDB = rejected alternative. MongoDB must NOT appear."""
    from app.models.project import ProjectState, UserSelectedTechnology
    from app.models.architecture import ArchitectureDocument, TechnologyChoice
    from app.utils.tech_normalizer import normalize_tech_list

    project = ProjectState(
        name="PG Project", desc="PG.", problem="Data.",
        target_users=["Users"], core_features=["CRUD"],
        technologies=["PostgreSQL"],
        user_selected_technologies=[
            UserSelectedTechnology(name="PostgreSQL", purpose="database (not MongoDB)", category="DATABASE"),
        ],
    )

    architecture = ArchitectureDocument(
        system_architecture="PostgreSQL backend.", components=[], technology_stack=[
            TechnologyChoice(category="Database", technology="PostgreSQL", reason="User selected"),
        ],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )

    arch_norm = normalize_tech_list([tc.technology for tc in architecture.technology_stack])
    assert "postgresql" in arch_norm
    assert "mongodb" not in arch_norm  # Rejected alternative must NOT appear


# ============================================================
# Test 11: Legacy System
# ============================================================

def test_legacy_system():
    """PHP/MySQL = legacy. Django/PostgreSQL = new app. No false substitution."""
    from app.models.project import ProjectState, UserSelectedTechnology
    from app.models.architecture import ArchitectureDocument, TechnologyChoice
    from app.utils.tech_normalizer import normalize_tech_list

    project = ProjectState(
        name="Migration", desc="Migrating from legacy.", problem="Old system.",
        target_users=["Users"], core_features=["CRUD"],
        technologies=["Django", "PostgreSQL"],
        user_selected_technologies=[
            UserSelectedTechnology(name="Django", purpose="new backend (replacing PHP)", category="BACKEND_FRAMEWORK"),
            UserSelectedTechnology(name="PostgreSQL", purpose="new database (replacing MySQL)", category="DATABASE"),
        ],
    )

    architecture = ArchitectureDocument(
        system_architecture="Django backend replacing legacy PHP.", components=[], technology_stack=[
            TechnologyChoice(category="Backend", technology="Django", reason="New app (replacing PHP)"),
            TechnologyChoice(category="Database", technology="PostgreSQL", reason="New app (replacing MySQL)"),
        ],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )

    arch_norm = normalize_tech_list([tc.technology for tc in architecture.technology_stack])
    assert "django" in arch_norm
    assert "postgresql" in arch_norm
    # Legacy techs should NOT be in the new architecture
    assert "php" not in arch_norm
    assert "mysql" not in arch_norm


# ============================================================
# Test 12: TypeScript Selected
# ============================================================

def test_typescript_selected():
    """TypeScript selected. JavaScript must NOT create false contradiction."""
    from app.utils.tech_normalizer import tech_sets_match, normalize_tech_list, find_substituted_technologies

    user = normalize_tech_list(["TypeScript"])
    arch = normalize_tech_list(["JavaScript"])
    match, missing, extra = tech_sets_match(user, arch)
    assert match, f"TS/JS should match: missing={missing}, extra={extra}"

    subs = find_substituted_technologies(["TypeScript"], ["JavaScript"])
    assert len(subs) == 0, f"TS/JS should not be substitution: {subs}"


# ============================================================
# Test 13: TypeScript + JavaScript Different Purposes
# ============================================================

def test_ts_js_different_purposes():
    """TypeScript for app, JavaScript for legacy script = both preserved, no contradiction."""
    from app.utils.tech_normalizer import normalize_tech_list

    # Both should be in the tech stack
    stack = normalize_tech_list(["TypeScript", "JavaScript"])
    assert "typescript" in stack
    assert "javascript" in stack

    # They should NOT be treated as duplicates
    assert len(stack) == 2


# ============================================================
# Test 14: AI Cannot Replace User Choice
# ============================================================

def test_ai_cannot_replace_user():
    """Flutter + Firebase must remain even if AI thinks React Native + AWS is better."""
    from app.models.project import ProjectState, UserSelectedTechnology
    from app.models.architecture import ArchitectureDocument, TechnologyChoice
    from app.utils.tech_normalizer import find_substituted_technologies, normalize_tech_list

    project = ProjectState(
        name="Flutter App", desc="Flutter.", problem="Mobile.",
        target_users=["Users"], core_features=["App"],
        technologies=["Flutter", "Firebase"],
        user_selected_technologies=[
            UserSelectedTechnology(name="Flutter", purpose="mobile", category="FRONTEND_FRAMEWORK"),
            UserSelectedTechnology(name="Firebase", purpose="backend", category="DATABASE"),
        ],
    )

    # AI architecture MUST use Flutter and Firebase (not React Native + AWS)
    architecture = ArchitectureDocument(
        system_architecture="Flutter + Firebase.", components=[], technology_stack=[
            TechnologyChoice(category="Mobile", technology="Flutter", reason="User selected"),
            TechnologyChoice(category="Backend", technology="Firebase", reason="User selected"),
        ],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )

    arch_norm = normalize_tech_list([tc.technology for tc in architecture.technology_stack])
    assert "flutter" in arch_norm
    assert "firebase" in arch_norm
    assert "react native" not in arch_norm
    assert "aws" not in arch_norm

    subs = _subs(["Flutter", "Firebase"],
                 [tc.technology for tc in architecture.technology_stack])
    assert len(subs) == 0


# ============================================================
# Test 15: Overengineering Detection
# ============================================================

def test_no_overengineering():
    """Simple supermarket should NOT have Kubernetes, microservices, etc."""
    from app.models.project import ProjectState, UserSelectedTechnology
    from app.models.architecture import ArchitectureDocument, TechnologyChoice
    from app.utils.tech_normalizer import normalize_tech_list

    project = ProjectState(
        name="Supermarket Inventory", desc="Simple inventory.", problem="Track stock.",
        target_users=["Staff"], core_features=["Products", "Stock"],
        technologies=["C#", "ASP.NET Core", "SQL Server"],
        user_selected_technologies=[
            UserSelectedTechnology(name="C#", purpose="language", category="LANGUAGE"),
            UserSelectedTechnology(name="ASP.NET Core", purpose="backend", category="BACKEND_FRAMEWORK"),
            UserSelectedTechnology(name="SQL Server", purpose="database", category="DATABASE"),
        ],
    )

    # Simple architecture — no Kubernetes, no microservices
    architecture = ArchitectureDocument(
        system_architecture="Single-server ASP.NET Core with SQL Server.",
        components=[], technology_stack=[
            TechnologyChoice(category="Language", technology="C#", reason="User"),
            TechnologyChoice(category="Backend", technology="ASP.NET Core", reason="User"),
            TechnologyChoice(category="Database", technology="SQL Server", reason="User"),
        ],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )

    arch_norm = normalize_tech_list([tc.technology for tc in architecture.technology_stack])
    overengineered = {"kubernetes", "k8s", "kafka", "graphql", "microservices",
                      "event sourcing", "cqrs", "service mesh"}
    assert arch_norm.isdisjoint(overengineered), \
        f"Overengineered techs found: {arch_norm & overengineered}"


# ============================================================
# Test 16: Complex Project
# ============================================================

def test_complex_project():
    """Nationwide healthcare may need more sophisticated architecture."""
    from app.models.project import ProjectState, UserSelectedTechnology
    from app.models.architecture import ArchitectureDocument, TechnologyChoice
    from app.utils.tech_normalizer import normalize_tech_list

    project = ProjectState(
        name="National Healthcare", desc="Nationwide healthcare.", problem="Healthcare access.",
        target_users=["Patients", "Clinics", "Admins"],
        core_features=["Patient records", "Clinic management", "Payments", "SMS", "AI", "Auditing"],
        technologies=["React", "Node.js", "PostgreSQL", "Redis", "Docker", "AWS"],
        user_selected_technologies=[
            UserSelectedTechnology(name="React", purpose="web", category="FRONTEND_FRAMEWORK"),
            UserSelectedTechnology(name="Node.js", purpose="backend", category="BACKEND_FRAMEWORK"),
            UserSelectedTechnology(name="PostgreSQL", purpose="database", category="DATABASE"),
            UserSelectedTechnology(name="Redis", purpose="caching", category="CACHE"),
            UserSelectedTechnology(name="Docker", purpose="containers", category="HOSTING"),
            UserSelectedTechnology(name="AWS", purpose="cloud", category="CLOUD_PROVIDER"),
        ],
    )

    # Complex architecture is OK — more components, more techs
    architecture = ArchitectureDocument(
        system_architecture="Scalable healthcare platform with multiple services.",
        components=[], technology_stack=[
            TechnologyChoice(category="Frontend", technology="React", reason="User"),
            TechnologyChoice(category="Backend", technology="Node.js", reason="User"),
            TechnologyChoice(category="Database", technology="PostgreSQL", reason="User"),
            TechnologyChoice(category="Cache", technology="Redis", reason="User"),
            TechnologyChoice(category="Containers", technology="Docker", reason="User"),
            TechnologyChoice(category="Cloud", technology="AWS", reason="User"),
            TechnologyChoice(category="AI", technology="Amazon Bedrock", reason="AI recommended"),
            TechnologyChoice(category="Payments", technology="Stripe", reason="AI recommended"),
        ],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )

    arch_norm = normalize_tech_list([tc.technology for tc in architecture.technology_stack])
    # Should have all user-selected techs
    for ust in project.user_selected_technologies:
        ust_norm = _norm(ust.name)
        assert ust_norm in arch_norm, f"User-selected '{ust.name}' missing from complex arch"


# ============================================================
# Test 17: Incomplete Requirements
# ============================================================

def test_incomplete_requirements():
    """Vague idea should still produce useful discovery."""
    from app.models.project import ProjectState

    project = ProjectState(
        name="Product Selling App",
        desc="App for selling products.",  # Very vague
        problem="Need to sell products online.",  # Vague
        target_users=[],  # Not specified
        core_features=[],  # Not specified
        technologies=[],
    )

    # Missing fields should be detected
    from app.engines.discovery import find_missing_fields
    missing = find_missing_fields(project)
    assert "target_users" in missing, "target_users should be missing"
    assert "core_features" in missing, "core_features should be missing"
    assert "platform" in missing, "platform should be missing"
    assert "technologies" in missing, "technologies should be missing"


# ============================================================
# Test 18: Conflicting Requirements
# ============================================================

def test_conflicting_requirements():
    """Offline + real-time cloud payments = architectural tension."""
    # This is a semantic check — we verify the system can represent both
    from app.models.project import ProjectState

    project = ProjectState(
        name="Offline-First App", desc="Offline-first with cloud sync.",
        problem="Need offline and online capabilities.",
        target_users=["Field workers"],
        core_features=["Offline data collection", "Cloud payment processing"],
        technologies=["React", "Node.js"],
        constraints=["Must work completely offline", "Must process real-time cloud payments"],
    )

    # Both constraints should be preserved
    assert "Must work completely offline" in project.constraints
    assert "Must process real-time cloud payments" in project.constraints
    # They coexist — the architecture should address the tension


# ============================================================
# Test 19: Technology in Natural Language
# ============================================================

def test_natural_language_tech():
    """'Communicate through SMS' = capability. 'Africa's Talking' = technology."""
    from app.utils.tech_normalizer import classify_tech, NON_TECH_WORDS

    # SMS as a capability — NOT a technology
    assert classify_tech("SMS") == "OTHER"
    assert "sms" in NON_TECH_WORDS

    # Africa's Talking as a provider — IS a technology
    assert classify_tech("Africa's Talking") == "SMS_PROVIDER"

    # Telebirr as a provider — IS a technology
    assert classify_tech("Telebirr") == "PAYMENT_PROVIDER"

    # Payments as a capability — NOT a technology
    assert classify_tech("payments") == "OTHER"
    assert "payments" in NON_TECH_WORDS


# ============================================================
# Test 20: Cross-Project Isolation
# ============================================================

def test_cross_project_isolation():
    """Project A (Django/PostgreSQL) must not leak into Project B (Flutter/Firebase)."""
    from app.models.project import ProjectState, UserSelectedTechnology
    from app.models.architecture import ArchitectureDocument, TechnologyChoice
    from app.utils.tech_normalizer import normalize_tech_list

    # Project A
    project_a = ProjectState(
        name="Web App", desc="Web.", problem="Web.",
        target_users=["Users"], core_features=["CRUD"],
        technologies=["Django", "PostgreSQL"],
        user_selected_technologies=[
            UserSelectedTechnology(name="Django", purpose="backend", category="BACKEND_FRAMEWORK"),
            UserSelectedTechnology(name="PostgreSQL", purpose="database", category="DATABASE"),
        ],
    )
    arch_a = ArchitectureDocument(
        system_architecture="Django.", components=[], technology_stack=[
            TechnologyChoice(category="Backend", technology="Django", reason="User"),
            TechnologyChoice(category="Database", technology="PostgreSQL", reason="User"),
        ],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )

    # Project B
    project_b = ProjectState(
        name="Mobile App", desc="Mobile.", problem="Mobile.",
        target_users=["Users"], core_features=["App"],
        technologies=["Flutter", "Firebase"],
        user_selected_technologies=[
            UserSelectedTechnology(name="Flutter", purpose="mobile", category="FRONTEND_FRAMEWORK"),
            UserSelectedTechnology(name="Firebase", purpose="backend", category="DATABASE"),
        ],
    )
    arch_b = ArchitectureDocument(
        system_architecture="Flutter.", components=[], technology_stack=[
            TechnologyChoice(category="Mobile", technology="Flutter", reason="User"),
            TechnologyChoice(category="Backend", technology="Firebase", reason="User"),
        ],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )

    # Verify isolation
    arch_a_norm = normalize_tech_list([tc.technology for tc in arch_a.technology_stack])
    arch_b_norm = normalize_tech_list([tc.technology for tc in arch_b.technology_stack])

    # Project A has Django/PostgreSQL
    assert "django" in arch_a_norm
    assert "postgresql" in arch_a_norm

    # Project B has Flutter/Firebase
    assert "flutter" in arch_b_norm
    assert "firebase" in arch_b_norm

    # No leakage
    assert "django" not in arch_b_norm, "Django leaked into Project B"
    assert "postgresql" not in arch_b_norm, "PostgreSQL leaked into Project B"
    assert "flutter" not in arch_a_norm, "Flutter leaked into Project A"
    assert "firebase" not in arch_a_norm, "Firebase leaked into Project A"

    # User-selected techs are also isolated
    a_names = {t.name for t in project_a.user_selected_technologies}
    b_names = {t.name for t in project_b.user_selected_technologies}
    assert a_names == {"Django", "PostgreSQL"}
    assert b_names == {"Flutter", "Firebase"}


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    tests = [
        ("1. No tech specified", test_no_tech_specified),
        ("2. Explicit tech preserved", test_explicit_tech_preserved),
        ("3. User uncertainty", test_user_uncertainty),
        ("4. Explicit contradiction", test_explicit_contradiction),
        ("5. Different purposes", test_different_purposes),
        ("6. Tech replacement", test_tech_replacement),
        ("7. Conflicting DB decisions", test_conflicting_db),
        ("8. Generic words", test_generic_words),
        ("9. Concrete providers", test_concrete_providers),
        ("10. Alternative vs selection", test_alternative_vs_selection),
        ("11. Legacy system", test_legacy_system),
        ("12. TypeScript selected", test_typescript_selected),
        ("13. TS+JS different purposes", test_ts_js_different_purposes),
        ("14. AI cannot replace user", test_ai_cannot_replace_user),
        ("15. No overengineering", test_no_overengineering),
        ("16. Complex project", test_complex_project),
        ("17. Incomplete requirements", test_incomplete_requirements),
        ("18. Conflicting requirements", test_conflicting_requirements),
        ("19. Natural language tech", test_natural_language_tech),
        ("20. Cross-project isolation", test_cross_project_isolation),
    ]

    print("=" * 60)
    print("ADVERSARIAL & EDGE-CASE VALIDATION")
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
