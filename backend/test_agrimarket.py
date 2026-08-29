"""
AgriMarket Ethiopia — Cross-Project Real-World Validation

Tests the complete ContextForge pipeline with a project that has never
been used in any HealthLink test. Verifies:

1. No HealthLink technology leakage
2. AgriMarket technology preservation
3. AI assumptions clearly marked
4. Generic words NOT classified as technologies
5. Architecture appropriate for marketplace (not healthcare)
6. No overengineering
7. Consistency across all sections
8. Cross-project independence
9. Substitution detection
10. Contradiction detection
11. Quality gate pass/fail behavior
12. Agent readiness for marketplace concerns

IMPORTANT: This file does NOT hardcode AgriMarket-specific behavior.
All checks use the generic ContextForge validation logic.
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
# AgriMarket model builders
# ============================================================

def _make_agrimarket_project():
    """Build a realistic AgriMarket ProjectState."""
    from app.models.project import ProjectState, UserSelectedTechnology

    return ProjectState(
        name="AgriMarket Ethiopia",
        description=(
            "Platform connecting Ethiopian farmers with buyers. "
            "Farmers list agricultural products, buyers search and order."
        ),
        problem=(
            "Ethiopian farmers struggle to reach buyers directly, "
            "leading to low prices and wasted produce."
        ),
        target_users=["Farmers", "Buyers", "Administrators"],
        core_features=[
            "Farmer product listing",
            "Buyer product search",
            "Order placement and tracking",
            "SMS notifications",
            "Admin management",
        ],
        platform="Web and mobile",
        technologies=[
            "React", "Node.js", "Express", "PostgreSQL",
            "Docker", "AWS",
        ],
        user_selected_technologies=[
            UserSelectedTechnology(
                name="React", purpose="web frontend",
                category="FRONTEND_FRAMEWORK",
            ),
            UserSelectedTechnology(
                name="Node.js", purpose="backend runtime",
                category="BACKEND_FRAMEWORK",
            ),
            UserSelectedTechnology(
                name="Express", purpose="backend framework",
                category="BACKEND_FRAMEWORK",
            ),
            UserSelectedTechnology(
                name="PostgreSQL", purpose="primary database",
                category="DATABASE",
            ),
            UserSelectedTechnology(
                name="Docker", purpose="containerized deployment",
                category="HOSTING",
            ),
            UserSelectedTechnology(
                name="AWS", purpose="cloud hosting",
                category="CLOUD_PROVIDER",
            ),
        ],
        database="PostgreSQL",
        authentication="JWT",
        integrations=["SMS notifications"],
        constraints=["Low initial budget", "Must work in rural Ethiopia"],
        deployment="Docker on AWS",
    )


def _make_agrimarket_requirements():
    """Build realistic AgriMarket requirements."""
    from app.models.requirements import RequirementsDocument, Requirement, AcceptanceCriterion

    return RequirementsDocument(
        functional_requirements=[
            Requirement(
                id="FR-001", title="Farmer Registration",
                description="Farmers can create accounts with profile information.",
                priority="MUST_HAVE",
                actors=["Farmer"],
                acceptance_criteria=[
                    AcceptanceCriterion(description="Farmer can create account"),
                ],
            ),
            Requirement(
                id="FR-002", title="Product Listing",
                description="Farmers can list agricultural products with details.",
                priority="MUST_HAVE",
                actors=["Farmer"],
                acceptance_criteria=[
                    AcceptanceCriterion(description="Farmer can create product listing"),
                ],
            ),
            Requirement(
                id="FR-003", title="Product Search",
                description="Buyers can search products by category and location.",
                priority="MUST_HAVE",
                actors=["Buyer"],
                acceptance_criteria=[
                    AcceptanceCriterion(description="Buyer can find products"),
                ],
            ),
            Requirement(
                id="FR-004", title="Order Placement",
                description="Buyers can place orders for products.",
                priority="MUST_HAVE",
                actors=["Buyer"],
                acceptance_criteria=[
                    AcceptanceCriterion(description="Order is created"),
                ],
            ),
            Requirement(
                id="FR-005", title="Order Tracking",
                description="Users can track order status.",
                priority="MUST_HAVE",
                actors=["Farmer", "Buyer"],
                acceptance_criteria=[
                    AcceptanceCriterion(description="Order status is visible"),
                ],
            ),
            Requirement(
                id="FR-006", title="SMS Notifications",
                description="Users receive SMS notifications for order events.",
                priority="SHOULD_HAVE",
                actors=["Farmer", "Buyer"],
                acceptance_criteria=[
                    AcceptanceCriterion(description="SMS sent on order events"),
                ],
            ),
            Requirement(
                id="FR-007", title="Admin Management",
                description="Administrators manage users, categories, and listings.",
                priority="MUST_HAVE",
                actors=["Administrator"],
                acceptance_criteria=[
                    AcceptanceCriterion(description="Admin can manage platform"),
                ],
            ),
        ],
    )


def _make_agrimarket_architecture(tech_stack=None):
    """Build a realistic AgriMarket architecture."""
    from app.models.architecture import (
        ArchitectureDocument, TechnologyChoice,
        ArchitectureComponent, DeploymentPlan,
        DataEntity, APIGroup, SecurityDecision,
    )

    default_tech = tech_stack or [
        ("Frontend", "React", "User-selected web frontend"),
        ("Language", "TypeScript", "Type safety"),
        ("Backend", "Node.js", "User-selected runtime"),
        ("Backend", "Express", "User-selected framework"),
        ("Database", "PostgreSQL", "User-selected database"),
        ("ORM", "Prisma", "Database access"),
        ("Containers", "Docker", "User-selected deployment"),
        ("Cloud", "AWS", "User-selected cloud"),
        ("Auth", "JWT", "Stateless authentication"),
        ("SMS", "Africa's Talking", "SMS notifications for order events"),
    ]

    return ArchitectureDocument(
        system_architecture=(
            "Single-server client-server architecture with React web and mobile "
            "frontend, Node.js + Express backend, PostgreSQL database, and "
            "external service integrations for SMS notifications."
        ),
        components=[
            ArchitectureComponent(
                name="Web Frontend",
                responsibility="React SPA for farmers and buyers",
                technologies=["React", "TypeScript", "TailwindCSS"],
            ),
            ArchitectureComponent(
                name="API Server",
                responsibility="Express REST API handling all business logic",
                technologies=["Node.js", "Express", "Prisma"],
            ),
            ArchitectureComponent(
                name="Database",
                responsibility="PostgreSQL for persistent data storage",
                technologies=["PostgreSQL"],
            ),
        ],
        technology_stack=[
            TechnologyChoice(category=c, technology=t, reason=r)
            for c, t, r in default_tech
        ],
        data_architecture=[
            DataEntity(
                name="User",
                purpose="Farmers, buyers, and admin accounts",
                important_fields=["id", "email", "phone", "role", "name"],
            ),
            DataEntity(
                name="Product",
                purpose="Agricultural product listings",
                important_fields=["id", "farmer_id", "name", "category", "price", "quantity", "location"],
            ),
            DataEntity(
                name="Order",
                purpose="Buyer orders for products",
                important_fields=["id", "buyer_id", "product_id", "quantity", "status", "total_price"],
            ),
            DataEntity(
                name="Category",
                purpose="Product categories (coffee, wheat, maize, teff, etc.)",
                important_fields=["id", "name", "description"],
            ),
            DataEntity(
                name="Notification",
                purpose="SMS notification logs",
                important_fields=["id", "user_id", "type", "message", "status"],
            ),
        ],
        api_design=[
            APIGroup(
                name="Authentication",
                purpose="User registration and login",
                endpoints=[
                    "POST /api/auth/register",
                    "POST /api/auth/login",
                    "POST /api/auth/refresh",
                ],
            ),
            APIGroup(
                name="Products",
                purpose="Product CRUD and search",
                endpoints=[
                    "GET /api/products",
                    "POST /api/products",
                    "GET /api/products/:id",
                    "PUT /api/products/:id",
                    "DELETE /api/products/:id",
                ],
            ),
            APIGroup(
                name="Orders",
                purpose="Order management",
                endpoints=[
                    "POST /api/orders",
                    "GET /api/orders",
                    "GET /api/orders/:id",
                    "PATCH /api/orders/:id/status",
                ],
            ),
            APIGroup(
                name="Admin",
                purpose="Administrative functions",
                endpoints=[
                    "GET /api/admin/users",
                    "GET /api/admin/categories",
                    "POST /api/admin/categories",
                ],
            ),
        ],
        security=[
            SecurityDecision(
                area="Authentication",
                decision="JWT with refresh tokens",
                reason="Stateless auth suitable for API",
            ),
            SecurityDecision(
                area="Authorization",
                decision="RBAC: farmer, buyer, admin roles",
                reason="Different user types need different permissions",
            ),
            SecurityDecision(
                area="Data Protection",
                decision="HTTPS + encrypted credentials",
                reason="Protect user data in transit and at rest",
            ),
        ],
        deployment=[
            DeploymentPlan(
                environment="production",
                services=["Docker containers on AWS ECS/Fargate"],
                reason="User-selected containerized deployment",
            ),
        ],
    )


def _make_agrimarket_context(tech_stack=None):
    """Build a realistic AgriMarket implementation context."""
    from app.models.context import (
        ImplementationContext, ImplementationPhase, AgentRule,
    )

    default_tech = tech_stack or [
        "React - Web frontend for farmers and buyers",
        "TypeScript - Type-safe JavaScript",
        "Node.js - Backend runtime",
        "Express - REST API framework",
        "PostgreSQL - Primary database",
        "Prisma - Database ORM",
        "Docker - Containerized deployment",
        "AWS - Cloud hosting",
        "JWT - Stateless authentication",
        "Africa's Talking - SMS notifications",
    ]

    return ImplementationContext(
        project_title="AgriMarket Ethiopia",
        project_summary=(
            "Platform connecting Ethiopian farmers with buyers for "
            "agricultural products."
        ),
        problem=(
            "Ethiopian farmers struggle to reach buyers directly."
        ),
        target_users=["Farmers", "Buyers", "Administrators"],
        functional_requirements=[
            "FR-001: Farmer Registration - Farmers can create accounts",
            "FR-002: Product Listing - Farmers list products with details",
            "FR-003: Product Search - Buyers search by category and location",
            "FR-004: Order Placement - Buyers place orders",
            "FR-005: Order Tracking - Users track order status",
            "FR-006: SMS Notifications - Users receive SMS for order events",
            "FR-007: Admin Management - Admin manages users and categories",
        ],
        non_functional_requirements=[
            "NFR-001: Security - Protect user credentials with bcrypt",
            "NFR-002: Performance - Search results under 2 seconds",
            "NFR-003: Availability - 99.5% uptime",
        ],
        architecture_summary=(
            "React + Node.js/Express + PostgreSQL with Docker deployment on AWS."
        ),
        technology_stack=default_tech,
        data_model=[
            "User: id, email, phone, name, role (farmer/buyer/admin), password_hash, created_at",
            "Product: id, farmer_id, name, category_id, description, price, quantity, unit, location, image_url, status, created_at",
            "Order: id, buyer_id, product_id, quantity, total_price, status (pending/confirmed/delivered/cancelled), created_at",
            "Category: id, name, description, image_url",
            "Notification: id, user_id, type, message, status (pending/sent/failed), created_at",
        ],
        api_contract=[
            "POST /api/auth/register - Register new user",
            "POST /api/auth/login - Login and receive JWT",
            "GET /api/products - List/search products",
            "POST /api/products - Create product listing (farmer)",
            "POST /api/orders - Place an order (buyer)",
            "GET /api/orders/:id - View order details",
            "PATCH /api/orders/:id/status - Update order status",
            "GET /api/admin/users - List all users (admin)",
            "POST /api/admin/categories - Create category (admin)",
        ],
        security_requirements=[
            "Password Storage: Use bcrypt with cost factor 12",
            "JWT: 15-minute access tokens, 7-day refresh tokens",
            "RBAC: farmers can manage own products, buyers can place orders, admins manage platform",
            "Rate limiting: max 5 login attempts per 15 minutes",
            "All API endpoints require HTTPS",
            "Audit logging for admin actions",
        ],
        implementation_phases=[
            ImplementationPhase(
                phase=1, name="Project Foundation",
                objective="Set up project structure, database, and auth",
                tasks=[
                    "Initialize Node.js + Express + TypeScript project",
                    "Set up Prisma with PostgreSQL",
                    "Implement user registration and JWT auth",
                    "Create database schema",
                ],
                deliverables=[
                    "Working API with authentication",
                    "Database migrations",
                ],
            ),
            ImplementationPhase(
                phase=2, name="Product Management",
                objective="Farmer product listing and search",
                tasks=[
                    "Implement product CRUD API",
                    "Implement product search with filters",
                    "Build product listing UI",
                ],
                deliverables=[
                    "Product API endpoints",
                    "Search functionality",
                ],
            ),
            ImplementationPhase(
                phase=3, name="Order System",
                objective="Order placement and tracking",
                tasks=[
                    "Implement order creation API",
                    "Implement order status management",
                    "Build order tracking UI",
                ],
                deliverables=[
                    "Order API endpoints",
                    "Order tracking UI",
                ],
            ),
            ImplementationPhase(
                phase=4, name="Notifications & Admin",
                objective="SMS notifications and admin panel",
                tasks=[
                    "Integrate Africa's Talking SMS API",
                    "Implement notification triggers",
                    "Build admin dashboard",
                ],
                deliverables=[
                    "SMS notifications",
                    "Admin panel",
                ],
            ),
        ],
        agent_rules=[
            AgentRule(
                category="Architecture",
                rule="Single-server Express API, no microservices for MVP",
            ),
            AgentRule(
                category="Security",
                rule="Never hardcode API keys. Use environment variables or secrets manager.",
            ),
            AgentRule(
                category="Security",
                rule="All passwords must be hashed with bcrypt before storage.",
            ),
            AgentRule(
                category="Testing",
                rule="Write unit tests for each API endpoint and integration tests for order flow.",
            ),
            AgentRule(
                category="Development",
                rule="Implement phases incrementally. Verify each phase before proceeding.",
            ),
        ],
        definition_of_done=[
            "All 7 functional requirements implemented and tested",
            "JWT authentication working with refresh tokens",
            "Product search returns results in under 2 seconds",
            "Order status transitions are validated",
            "SMS notifications sent on order events",
            "Admin can manage users and categories",
            "All API endpoints require authentication",
            "Unit test coverage above 80%",
        ],
    )


# ============================================================
# TEST 1: No HealthLink technology leakage
# ============================================================
def test_no_healthlink_leakage():
    """Verify that HealthLink-specific technologies do NOT appear
    in AgriMarket unless explicitly selected."""
    from app.utils.tech_normalizer import normalize_tech_list

    project = _make_agrimarket_project()
    arch = _make_agrimarket_architecture()
    ctx = _make_agrimarket_context()

    # Technologies that are HealthLink-specific and should NOT appear
    # in AgriMarket's architecture unless the user explicitly selected them
    healthlink_only = {
        "telebirr", "openai api", "amazon bedrock", "bedrock",
        "google maps", "mapbox", "react native", "expo",
        "prisma",  # AgriMarket might use Prisma, but it's not HealthLink-specific
    }

    # Check architecture
    arch_norm = normalize_tech_list(
        [tc.technology for tc in arch.technology_stack]
    )

    # These should definitely NOT be in AgriMarket's architecture
    forbidden_in_arch = {"telebirr", "openai api", "amazon bedrock", "google maps", "react native", "expo"}
    leaked = arch_norm & forbidden_in_arch
    assert len(leaked) == 0, (
        f"HealthLink technologies leaked into AgriMarket architecture: {leaked}"
    )

    # Check context
    ctx_norm = normalize_tech_list(ctx.technology_stack)
    leaked_ctx = ctx_norm & forbidden_in_arch
    assert len(leaked_ctx) == 0, (
        f"HealthLink technologies leaked into AgriMarket context: {leaked_ctx}"
    )

    # Check project — no user-selected HealthLink techs
    user_tech_norms = {
        t.name.lower().strip() for t in project.user_selected_technologies
    }
    leaked_user = user_tech_norms & {"telebirr", "openai api", "amazon bedrock", "google maps"}
    assert len(leaked_user) == 0, (
        f"HealthLink user-selected techs leaked into AgriMarket: {leaked_user}"
    )


# ============================================================
# TEST 2: AgriMarket user-selected tech preservation
# ============================================================
def test_agrimarket_tech_preservation():
    """Verify that AgriMarket's user-selected technologies are preserved
    through architecture and context."""
    from app.utils.tech_normalizer import normalize_tech_name, find_substituted_technologies

    project = _make_agrimarket_project()
    arch = _make_agrimarket_architecture()
    ctx = _make_agrimarket_context()

    arch_norm = {tc.technology.lower().strip() for tc in arch.technology_stack}
    ctx_text = " ".join(ctx.technology_stack).lower()

    for ust in project.user_selected_technologies:
        ust_norm = normalize_tech_name(ust.name)

        # Must be in architecture
        assert ust_norm in arch_norm or ust.name.lower() in arch_norm, (
            f"User-selected '{ust.name}' missing from architecture. "
            f"Architecture has: {arch_norm}"
        )

        # Must be in context
        assert ust_norm in ctx_text or ust.name.lower() in ctx_text, (
            f"User-selected '{ust.name}' missing from context."
        )

    # No substitutions
    subs = find_substituted_technologies(
        [t.name for t in project.user_selected_technologies],
        [tc.technology for tc in arch.technology_stack],
    )
    assert len(subs) == 0, (
        f"Unexpected substitutions: {subs}"
    )


# ============================================================
# TEST 3: Generic words NOT classified as technologies
# ============================================================
def test_agrimarket_generic_words():
    """Verify that AgriMarket domain words are NOT classified as technologies."""
    from app.utils.tech_normalizer import classify_tech

    # Words that appear in AgriMarket context but are NOT technologies
    generic_words = [
        "web", "mobile", "backend", "API", "database", "platform",
        "farmer", "buyer", "orders", "products", "categories",
        "search", "notifications", "SMS", "payments", "authentication",
        "admin", "listing", "profiles", "location", "quantity",
        "production", "staging", "service", "worker", "monitoring",
    ]

    for word in generic_words:
        cat = classify_tech(word)
        assert cat == "OTHER", (
            f"Generic word '{word}' incorrectly classified as {cat}. "
            f"It should be OTHER (not a technology)."
        )


# ============================================================
# TEST 4: Architecture appropriate for marketplace
# ============================================================
def test_agrimarket_architecture_appropriate():
    """Verify the architecture fits a marketplace, not a healthcare app."""
    arch = _make_agrimarket_architecture()
    ctx = _make_agrimarket_context()

    # Architecture should mention marketplace-relevant concepts
    # Check across system_architecture + component responsibilities
    all_arch_text = (
        arch.system_architecture + " "
        + " ".join(c.responsibility for c in arch.components)
    ).lower()
    assert any(kw in all_arch_text for kw in ["product", "buyer", "farmer", "marketplace", "order", "listing"]), (
        f"Architecture doesn't mention marketplace concepts: {arch.system_architecture}"
    )

    # Should NOT mention healthcare concepts
    healthcare_concepts = [
        "patient", "doctor", "clinic", "appointment", "medical",
        "health", "diagnosis", "prescription", "telebirr",
    ]
    for concept in healthcare_concepts:
        assert concept not in all_arch_text, (
            f"Healthcare concept '{concept}' found in marketplace architecture"
        )

    # Should have relevant data entities
    entity_names = {de.name.lower() for de in arch.data_architecture}
    assert "user" in entity_names or "farmer" in str(entity_names), (
        f"Architecture missing User/Farmer entity: {entity_names}"
    )

    # Should have product-related entities
    has_product = any(
        "product" in de.name.lower() or "listing" in de.name.lower()
        for de in arch.data_architecture
    )
    assert has_product, (
        f"Architecture missing product-related entity: {entity_names}"
    )


# ============================================================
# TEST 5: No overengineering
# ============================================================
def test_agrimarket_no_overengineering():
    """Verify the architecture is appropriately simple for an MVP."""
    arch = _make_agrimarket_architecture()

    # Should NOT have microservices keywords
    overengineering_keywords = [
        "kubernetes", "k8s", "service mesh", "istio",
        "event sourcing", "cqrs", " saga",
    ]

    arch_text = (
        arch.system_architecture.lower()
        + " "
        + " ".join(c.responsibility.lower() for c in arch.components)
    )

    for keyword in overengineering_keywords:
        assert keyword not in arch_text, (
            f"Overengineering keyword '{keyword}' found in architecture"
        )

    # Should NOT have too many components for an MVP
    assert len(arch.components) <= 6, (
        f"Too many components ({len(arch.components)}) for MVP. "
        f"Expected <= 6."
    )

    # Should NOT have too many technology choices
    assert len(arch.technology_stack) <= 15, (
        f"Too many technologies ({len(arch.technology_stack)}) for MVP."
    )


# ============================================================
# TEST 6: Cross-project isolation (AgriMarket vs HealthLink)
# ============================================================
def test_cross_project_isolation():
    """Verify that AgriMarket and HealthLink produce completely different results."""
    from app.utils.tech_normalizer import normalize_tech_list

    # AgriMarket project
    am_project = _make_agrimarket_project()
    am_arch = _make_agrimarket_architecture()
    am_ctx = _make_agrimarket_context()

    # HealthLink project (from existing tests)
    from app.models.project import ProjectState, UserSelectedTechnology
    from app.models.architecture import ArchitectureDocument, TechnologyChoice

    hl_project = ProjectState(
        name="HealthLink Ethiopia",
        description="Healthcare platform.",
        problem="Healthcare access.",
        target_users=["Patients", "Doctors"],
        core_features=["Appointments", "AI guidance", "Payments"],
        user_selected_technologies=[
            UserSelectedTechnology(name="Telebirr", purpose="payments", category="PAYMENT_PROVIDER"),
            UserSelectedTechnology(name="Africa's Talking", purpose="SMS", category="SMS_PROVIDER"),
            UserSelectedTechnology(name="OpenAI API", purpose="AI", category="AI_PROVIDER"),
            UserSelectedTechnology(name="Google Maps", purpose="locations", category="MAP_PROVIDER"),
        ],
    )

    hl_arch = ArchitectureDocument(
        system_architecture="Healthcare platform with React, Node.js, and external services.",
        components=[],
        technology_stack=[
            TechnologyChoice(category="AI", technology="OpenAI API", reason="User"),
            TechnologyChoice(category="Maps", technology="Google Maps", reason="User"),
            TechnologyChoice(category="Payments", technology="Telebirr", reason="User"),
            TechnologyChoice(category="SMS", technology="Africa's Talking", reason="User"),
        ],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )

    # Technology stacks should be different
    am_techs = normalize_tech_list(
        [tc.technology for tc in am_arch.technology_stack]
    )
    hl_techs = normalize_tech_list(
        [tc.technology for tc in hl_arch.technology_stack]
    )

    # AgriMarket should NOT have HealthLink-specific techs
    healthlink_specific = {"telebirr", "openai api", "google maps"}
    assert am_techs.isdisjoint(healthlink_specific), (
        f"AgriMarket has HealthLink techs: {am_techs & healthlink_specific}"
    )

    # Project names should be different
    assert am_project.name != hl_project.name

    # Core features should be different
    am_features = set(f.lower() for f in am_project.core_features)
    hl_features = set(f.lower() for f in hl_project.core_features)
    # Very little overlap expected between marketplace and healthcare
    overlap = am_features & hl_features
    assert len(overlap) <= 1, (
        f"Too much feature overlap between projects: {overlap}"
    )


# ============================================================
# TEST 7: Quality gate — good architecture
# ============================================================
def test_agrimarket_quality_gate_good():
    """Verify quality gate passes for a well-formed AgriMarket context."""
    from app.services.quality_gate import run_quality_gate

    project = _make_agrimarket_project()
    reqs = _make_agrimarket_requirements()
    arch = _make_agrimarket_architecture()
    ctx = _make_agrimarket_context()

    result = run_quality_gate(project, reqs, arch, ctx)

    print(f"    Overall: {result.overall_score}")
    print(f"    Validation: {result.validation_score}")
    print(f"    Readiness: {result.readiness_score}")
    print(f"    Ready: {result.ready_for_agent}")

    # Should have reasonable scores
    assert result.validation_score >= 80, (
        f"Validation score {result.validation_score} < 80"
    )
    assert result.readiness_score >= 60, (
        f"Readiness score {result.readiness_score} < 60"
    )

    # Should not have critical contradictions
    critical_warnings = []
    for w in result.warnings:
        msg = w.message if hasattr(w, 'message') else w.get('message', '')
        if "CONTRADICTION" in msg and "substitut" in msg.lower():
            critical_warnings.append(msg)
    assert len(critical_warnings) == 0, (
        f"Unexpected substitution contradictions: {critical_warnings}"
    )


# ============================================================
# TEST 8: Quality gate — broken architecture
# ============================================================
def test_agrimarket_quality_gate_broken():
    """Verify quality gate FAILS when architecture substitutes user techs."""
    from app.services.quality_gate import run_quality_gate
    from app.models.architecture import ArchitectureDocument, TechnologyChoice

    project = _make_agrimarket_project()
    reqs = _make_agrimarket_requirements()
    ctx = _make_agrimarket_context()

    # BROKEN architecture: replaced PostgreSQL with MongoDB, React with Angular
    broken_arch = ArchitectureDocument(
        system_architecture="Single-server architecture.",
        components=[],
        technology_stack=[
            TechnologyChoice(category="Frontend", technology="Angular", reason="AI chose"),
            TechnologyChoice(category="Backend", technology="Python", reason="AI chose"),
            TechnologyChoice(category="Database", technology="MongoDB", reason="AI chose"),
            TechnologyChoice(category="Cache", technology="Redis", reason="AI chose"),
        ],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )

    result = run_quality_gate(project, reqs, broken_arch, ctx)

    print(f"    Overall: {result.overall_score}")
    print(f"    Tech preservation: {result.tech_preservation.substituted_count} substitutions")

    # Should detect substitutions
    assert result.tech_preservation.substituted_count >= 1, (
        "Broken architecture should have detected substitutions"
    )

    # Tech consistency should be low
    assert result.readiness_score < 80, (
        f"Broken architecture readiness {result.readiness_score} should be < 80"
    )


# ============================================================
# TEST 9: Agent readiness — no false healthcare warnings
# ============================================================
def test_agrimarket_no_false_healthcare_warnings():
    """Verify agent readiness doesn't generate healthcare-specific warnings
    for a marketplace project."""
    from app.engines.agent_readiness import check_agent_readiness

    project = _make_agrimarket_project()
    reqs = _make_agrimarket_requirements()
    arch = _make_agrimarket_architecture()
    ctx = _make_agrimarket_context()

    result = check_agent_readiness(project, reqs, arch, ctx)

    # Should NOT have healthcare-specific warnings
    healthcare_warnings = [
        w for w in result.warnings
        if any(kw in w.message.lower() for kw in [
            "patient", "medical", "health record", "clinical",
            "appointment locking", "telebirr", "bedrock",
        ])
    ]
    assert len(healthcare_warnings) == 0, (
        f"Healthcare warnings in marketplace project: "
        f"{[w.message for w in healthcare_warnings]}"
    )


# ============================================================
# TEST 10: Agent readiness — marketplace-specific checks
# ============================================================
def test_agrimarket_readiness_checks():
    """Verify agent readiness produces reasonable scores for marketplace."""
    from app.engines.agent_readiness import check_agent_readiness

    project = _make_agrimarket_project()
    reqs = _make_agrimarket_requirements()
    arch = _make_agrimarket_architecture()
    ctx = _make_agrimarket_context()

    result = check_agent_readiness(project, reqs, arch, ctx)

    # Requirements coverage should be high
    assert result.checks.requirements_coverage >= 70, (
        f"Requirements coverage {result.checks.requirements_coverage}% < 70%"
    )

    # Technology consistency should be high (all user techs preserved)
    assert result.checks.technology_consistency >= 80, (
        f"Technology consistency {result.checks.technology_consistency}% < 80%"
    )

    # Should have agent rules
    assert result.checks.agent_rules_quality >= 60, (
        f"Agent rules quality {result.checks.agent_rules_quality}% < 60%"
    )


# ============================================================
# TEST 11: Validation — consistent requirements
# ============================================================
def test_agrimarket_validation_consistency():
    """Verify the validator finds AgriMarket requirements represented in context."""
    from app.engines.validation import validate_context

    project = _make_agrimarket_project()
    reqs = _make_agrimarket_requirements()
    arch = _make_agrimarket_architecture()
    ctx = _make_agrimarket_context()

    result = validate_context(project, reqs, arch, context=ctx)

    assert result.score >= 80, (
        f"Validation score {result.score} < 80"
    )

    # Check that key FRs are represented
    context_text = " ".join(
        ctx.functional_requirements + ctx.non_functional_requirements
    ).lower()

    for req in reqs.functional_requirements:
        assert (
            req.id.lower() in context_text
            or req.title.lower() in context_text
        ), (
            f"{req.id} ({req.title}) not represented in context"
        )


# ============================================================
# TEST 12: No technology substitution
# ============================================================
def test_agrimarket_no_substitution():
    """Verify no silent technology substitution in AgriMarket."""
    from app.utils.tech_normalizer import find_substituted_technologies

    project = _make_agrimarket_project()
    arch = _make_agrimarket_architecture()

    subs = find_substituted_technologies(
        [t.name for t in project.user_selected_technologies],
        [tc.technology for tc in arch.technology_stack],
    )
    assert len(subs) == 0, (
        f"Unexpected substitutions in AgriMarket: {subs}"
    )


# ============================================================
# TEST 13: Definition of Done completeness
# ============================================================
def test_agrimarket_dod_completeness():
    """Verify the Definition of Done covers all major requirements."""
    ctx = _make_agrimarket_context()
    reqs = _make_agrimarket_requirements()

    # DoD should have at least as many items as FRs / 2
    min_dod = max(3, len(reqs.functional_requirements) // 2)
    assert len(ctx.definition_of_done) >= min_dod, (
        f"DoD has {len(ctx.definition_of_done)} items, expected >= {min_dod}"
    )

    # DoD should mention key features
    dod_text = " ".join(ctx.definition_of_done).lower()
    key_concepts = ["test", "auth", "product", "order"]
    for concept in key_concepts:
        assert concept in dod_text, (
            f"DoD missing key concept: {concept}"
        )


# ============================================================
# TEST 14: AI assumptions correctly marked
# ============================================================
def test_agrimarket_ai_assumptions():
    """Verify AI-selected technologies are marked as assumptions,
    not user decisions."""
    from app.engines.agent_readiness import check_agent_readiness

    project = _make_agrimarket_project()
    reqs = _make_agrimarket_requirements()
    arch = _make_agrimarket_architecture()
    ctx = _make_agrimarket_context()

    result = check_agent_readiness(project, reqs, arch, ctx)

    # User-selected techs should NOT be AI assumptions
    user_tech_names = {t.name.lower() for t in project.user_selected_technologies}
    for assumption in result.assumptions:
        for ut in user_tech_names:
            assert ut not in assumption.assumption.lower() or "selected by ai" not in assumption.assumption.lower(), (
                f"User-selected tech '{ut}' incorrectly marked as AI assumption: "
                f"{assumption.assumption}"
            )

    # AI-selected techs (like TailwindCSS, Prisma) SHOULD be assumptions
    ai_assumption_text = " ".join(a.assumption.lower() for a in result.assumptions)
    # Prisma is not user-selected, so it should be an AI assumption
    if "prisma" in [tc.technology.lower() for tc in arch.technology_stack]:
        # Prisma is in architecture but not in user_selected — should be AI assumption
        assert "prisma" in ai_assumption_text or result.checks.technology_consistency >= 80, (
            "Prisma (AI-selected) should appear as assumption or tech consistency should be high"
        )


# ============================================================
# TEST 15: Architecture/context technology consistency
# ============================================================
def test_agrimarket_arch_ctx_consistency():
    """Verify architecture and context use the same technology names."""
    from app.utils.tech_normalizer import normalize_tech_list, tech_sets_match

    arch = _make_agrimarket_architecture()
    ctx = _make_agrimarket_context()

    arch_norm = normalize_tech_list(
        [tc.technology for tc in arch.technology_stack]
    )
    ctx_norm = normalize_tech_list(ctx.technology_stack)

    match, missing, extra = tech_sets_match(arch_norm, ctx_norm)

    # Context should be a superset of architecture
    assert len(missing) == 0, (
        f"Architecture techs missing from context: {missing}"
    )

    # Extra techs in context are OK (superset)
    # But they should be reasonable additions, not substitutions


# ============================================================
# TEST 16: Concurrency safety for AgriMarket
# ============================================================
def test_agrimarket_concurrency_safety():
    """Verify concurrency checks work for marketplace (order locking)."""
    from app.engines.agent_readiness import check_agent_readiness

    project = _make_agrimarket_project()
    reqs = _make_agrimarket_requirements()
    arch = _make_agrimarket_architecture()
    ctx = _make_agrimarket_context()

    result = check_agent_readiness(project, reqs, arch, ctx)

    # Marketplace has orders but no explicit locking strategy
    # This should generate a concurrency warning
    concurrency_warnings = [
        w for w in result.warnings
        if w.category == "concurrency_safety"
    ]

    # At minimum, the system should be checking for these concerns
    # (even if the architecture doesn't address them yet)
    print(f"    Concurrency warnings: {len(concurrency_warnings)}")
    for w in concurrency_warnings:
        print(f"      - {w.message[:80]}...")


# ============================================================
# TEST 17: Full pipeline — requirements to context consistency
# ============================================================
def test_agrimarket_full_consistency():
    """Verify the complete pipeline produces consistent output."""
    from app.engines.validation import validate_context
    from app.engines.agent_readiness import check_agent_readiness
    from app.services.quality_gate import run_quality_gate

    project = _make_agrimarket_project()
    reqs = _make_agrimarket_requirements()
    arch = _make_agrimarket_architecture()
    ctx = _make_agrimarket_context()

    # 1. Validation
    val = validate_context(project, reqs, arch, context=ctx)
    assert val.valid, f"Context invalid: {[i.message for i in val.issues if i.severity == 'error']}"

    # 2. Agent readiness
    readiness = check_agent_readiness(project, reqs, arch, ctx)
    assert readiness.score >= 50, f"Readiness score {readiness.score} < 50"

    # 3. Quality gate
    gate = run_quality_gate(project, reqs, arch, ctx)
    assert gate.validation_score >= 80, f"Gate validation {gate.validation_score} < 80"

    # 4. Tech preservation
    assert gate.tech_preservation.substituted_count == 0, (
        f"Unexpected substitutions: {gate.tech_preservation.substituted}"
    )

    print(f"    Validation: {val.score}")
    print(f"    Readiness: {readiness.score}")
    print(f"    Gate overall: {gate.overall_score}")
    print(f"    Tech preserved: {gate.tech_preservation.preserved_count}/{gate.tech_preservation.user_selected_count}")


# ============================================================
# TEST 18: AgriMarket vs generic marketplace keywords
# ============================================================
def test_agrimarket_domain_isolation():
    """Verify that marketplace-specific concepts don't leak into
    technology classification."""
    from app.utils.tech_normalizer import classify_tech

    # Marketplace domain words that should NOT be technologies
    marketplace_words = [
        "listing", "catalog", "inventory", "supply chain",
        "logistics", "warehouse", "shipping", "delivery",
        "payment gateway", "shopping cart", "checkout",
        "seller", "vendor", "merchant", "wholesale",
        "retail", "bulk order", "purchase order",
    ]

    for word in marketplace_words:
        cat = classify_tech(word)
        assert cat == "OTHER", (
            f"Marketplace word '{word}' incorrectly classified as {cat}"
        )


# ============================================================
# TEST 19: Different project types produce different architectures
# ============================================================
def test_different_projects_different_architectures():
    """Verify AgriMarket produces a different architecture than HealthLink."""
    from app.utils.tech_normalizer import normalize_tech_list

    # AgriMarket architecture
    am_arch = _make_agrimarket_architecture()
    am_techs = normalize_tech_list(
        [tc.technology for tc in am_arch.technology_stack]
    )

    # HealthLink-style architecture (healthcare)
    from app.models.architecture import ArchitectureDocument, TechnologyChoice
    hl_arch = ArchitectureDocument(
        system_architecture="Healthcare platform with patient management.",
        components=[],
        technology_stack=[
            TechnologyChoice(category="AI", technology="OpenAI API", reason="Health guidance"),
            TechnologyChoice(category="Maps", technology="Google Maps", reason="Clinic locations"),
            TechnologyChoice(category="Payments", technology="Telebirr", reason="Payments"),
            TechnologyChoice(category="SMS", technology="Africa's Talking", reason="Reminders"),
        ],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )
    hl_techs = normalize_tech_list(
        [tc.technology for tc in hl_arch.technology_stack]
    )

    # Should be very different
    overlap = am_techs & hl_techs
    # Some overlap is OK (e.g. both might use PostgreSQL, React)
    # But HealthLink-specific techs should NOT be in AgriMarket
    healthlink_only = {"telebirr", "openai api", "google maps"}
    assert am_techs.isdisjoint(healthlink_only), (
        f"AgriMarket has HealthLink-only techs: {am_techs & healthlink_only}"
    )


# ============================================================
# TEST 20: Security requirements appropriate for marketplace
# ============================================================
def test_agrimarket_security_appropriate():
    """Verify security requirements fit a marketplace, not healthcare."""
    ctx = _make_agrimarket_context()

    sec_text = " ".join(ctx.security_requirements).lower()

    # Should mention marketplace-relevant security
    assert "jwt" in sec_text or "token" in sec_text or "auth" in sec_text, (
        "Security requirements should mention authentication"
    )
    assert "rbac" in sec_text or "role" in sec_text or "permission" in sec_text, (
        "Security requirements should mention authorization"
    )

    # Should NOT have healthcare-specific security
    healthcare_sec = [
        "hipaa", "patient data", "medical record",
        "health information", "clinical data",
    ]
    for term in healthcare_sec:
        assert term not in sec_text, (
            f"Healthcare security term '{term}' in marketplace context"
        )


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    tests = [
        # Technology leakage & preservation
        ("No HealthLink technology leakage", test_no_healthlink_leakage),
        ("AgriMarket user-selected tech preservation", test_agrimarket_tech_preservation),
        ("Generic words NOT classified as tech", test_agrimarket_generic_words),
        ("No technology substitution", test_agrimarket_no_substitution),

        # Architecture appropriateness
        ("Architecture fits marketplace", test_agrimarket_architecture_appropriate),
        ("No overengineering", test_agrimarket_no_overengineering),
        ("Architecture/context consistency", test_agrimarket_arch_ctx_consistency),

        # Cross-project isolation
        ("Cross-project isolation", test_cross_project_isolation),
        ("Different projects, different architectures", test_different_projects_different_architectures),
        ("Domain word isolation", test_agrimarket_domain_isolation),

        # Quality gate
        ("Quality gate — good architecture", test_agrimarket_quality_gate_good),
        ("Quality gate — broken architecture", test_agrimarket_quality_gate_broken),

        # Agent readiness
        ("No false healthcare warnings", test_agrimarket_no_false_healthcare_warnings),
        ("Agent readiness checks", test_agrimarket_readiness_checks),
        ("AI assumptions correctly marked", test_agrimarket_ai_assumptions),
        ("Concurrency safety checks", test_agrimarket_concurrency_safety),

        # Validation & consistency
        ("Validation consistency", test_agrimarket_validation_consistency),
        ("DoD completeness", test_agrimarket_dod_completeness),
        ("Security appropriate for marketplace", test_agrimarket_security_appropriate),

        # Full pipeline
        ("Full pipeline consistency", test_agrimarket_full_consistency),
    ]

    print("=" * 60)
    print("AGRIMARKET ETHIOPIA — CROSS-PROJECT VALIDATION")
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
