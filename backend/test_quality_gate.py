import os
os.environ.setdefault("OPENROUTER_API_KEY", "test")
os.environ.setdefault("OPENROUTER_MODEL", "test")

from app.models.project import ProjectState
from app.models.requirements import RequirementsDocument
from app.models.architecture import ArchitectureDocument
from app.models.context import ImplementationContext
from app.services.quality_gate import run_quality_gate, QualityGateResult


# ============================================================
# Test data
# ============================================================

project = ProjectState(
    name="Yibe Market",
    description="An online supermarket.",
    problem="Convenient online shopping.",
    target_users=["Customers", "Administrators"],
    core_features=["Browse products", "Place orders", "Online payment"],
    platform="Both web and mobile",
    technologies=[],
    database=None,
    authentication="Customer and admin accounts",
    integrations=["Online payment", "Notifications"],
    constraints=["Limited budget"],
    deployment="Cloud hosting",
)

requirements = RequirementsDocument(
    functional_requirements=[
        {"id": "FR-001", "title": "Browse Product Catalog", "description": "Browse products", "priority": "MUST_HAVE", "actors": ["Customer"], "acceptance_criteria": [{"description": "View products"}]},
        {"id": "FR-002", "title": "Place Orders", "description": "Place orders", "priority": "MUST_HAVE", "actors": ["Customer"], "acceptance_criteria": [{"description": "Place order"}]},
        {"id": "FR-003", "title": "Online Payment", "description": "Pay online", "priority": "MUST_HAVE", "actors": ["Customer"], "acceptance_criteria": [{"description": "Pay via Stripe"}]},
        {"id": "FR-004", "title": "Manage Products", "description": "Admin manages products", "priority": "MUST_HAVE", "actors": ["Admin"], "acceptance_criteria": [{"description": "CRUD products"}]},
        {"id": "FR-005", "title": "Manage Orders", "description": "Admin manages orders", "priority": "MUST_HAVE", "actors": ["Admin"], "acceptance_criteria": [{"description": "Update status"}]},
    ],
    non_functional_requirements=[
        {"id": "NFR-001", "title": "Security", "description": "Secure system", "priority": "MUST_HAVE", "actors": [], "acceptance_criteria": [{"description": "JWT auth"}]},
        {"id": "NFR-002", "title": "Performance", "description": "Fast loading", "priority": "SHOULD_HAVE", "actors": [], "acceptance_criteria": [{"description": "2s load"}]},
    ],
)

architecture = ArchitectureDocument(
    system_architecture="Three-tier monolith: React frontend, Node.js/Express API, PostgreSQL database.",
    components=[
        {"name": "Web App", "responsibility": "Customer UI", "technologies": ["React", "TypeScript"]},
        {"name": "API", "responsibility": "Backend logic", "technologies": ["Node.js", "Express"]},
        {"name": "Database", "responsibility": "Data storage", "technologies": ["PostgreSQL"]},
    ],
    technology_stack=[
        {"category": "Frontend", "technology": "React", "reason": "Component-based UI"},
        {"category": "Language", "technology": "TypeScript", "reason": "Type safety"},
        {"category": "Backend", "technology": "Node.js", "reason": "JS runtime"},
        {"category": "Framework", "technology": "Express", "reason": "Minimal framework"},
        {"category": "Database", "technology": "PostgreSQL", "reason": "Relational DB"},
        {"category": "Auth", "technology": "JWT", "reason": "Stateless auth"},
        {"category": "Payments", "technology": "Stripe", "reason": "PCI compliant"},
    ],
    data_architecture=[
        {"name": "User", "purpose": "User accounts", "important_fields": ["id", "email", "role"]},
        {"name": "Product", "purpose": "Product catalog", "important_fields": ["id", "name", "price"]},
        {"name": "Order", "purpose": "Customer orders", "important_fields": ["id", "user_id", "status"]},
        {"name": "Payment", "purpose": "Payment records", "important_fields": ["id", "order_id", "amount"]},
    ],
    api_design=[
        {"name": "Auth", "purpose": "Authentication", "endpoints": ["POST /auth/register", "POST /auth/login"]},
        {"name": "Products", "purpose": "Product CRUD", "endpoints": ["GET /products", "POST /products"]},
        {"name": "Orders", "purpose": "Order management", "endpoints": ["POST /orders", "GET /orders"]},
        {"name": "Payments", "purpose": "Payment processing", "endpoints": ["POST /payments/create-intent"]},
    ],
    security=[
        {"area": "Authentication", "decision": "JWT with bcrypt", "reason": "Stateless auth"},
        {"area": "API Security", "decision": "Rate limiting, CORS", "reason": "Protection"},
        {"area": "Payments", "decision": "Stripe PCI compliance", "reason": "No card storage"},
    ],
    deployment=[
        {"environment": "Production", "services": ["Docker", "AWS ECS"], "reason": "Scalable deployment"},
    ],
)

