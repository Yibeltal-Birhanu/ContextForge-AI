"""
Full Multi-Project Pipeline Validation for ContextForge AI.

Tests the deterministic parts of the pipeline:
- Technology preservation through discovery -> architecture -> context
- Validation logic
- Quality gate logic
- Architecture/context consistency
- No false contradictions
- No generic concepts classified as technologies

Each project is modeled with realistic data that ContextForge would
generate after running through the LLM-dependent stages.
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


# ============================================================
# Helpers
# ============================================================

def _make_project(name, desc, problem, features, techs, user_sel=None,
                  db=None, auth=None, integrations=None, platform=None,
                  constraints=None, deployment=None):
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
        constraints=constraints or [], deployment=deployment,
    )


def _make_arch(tech_stack, sys_arch="Client-server.", components=None,
               data_arch=None, api_design=None, security=None, deployment=None):
    from app.models.architecture import ArchitectureDocument, TechnologyChoice
    return ArchitectureDocument(
        system_architecture=sys_arch,
        components=components or [],
        technology_stack=[
            TechnologyChoice(category=c, technology=t, reason=r)
            for c, t, r in tech_stack
        ],
        data_architecture=data_arch or [],
        api_design=api_design or [],
        security=security or [],
        deployment=deployment or [],
    )


def _make_ctx(tech_stack, title="Test", arch_summary="Test.",
              frs=None, nfrs=None, data_model=None, api_contract=None,
              security=None, phases=None, agent_rules=None, dod=None):
    from app.models.context import ImplementationContext, ImplementationPhase, AgentRule
    return ImplementationContext(
        project_title=title, project_summary="Test.", problem="Test.",
        target_users=["Users"],
        functional_requirements=frs or ["FR-001: Feature"],
        non_functional_requirements=nfrs or [],
        architecture_summary=arch_summary,
        technology_stack=tech_stack,
        data_model=data_model or ["Entity"],
        api_contract=api_contract or ["GET /api"],
        security_requirements=security or ["JWT"],
        implementation_phases=phases or [
            ImplementationPhase(phase=1, name="F", objective="Setup",
                              tasks=["Setup"], deliverables=["App"])
        ],
        agent_rules=agent_rules or [
            AgentRule(category="Architecture", rule="Monolith"),
            AgentRule(category="Security", rule="JWT"),
            AgentRule(category="Testing", rule="Tests"),
        ],
        definition_of_done=dod or ["Done"],
    )


def _make_reqs(frs=None):
    from app.models.requirements import RequirementsDocument, Requirement
    feats = frs or [("FR-001", "Feature")]
    return RequirementsDocument(
        functional_requirements=[
            Requirement(id=fid, title=t, description="Test.", priority="MUST_HAVE")
            for fid, t in feats
        ]
    )


# ============================================================
# PROJECT 1: HealthLink Ethiopia
# ============================================================

def test_healthlink_pipeline():
    from app.engines.agent_readiness import check_agent_readiness
    from app.engines.validation import validate_context
    from app.services.quality_gate import run_quality_gate
    from app.utils.tech_normalizer import normalize_tech_list, tech_sets_match

    project = _make_project(
        name="HealthLink Ethiopia",
        desc="Healthcare platform connecting patients with doctors and clinics.",
        problem="Patients in Ethiopia struggle to find and access healthcare.",
        features=["Doctor search", "Clinic locations", "Appointment booking",
                  "SMS reminders", "Telebirr payments", "AI health guidance"],
        techs=["React", "React Native", "TypeScript", "Node.js", "Express",
               "PostgreSQL", "Prisma", "Telebirr", "Africa's Talking",
               "Amazon Bedrock", "Docker", "AWS"],
        user_sel=[
            {"name": "React", "purpose": "web frontend", "category": "FRONTEND_FRAMEWORK"},
            {"name": "React Native", "purpose": "mobile frontend", "category": "FRONTEND_FRAMEWORK"},
            {"name": "TypeScript", "purpose": "language", "category": "LANGUAGE"},
            {"name": "Node.js", "purpose": "backend", "category": "BACKEND_FRAMEWORK"},
            {"name": "Express", "purpose": "backend framework", "category": "BACKEND_FRAMEWORK"},
            {"name": "PostgreSQL", "purpose": "database", "category": "DATABASE"},
            {"name": "Prisma", "purpose": "ORM", "category": "ORM"},
            {"name": "Telebirr", "purpose": "payments", "category": "PAYMENT_PROVIDER"},
            {"name": "Africa's Talking", "purpose": "SMS", "category": "SMS_PROVIDER"},
            {"name": "Amazon Bedrock", "purpose": "AI", "category": "AI_PROVIDER"},
            {"name": "Docker", "purpose": "containers", "category": "HOSTING"},
            {"name": "AWS", "purpose": "cloud", "category": "CLOUD_PROVIDER"},
        ],
        db="PostgreSQL", auth="Phone + SMS OTP",
        integrations=["Telebirr", "Africa's Talking", "Amazon Bedrock"],
        platform="Web and mobile", deployment="Docker on AWS",
    )

    architecture = _make_arch(
        tech_stack=[
            ("Frontend", "React", "User selected"),
            ("Mobile", "React Native", "User selected"),
            ("Language", "TypeScript", "User selected"),
            ("Backend", "Node.js", "User selected"),
            ("Backend", "Express", "User selected"),
            ("Database", "PostgreSQL", "User selected"),
            ("ORM", "Prisma", "User selected"),
            ("Payments", "Telebirr", "User selected"),
            ("SMS", "Africa's Talking", "User selected"),
            ("AI", "Amazon Bedrock", "User selected"),
            ("Containers", "Docker", "User selected"),
            ("Cloud", "AWS", "User selected"),
        ],
        sys_arch="Client-server with React web, React Native mobile, Node.js backend.",
    )

    context = _make_ctx(
        tech_stack=[
            "React - Web frontend", "React Native - Mobile",
            "TypeScript - Language", "Node.js - Backend", "Express - Framework",
            "PostgreSQL - Database", "Prisma - ORM",
            "Telebirr - Payments", "Africa's Talking - SMS",
            "Amazon Bedrock - AI", "Docker - Containers", "AWS - Cloud",
        ],
        title="HealthLink Ethiopia",
        frs=["FR-001: Doctor Search", "FR-002: Appointments", "FR-003: Payments"],
        nfrs=["NFR-001: Security"],
    )

    reqs = _make_reqs([("FR-001", "Doctor Search"), ("FR-002", "Appointments"), ("FR-003", "Payments")])

    # 1. Technology consistency
    arch_norm = normalize_tech_list([tc.technology for tc in architecture.technology_stack])
    ctx_norm = normalize_tech_list(context.technology_stack)
    match, missing, extra = tech_sets_match(arch_norm, ctx_norm)
    assert len(missing) == 0, f"Arch techs missing from context: {missing}"

    # 2. User-selected tech preservation
    for ust in project.user_selected_technologies:
        ust_norm = __import__('app.utils.tech_normalizer', fromlist=['normalize_tech_name']).normalize_tech_name(ust.name)
        assert ust_norm in arch_norm, f"User-selected '{ust.name}' missing from architecture"
        assert ust_norm in ctx_norm, f"User-selected '{ust.name}' missing from context"

    # 3. No substitution
    from app.utils.tech_normalizer import find_substituted_technologies
    subs = find_substituted_technologies(
        [t.name for t in project.user_selected_technologies],
        [tc.technology for tc in architecture.technology_stack],
    )
    assert len(subs) == 0, f"Unexpected substitutions: {subs}"

    # 4. Validation
    val = validate_context(project, reqs, architecture, context)
    assert val.score >= 80, f"Validation score {val.score} < 80"

    # 5. Agent readiness
    readiness = check_agent_readiness(project, reqs, architecture, context)
    assert readiness.checks.technology_consistency >= 85, \
        f"Tech consistency {readiness.checks.technology_consistency}% < 85%"
    sub_warnings = [w for w in readiness.warnings if "CONTRADICTION" in w.message]
    assert len(sub_warnings) == 0, f"False contradictions: {[w.message for w in sub_warnings]}"


# ============================================================
# PROJECT 2: Ethiopian Supermarket Inventory (C#/.NET)
# ============================================================

def test_inventory_pipeline():
    from app.engines.agent_readiness import check_agent_readiness
    from app.engines.validation import validate_context
    from app.utils.tech_normalizer import normalize_tech_list, tech_sets_match, find_substituted_technologies

    project = _make_project(
        name="Ethiopian Supermarket Inventory",
        desc="Inventory management for a single supermarket branch.",
        problem="Manual inventory tracking causes stockouts and waste.",
        features=["Product management", "Stock tracking", "Sales tracking", "Reports"],
        techs=["C#", "ASP.NET Core", "SQL Server", "Entity Framework Core"],
        user_sel=[
            {"name": "C#", "purpose": "language", "category": "LANGUAGE"},
            {"name": "ASP.NET Core", "purpose": "backend", "category": "BACKEND_FRAMEWORK"},
            {"name": "SQL Server", "purpose": "database", "category": "DATABASE"},
            {"name": "Entity Framework Core", "purpose": "ORM", "category": "ORM"},
        ],
        db="SQL Server", auth="JWT",
        platform="Web", deployment="IIS",
    )

    architecture = _make_arch(
        tech_stack=[
            ("Language", "C#", "User selected"),
            ("Backend", "ASP.NET Core", "User selected"),
            ("Database", "SQL Server", "User selected"),
            ("ORM", "Entity Framework Core", "User selected"),
        ],
        sys_arch="Single-server ASP.NET Core with SQL Server.",
    )

    context = _make_ctx(
        tech_stack=["C#", "ASP.NET Core", "SQL Server", "Entity Framework Core"],
        title="Ethiopian Supermarket Inventory",
        frs=["FR-001: Products", "FR-002: Stock", "FR-003: Reports"],
    )

    reqs = _make_reqs([("FR-001", "Products"), ("FR-002", "Stock"), ("FR-003", "Reports")])

    # 1. Must NOT contain Node.js, React, MongoDB
    arch_norm = normalize_tech_list([tc.technology for tc in architecture.technology_stack])
    forbidden = {"node.js", "react", "mongodb", "postgresql", "django", "flutter"}
    assert arch_norm.isdisjoint(forbidden), f"Forbidden techs in architecture: {arch_norm & forbidden}"

    # 2. User-selected tech preservation
    for ust in project.user_selected_technologies:
        ust_norm = __import__('app.utils.tech_normalizer', fromlist=['normalize_tech_name']).normalize_tech_name(ust.name)
        assert ust_norm in arch_norm, f"User-selected '{ust.name}' missing from architecture"

    # 3. No substitution
    subs = find_substituted_technologies(
        [t.name for t in project.user_selected_technologies],
        [tc.technology for tc in architecture.technology_stack],
    )
    assert len(subs) == 0, f"Unexpected substitutions: {subs}"

    # 4. Validation
    val = validate_context(project, reqs, architecture, context)
    assert val.score >= 80, f"Validation score {val.score} < 80"

    # 5. Readiness
    readiness = check_agent_readiness(project, reqs, architecture, context)
    assert readiness.checks.technology_consistency >= 85, \
        f"Tech consistency {readiness.checks.technology_consistency}% < 85%"
    sub_warnings = [w for w in readiness.warnings if "CONTRADICTION" in w.message]
    assert len(sub_warnings) == 0, f"False contradictions: {[w.message for w in sub_warnings]}"


# ============================================================
# PROJECT 3: Ethiopian Coffee Bean Quality AI (Python)
# ============================================================

def test_aiml_pipeline():
    from app.engines.agent_readiness import check_agent_readiness
    from app.engines.validation import validate_context
    from app.utils.tech_normalizer import normalize_tech_list, tech_sets_match, find_substituted_technologies

    project = _make_project(
        name="Ethiopian Coffee Bean Quality AI",
        desc="AI system classifying coffee bean quality from images and data.",
        problem="Manual quality grading is slow and inconsistent.",
        features=["Image upload", "Quality classification", "Dataset management"],
        techs=["Python", "FastAPI", "scikit-learn", "pandas", "NumPy", "PostgreSQL"],
        user_sel=[
            {"name": "Python", "purpose": "language", "category": "LANGUAGE"},
            {"name": "FastAPI", "purpose": "backend", "category": "BACKEND_FRAMEWORK"},
            {"name": "scikit-learn", "purpose": "ML", "category": "AI_PROVIDER"},
            {"name": "pandas", "purpose": "data processing", "category": "DATA_TOOL"},
            {"name": "NumPy", "purpose": "numerical computing", "category": "DATA_TOOL"},
            {"name": "PostgreSQL", "purpose": "database", "category": "DATABASE"},
        ],
        db="PostgreSQL", auth="JWT",
        platform="Web", deployment="Docker",
    )

    architecture = _make_arch(
        tech_stack=[
            ("Language", "Python", "User selected"),
            ("Backend", "FastAPI", "User selected"),
            ("ML", "scikit-learn", "User selected"),
            ("Data", "pandas", "User selected"),
            ("Data", "NumPy", "User selected"),
            ("Database", "PostgreSQL", "User selected"),
        ],
        sys_arch="Python ML backend with FastAPI serving model predictions.",
    )

    context = _make_ctx(
        tech_stack=["Python", "FastAPI", "scikit-learn", "pandas", "NumPy", "PostgreSQL"],
        title="Ethiopian Coffee Bean Quality AI",
        frs=["FR-001: Image Upload", "FR-002: Classification", "FR-003: Dataset Management"],
    )

    reqs = _make_reqs([("FR-001", "Image Upload"), ("FR-002", "Classification"), ("FR-003", "Dataset Management")])

    # 1. Must NOT force Node.js backend
    arch_norm = normalize_tech_list([tc.technology for tc in architecture.technology_stack])
    forbidden = {"node.js", "express", "react", "mongodb", "django"}
    assert arch_norm.isdisjoint(forbidden), f"Forbidden techs in architecture: {arch_norm & forbidden}"

    # 2. Must contain Python, FastAPI, scikit-learn
    required = {"python", "fastapi", "scikit-learn", "postgresql"}
    assert required.issubset(arch_norm), f"Missing required techs: {required - arch_norm}"

    # 3. User-selected preservation
    for ust in project.user_selected_technologies:
        ust_norm = __import__('app.utils.tech_normalizer', fromlist=['normalize_tech_name']).normalize_tech_name(ust.name)
        assert ust_norm in arch_norm, f"User-selected '{ust.name}' missing from architecture"

    # 4. No substitution
    subs = find_substituted_technologies(
        [t.name for t in project.user_selected_technologies],
        [tc.technology for tc in architecture.technology_stack],
    )
    assert len(subs) == 0, f"Unexpected substitutions: {subs}"

    # 5. Validation
    val = validate_context(project, reqs, architecture, context)
    assert val.score >= 80, f"Validation score {val.score} < 80"

    # 6. Readiness
    readiness = check_agent_readiness(project, reqs, architecture, context)
    assert readiness.checks.technology_consistency >= 85, \
        f"Tech consistency {readiness.checks.technology_consistency}% < 85%"
    sub_warnings = [w for w in readiness.warnings if "CONTRADICTION" in w.message]
    assert len(sub_warnings) == 0, f"False contradictions: {[w.message for w in sub_warnings]}"


# ============================================================
# PROJECT 4: Ethiopian Food Delivery (Flutter/Firebase)
# ============================================================

def test_flutter_pipeline():
    from app.engines.agent_readiness import check_agent_readiness
    from app.engines.validation import validate_context
    from app.utils.tech_normalizer import normalize_tech_list, find_substituted_technologies

    project = _make_project(
        name="Ethiopian Food Delivery",
        desc="Mobile food delivery application.",
        problem="Difficult to order food from restaurants.",
        features=["Restaurant browsing", "Menu viewing", "Order placement", "Order tracking"],
        techs=["Flutter", "Dart", "Firebase"],
        user_sel=[
            {"name": "Flutter", "purpose": "mobile framework", "category": "FRONTEND_FRAMEWORK"},
            {"name": "Dart", "purpose": "language", "category": "LANGUAGE"},
            {"name": "Firebase", "purpose": "backend platform", "category": "DATABASE"},
        ],
        db="Firebase", auth="Firebase Auth",
        platform="Mobile", deployment="Firebase Hosting",
    )

    architecture = _make_arch(
        tech_stack=[
            ("Mobile", "Flutter", "User selected"),
            ("Language", "Dart", "User selected"),
            ("Backend", "Firebase", "User selected"),
        ],
        sys_arch="Flutter mobile app with Firebase backend.",
    )

    context = _make_ctx(
        tech_stack=["Flutter", "Dart", "Firebase"],
        title="Ethiopian Food Delivery",
        frs=["FR-001: Restaurants", "FR-002: Orders", "FR-003: Tracking"],
    )

    reqs = _make_reqs([("FR-001", "Restaurants"), ("FR-002", "Orders"), ("FR-003", "Tracking")])

    # 1. Must keep Flutter, NOT replace with React Native
    arch_norm = normalize_tech_list([tc.technology for tc in architecture.technology_stack])
    assert "flutter" in arch_norm, "Flutter missing from architecture"

    # 2. Must NOT contain React, Node.js
    forbidden = {"react", "react native", "node.js", "express", "postgresql", "django"}
    assert arch_norm.isdisjoint(forbidden), f"Forbidden techs: {arch_norm & forbidden}"

    # 3. User-selected preservation
    for ust in project.user_selected_technologies:
        ust_norm = __import__('app.utils.tech_normalizer', fromlist=['normalize_tech_name']).normalize_tech_name(ust.name)
        assert ust_norm in arch_norm, f"User-selected '{ust.name}' missing"

    # 4. No substitution
    subs = find_substituted_technologies(
        [t.name for t in project.user_selected_technologies],
        [tc.technology for tc in architecture.technology_stack],
    )
    assert len(subs) == 0, f"Unexpected substitutions: {subs}"

    # 5. Validation
    val = validate_context(project, reqs, architecture, context)
    assert val.score >= 80

    # 6. Readiness
    readiness = check_agent_readiness(project, reqs, architecture, context)
    assert readiness.checks.technology_consistency >= 85
    sub_warnings = [w for w in readiness.warnings if "CONTRADICTION" in w.message]
    assert len(sub_warnings) == 0, f"False contradictions: {[w.message for w in sub_warnings]}"


# ============================================================
# PROJECT 5: Django Property Marketplace
# ============================================================

def test_django_pipeline():
    from app.engines.agent_readiness import check_agent_readiness
    from app.engines.validation import validate_context
    from app.utils.tech_normalizer import normalize_tech_list, find_substituted_technologies

    project = _make_project(
        name="Django Property Marketplace",
        desc="Property marketplace for rent and sale.",
        problem="Difficult to find properties to rent or buy.",
        features=["Property listing", "Search", "Contact owners", "Save favorites"],
        techs=["Python", "Django", "PostgreSQL", "Redis"],
        user_sel=[
            {"name": "Python", "purpose": "language", "category": "LANGUAGE"},
            {"name": "Django", "purpose": "backend", "category": "BACKEND_FRAMEWORK"},
            {"name": "PostgreSQL", "purpose": "database", "category": "DATABASE"},
            {"name": "Redis", "purpose": "caching", "category": "CACHE"},
        ],
        db="PostgreSQL", auth="Django auth",
        platform="Web", deployment="Docker",
    )

    architecture = _make_arch(
        tech_stack=[
            ("Language", "Python", "User selected"),
            ("Backend", "Django", "User selected"),
            ("Database", "PostgreSQL", "User selected"),
            ("Cache", "Redis", "User selected"),
        ],
        sys_arch="Django web application with PostgreSQL and Redis.",
    )

    context = _make_ctx(
        tech_stack=["Python", "Django", "PostgreSQL", "Redis"],
        title="Django Property Marketplace",
        frs=["FR-001: Listings", "FR-002: Search", "FR-003: Contact"],
    )

    reqs = _make_reqs([("FR-001", "Listings"), ("FR-002", "Search"), ("FR-003", "Contact")])

    # 1. Must keep Django, NOT replace with Node.js
    arch_norm = normalize_tech_list([tc.technology for tc in architecture.technology_stack])
    assert "django" in arch_norm, "Django missing from architecture"
    forbidden = {"node.js", "express", "react", "mongodb", "fastapi"}
    assert arch_norm.isdisjoint(forbidden), f"Forbidden techs: {arch_norm & forbidden}"

    # 2. Must keep Redis
    assert "redis" in arch_norm, "Redis missing from architecture"

    # 3. User-selected preservation
    for ust in project.user_selected_technologies:
        ust_norm = __import__('app.utils.tech_normalizer', fromlist=['normalize_tech_name']).normalize_tech_name(ust.name)
        assert ust_norm in arch_norm, f"User-selected '{ust.name}' missing"

    # 4. No substitution
    subs = find_substituted_technologies(
        [t.name for t in project.user_selected_technologies],
        [tc.technology for tc in architecture.technology_stack],
    )
    assert len(subs) == 0, f"Unexpected substitutions: {subs}"

    # 5. Validation
    val = validate_context(project, reqs, architecture, context)
    assert val.score >= 80

    # 6. Readiness
    readiness = check_agent_readiness(project, reqs, architecture, context)
    assert readiness.checks.technology_consistency >= 85
    sub_warnings = [w for w in readiness.warnings if "CONTRADICTION" in w.message]
    assert len(sub_warnings) == 0, f"False contradictions: {[w.message for w in sub_warnings]}"


# ============================================================
# REGRESSION: Generic concept filtering
# ============================================================

def test_generic_not_classified():
    from app.utils.tech_normalizer import classify_tech, NON_TECH_WORDS

    generic_words = [
        "backend", "frontend", "web", "mobile", "API", "database",
        "authentication", "OTP", "SMS", "payments", "reminders",
        "doctor", "patient", "production", "staging", "platform",
        "service", "worker", "AI", "machine learning", "metrics",
        "logging", "monitoring", "security",
    ]
    for word in generic_words:
        cat = classify_tech(word)
        assert cat == "OTHER", f"'{word}' classified as {cat}, expected OTHER"


# ============================================================
# REGRESSION: Technology substitution detection
# ============================================================

def test_substitution_detection():
    from app.utils.tech_normalizer import find_substituted_technologies

    # Same tech = no substitution
    subs = find_substituted_technologies(["PostgreSQL"], ["PostgreSQL"])
    assert len(subs) == 0

    # Same category, different tech = substitution
    subs = find_substituted_technologies(["OpenAI API"], ["Amazon Bedrock"])
    assert len(subs) == 1
    assert subs[0]["category"] == "AI_PROVIDER"

    # Different category = no substitution
    subs = find_substituted_technologies(["React"], ["PostgreSQL"])
    assert len(subs) == 0

    # Multiple substitutions
    subs = find_substituted_technologies(
        ["OpenAI API", "Telebirr", "Google Maps"],
        ["Amazon Bedrock", "Stripe", "Mapbox"],
    )
    assert len(subs) == 3


# ============================================================
# REGRESSION: JS/TS equivalence
# ============================================================

def test_jst_equivalence():
    from app.utils.tech_normalizer import tech_sets_match, normalize_tech_list, find_substituted_technologies

    # JS/TS should match
    user = normalize_tech_list(["TypeScript"])
    arch = normalize_tech_list(["JavaScript"])
    match, missing, extra = tech_sets_match(user, arch)
    assert match, f"JS/TS should match: missing={missing}, extra={extra}"

    # JS/TS should not be substitution
    subs = find_substituted_technologies(["TypeScript"], ["JavaScript"])
    assert len(subs) == 0


# ============================================================
# REGRESSION: AI assumption handling
# ============================================================

def test_ai_assumption_handling():
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
            UserSelectedTechnology(name="PostgreSQL", purpose="database", category="DATABASE"),
        ],
    )

    architecture = ArchitectureDocument(
        system_architecture="Test.", components=[],
        technology_stack=[
            TechnologyChoice(category="Frontend", technology="React", reason="User"),
            TechnologyChoice(category="Database", technology="PostgreSQL", reason="User"),
            TechnologyChoice(category="CSS", technology="TailwindCSS", reason="AI recommended"),
        ],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )

    context = ImplementationContext(
        project_title="Test", project_summary="Test.", problem="Test.",
        target_users=["Users"], functional_requirements=["FR-001: Feature"],
        non_functional_requirements=[], architecture_summary="Test.",
        technology_stack=["React", "PostgreSQL", "TailwindCSS"],
        data_model=[], api_contract=[], security_requirements=[],
        implementation_phases=[ImplementationPhase(phase=1, name="F", objective="Setup", tasks=["Setup"], deliverables=["App"])],
        agent_rules=[AgentRule(category="Architecture", rule="Monolith"), AgentRule(category="Security", rule="JWT"), AgentRule(category="Testing", rule="Tests")],
        definition_of_done=["Done"],
    )

    reqs = RequirementsDocument(functional_requirements=[
        Requirement(id="FR-001", title="Feature", description="F", priority="MUST_HAVE"),
    ])

    result = check_agent_readiness(project, reqs, architecture, context)

    # React and PostgreSQL should NOT be AI assumptions
    for tech in ["React", "PostgreSQL"]:
        assumptions = [a for a in result.assumptions
                      if tech.lower() in a.assumption.lower()
                      and "selected by ai" in a.assumption.lower()]
        assert len(assumptions) == 0, f"{tech} should not be AI assumption"

    # TailwindCSS IS an AI recommendation — should appear as info
    tw = [a for a in result.assumptions if "tailwindcss" in a.assumption.lower()]
    assert len(tw) == 1, f"Expected 1 TailwindCSS assumption, got {len(tw)}"


# ============================================================
# REGRESSION: Definition of Done generation
# ============================================================

def test_definition_of_done():
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
        ],
    )

    architecture = ArchitectureDocument(
        system_architecture="Test.", components=[],
        technology_stack=[
            TechnologyChoice(category="Frontend", technology="React", reason="User"),
        ],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )

    context = ImplementationContext(
        project_title="Test", project_summary="Test.", problem="Test.",
        target_users=["Users"], functional_requirements=["FR-001: Feature"],
        non_functional_requirements=[], architecture_summary="Test.",
        technology_stack=["React"],
        data_model=[], api_contract=[], security_requirements=[],
        implementation_phases=[ImplementationPhase(phase=1, name="F", objective="Setup", tasks=["Setup"], deliverables=["App"])],
        agent_rules=[AgentRule(category="Architecture", rule="Monolith"), AgentRule(category="Security", rule="JWT"), AgentRule(category="Testing", rule="Tests")],
        definition_of_done=[
            "All features implemented",
            "Tests passing",
            "Documentation complete",
        ],
    )

    reqs = RequirementsDocument(functional_requirements=[
        Requirement(id="FR-001", title="Feature", description="F", priority="MUST_HAVE"),
    ])

    result = check_agent_readiness(project, reqs, architecture, context)
    # Definition of done should have reasonable score
    assert result.checks.definition_of_done >= 60, \
        f"DoD score {result.checks.definition_of_done} < 60"


# ============================================================
# REGRESSION: Architecture/context consistency
# ============================================================

def test_arch_context_consistency():
    from app.utils.tech_normalizer import normalize_tech_list, tech_sets_match

    # Matching sets
    arch = normalize_tech_list(["React", "Node.js", "PostgreSQL"])
    ctx = normalize_tech_list(["React - Frontend", "Node.js - Backend", "PostgreSQL - Database"])
    match, missing, extra = tech_sets_match(arch, ctx)
    assert match, f"Should match: missing={missing}, extra={extra}"

    # Context has extra (superset) — OK
    arch2 = normalize_tech_list(["React", "Node.js"])
    ctx2 = normalize_tech_list(["React", "Node.js", "PostgreSQL"])
    match2, missing2, extra2 = tech_sets_match(arch2, ctx2)
    assert len(missing2) == 0, f"Should have no missing: {missing2}"


# ============================================================
# REGRESSION: Requirements/architecture consistency
# ============================================================

def test_req_arch_consistency():
    from app.engines.validation import validate_context
    from app.models.project import ProjectState
    from app.models.requirements import RequirementsDocument, Requirement
    from app.models.architecture import ArchitectureDocument, TechnologyChoice
    from app.models.context import ImplementationContext, ImplementationPhase, AgentRule

    project = ProjectState(name="Test", description="Test.", problem="Test.",
                          target_users=["Users"], core_features=["Feature"])

    reqs = RequirementsDocument(functional_requirements=[
        Requirement(id="FR-001", title="Feature", description="F", priority="MUST_HAVE"),
    ])

    architecture = ArchitectureDocument(
        system_architecture="Test.", components=[],
        technology_stack=[
            TechnologyChoice(category="Frontend", technology="React", reason="Standard"),
        ],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )

    context = ImplementationContext(
        project_title="Test", project_summary="Test.", problem="Test.",
        target_users=["Users"],
        functional_requirements=["FR-001: Feature"],
        non_functional_requirements=[], architecture_summary="Test.",
        technology_stack=["React"],
        data_model=[], api_contract=[], security_requirements=[],
        implementation_phases=[ImplementationPhase(phase=1, name="F", objective="Setup", tasks=["Setup"], deliverables=["App"])],
        agent_rules=[AgentRule(category="Architecture", rule="Monolith"), AgentRule(category="Security", rule="JWT"), AgentRule(category="Testing", rule="Tests")],
        definition_of_done=["All features implemented"],
    )

    val = validate_context(project, reqs, architecture, context)
    assert val.score >= 80, f"Validation score {val.score} < 80"
    # FR-001 should be represented
    fr_issues = [i for i in val.issues if "FR-001" in i.message]
    assert len(fr_issues) == 0, f"FR-001 not represented: {fr_issues}"


# ============================================================
# REGRESSION: Cross-project architecture diversity
# ============================================================

def test_architecture_diversity():
    """Verify different projects produce appropriately different architectures."""
    from app.utils.tech_normalizer import normalize_tech_list

    # Each project should have distinct technology stacks
    stacks = {
        "HealthLink": normalize_tech_list(["React", "React Native", "TypeScript", "Node.js", "Express", "PostgreSQL", "Prisma", "Telebirr", "Africa's Talking", "Amazon Bedrock", "Docker", "AWS"]),
        "Inventory": normalize_tech_list(["C#", "ASP.NET Core", "SQL Server", "Entity Framework Core"]),
        "AI/ML": normalize_tech_list(["Python", "FastAPI", "scikit-learn", "pandas", "NumPy", "PostgreSQL"]),
        "Flutter": normalize_tech_list(["Flutter", "Dart", "Firebase"]),
        "Django": normalize_tech_list(["Python", "Django", "PostgreSQL", "Redis"]),
    }

    # HealthLink and Inventory should be very different
    assert stacks["HealthLink"].isdisjoint(stacks["Inventory"]), \
        "HealthLink and Inventory should have different stacks"

    # Django and Inventory should be different
    assert stacks["Django"].isdisjoint(stacks["Inventory"]), \
        "Django and Inventory should have different stacks"

    # Flutter should be unique
    assert "flutter" in stacks["Flutter"]
    assert "flutter" not in stacks["HealthLink"]
    assert "flutter" not in stacks["Django"]


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    tests = [
        # Full pipeline tests (5)
        ("Pipeline: HealthLink Ethiopia", test_healthlink_pipeline),
        ("Pipeline: Inventory C#/.NET", test_inventory_pipeline),
        ("Pipeline: AI/ML Python", test_aiml_pipeline),
        ("Pipeline: Flutter/Firebase", test_flutter_pipeline),
        ("Pipeline: Django/Redis", test_django_pipeline),
        # Regression tests (7)
        ("Regress: Generic concept filtering", test_generic_not_classified),
        ("Regress: Substitution detection", test_substitution_detection),
        ("Regress: JS/TS equivalence", test_jst_equivalence),
        ("Regress: AI assumption handling", test_ai_assumption_handling),
        ("Regress: Definition of Done", test_definition_of_done),
        ("Regress: Arch/context consistency", test_arch_context_consistency),
        ("Regress: Req/arch consistency", test_req_arch_consistency),
        ("Regress: Architecture diversity", test_architecture_diversity),
    ]

    print("=" * 60)
    print("FULL MULTI-PROJECT PIPELINE VALIDATION")
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