good_context = ImplementationContext(
    project_title="Yibe Market",
    project_summary="Online supermarket for browsing and ordering products.",
    problem="Convenient online shopping.",
    target_users=["Customer", "Administrator"],
    functional_requirements=[
        "FR-001: Browse Product Catalog - View products with name, price, category",
        "FR-002: Place Orders - Add to cart and place orders",
        "FR-003: Online Payment - Pay via Stripe",
        "FR-004: Manage Products - Admin CRUD for products",
        "FR-005: Manage Orders - Admin order management",
    ],
    non_functional_requirements=[
        "NFR-001: Security - JWT auth, bcrypt, input validation",
        "NFR-002: Performance - 2s load time",
    ],
    architecture_summary="Three-tier monolith: React, Node.js/Express, PostgreSQL.",
    technology_stack=["React", "TypeScript", "Node.js", "Express", "PostgreSQL", "JWT", "Stripe"],
    data_model=["User: id, email, role", "Product: id, name, price", "Order: id, user_id, status", "Payment: id, order_id, amount"],
    api_contract=["POST /auth/register", "GET /products", "POST /orders", "POST /payments/create-intent"],
    security_requirements=["JWT auth with bcrypt", "Rate limiting", "Stripe PCI compliance"],
    implementation_phases=[
        {"phase": 1, "name": "Foundation", "objective": "Set up project and auth", "tasks": ["Init project", "User model", "Auth endpoints"], "deliverables": ["Working auth"]},
        {"phase": 2, "name": "Products", "objective": "Product catalog", "tasks": ["Product CRUD", "Categories"], "deliverables": ["Product API"]},
        {"phase": 3, "name": "Orders", "objective": "Order flow", "tasks": ["Cart", "Orders", "Payments"], "deliverables": ["Order flow"]},
    ],
    agent_rules=[
        {"category": "Architecture", "rule": "Keep monolith. No microservices."},
        {"category": "Security", "rule": "Never hardcode secrets."},
        {"category": "Testing", "rule": "Write integration tests for all endpoints."},
    ],
    definition_of_done=[
        "All FRs implemented and verified",
        "All NFRs met",
        "Integration tests passing",
        "Deployed to cloud",
    ],
)


# ============================================================
# Test 1: Excellent context
# ============================================================

print("=" * 60)
print("TEST 1: Excellent context (should PASS)")
print("=" * 60)

result = run_quality_gate(project, requirements, architecture, good_context)

print(f"  Passed:     {result.passed}")
print(f"  Score:      {result.overall_score}/100")
print(f"  Validation: {result.validation_score}")
print(f"  Readiness:  {result.readiness_score}")
print(f"  Ready:      {result.ready_for_agent}")
print(f"  Warnings:   {len(result.warnings)}")
print(f"  Assumptions: {len(result.assumptions)}")
assert result.passed, "Expected gate to PASS"
print("  >>> PASS\n")


# ============================================================
# Test 2: Degraded context (should FAIL)
# ============================================================

print("=" * 60)
print("TEST 2: Degraded context (should FAIL)")
print("=" * 60)

bad_context = ImplementationContext(
    project_title="Yibe Market",
    project_summary="Online store.",
    problem="Shopping.",
    target_users=[],
    functional_requirements=["Browse products"],
    non_functional_requirements=[],
    architecture_summary="Web app.",
    technology_stack=["React"],
    data_model=[],
    api_contract=[],
    security_requirements=[],
    implementation_phases=[],
    agent_rules=[],
    definition_of_done=[],
)

result2 = run_quality_gate(project, requirements, architecture, bad_context)

print(f"  Passed:     {result2.passed}")
print(f"  Score:      {result2.overall_score}/100")
print(f"  Validation: {result2.validation_score}")
print(f"  Readiness:  {result2.readiness_score}")
print(f"  Ready:      {result2.ready_for_agent}")
print(f"  Rejections: {len(result2.rejection_reasons)}")
for r in result2.rejection_reasons:
    print(f"    - {r}")
assert not result2.passed, "Expected gate to FAIL"
print("  >>> PASS\n")


# ============================================================
# Test 3: Warnings only (should PASS)
# ============================================================

print("=" * 60)
print("TEST 3: Warnings only (should PASS)")
print("=" * 60)

context_with_warnings = ImplementationContext(
    project_title="Yibe Market",
    project_summary="Online supermarket for customers to browse and order products.",
    problem="Customers need convenient online shopping.",
    target_users=["Customer", "Administrator"],
    functional_requirements=[
        "FR-001: Browse Product Catalog",
        "FR-002: Place Orders",
        "FR-003: Online Payment via Stripe",
        "FR-004: Manage Products (Admin)",
        "FR-005: Manage Orders (Admin)",
    ],
    non_functional_requirements=[
        "NFR-001: Security with JWT and bcrypt",
        "NFR-002: Performance under 2 seconds",
    ],
    architecture_summary="Three-tier monolith with React, Express, PostgreSQL.",
    technology_stack=["React", "TypeScript", "Node.js", "Express", "PostgreSQL", "JWT", "Stripe"],
    data_model=["User", "Product", "Order", "Payment"],
    api_contract=["POST /auth/register", "GET /products", "POST /orders", "POST /payments"],
    security_requirements=["JWT authentication", "bcrypt passwords", "Input validation"],
    implementation_phases=[
        {"phase": 1, "name": "Foundation", "objective": "Set up project", "tasks": ["Init", "Auth"], "deliverables": ["Working auth"]},
        {"phase": 2, "name": "Features", "objective": "Build features", "tasks": ["Products", "Orders"], "deliverables": ["Full app"]},
    ],
    agent_rules=[
        {"category": "Architecture", "rule": "Keep as monolith"},
        {"category": "Security", "rule": "Use environment variables for secrets"},
    ],
    definition_of_done=[
        "All features implemented",
        "Tests passing",
        "Deployed",
    ],
)

result3 = run_quality_gate(project, requirements, architecture, context_with_warnings)

print(f"  Passed:     {result3.passed}")
print(f"  Score:      {result3.overall_score}/100")
print(f"  Warnings:   {len(result3.warnings)}")
print(f"  Assumptions: {len(result3.assumptions)}")
assert result3.passed, "Expected gate to PASS with warnings"
print("  >>> PASS\n")


# ============================================================
# Test 4: QualityGateResult structure
# ============================================================

print("=" * 60)
print("TEST 4: QualityGateResult structure")
print("=" * 60)

print(f"  Type: {type(result)}")
print(f"  Fields: {list(result.model_fields.keys())}")
assert hasattr(result, "passed")
assert hasattr(result, "validation_score")
assert hasattr(result, "readiness_score")
assert hasattr(result, "overall_score")
assert hasattr(result, "ready_for_agent")
assert hasattr(result, "checks")
assert hasattr(result, "warnings")
assert hasattr(result, "assumptions")
assert hasattr(result, "errors")
assert hasattr(result, "rejection_reasons")
print("  >>> PASS\n")


print("=" * 60)
print("ALL QUALITY GATE TESTS COMPLETE")
print("=" * 60)
