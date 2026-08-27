import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.engines.artifact import create_artifact
from app.engines.validation import validate_context
from app.services.artifact_store import get_artifact

from app.models.project import ProjectState
from app.models.requirements import RequirementsDocument
from app.models.architecture import ArchitectureDocument
from app.models.context import ImplementationContext


def main():

    print("=" * 60)
    print("Generating artifact...")
    print("=" * 60)

    project = ProjectState(
        name="Yibe Market",
        description="An online supermarket.",
        problem="Customers need online shopping.",
        target_users=["Customer", "Administrator"],
        core_features=["Browse products", "Place orders"],
        platform="Both web and mobile",
        technologies=[],
        database=None,
        authentication="Customer and admin accounts",
        integrations=["Online payment", "Notifications"],
        constraints=["Limited budget"],
        deployment="Cloud hosting"
    )

    requirements = RequirementsDocument(
        functional_requirements=[
            {"id": "FR-001", "title": "Browse Products", "description": "View products.", "priority": "MUST_HAVE", "actors": ["Customer"], "acceptance_criteria": [{"description": "Can view products."}]},
            {"id": "FR-002", "title": "Place Orders", "description": "Place orders.", "priority": "MUST_HAVE", "actors": ["Customer"], "acceptance_criteria": [{"description": "Can place orders."}]},
            {"id": "FR-003", "title": "Payment", "description": "Process payments.", "priority": "MUST_HAVE", "actors": ["Customer"], "acceptance_criteria": [{"description": "Payments work."}]},
            {"id": "FR-004", "title": "Notifications", "description": "Send notifications.", "priority": "SHOULD_HAVE", "actors": ["Customer"], "acceptance_criteria": [{"description": "Notifications sent."}]},
            {"id": "FR-005", "title": "Auth", "description": "User login.", "priority": "MUST_HAVE", "actors": ["Customer"], "acceptance_criteria": [{"description": "Login works."}]},
            {"id": "FR-006", "title": "Admin Auth", "description": "Admin login.", "priority": "MUST_HAVE", "actors": ["Admin"], "acceptance_criteria": [{"description": "Admin login."}]},
            {"id": "FR-007", "title": "Manage Products", "description": "Admin CRUD.", "priority": "MUST_HAVE", "actors": ["Admin"], "acceptance_criteria": [{"description": "CRUD works."}]},
            {"id": "FR-008", "title": "Manage Orders", "description": "Admin orders.", "priority": "MUST_HAVE", "actors": ["Admin"], "acceptance_criteria": [{"description": "Orders managed."}]}
        ],
        non_functional_requirements=[
            {"id": "NFR-001", "title": "Security", "description": "Protect data.", "priority": "MUST_HAVE", "actors": [], "acceptance_criteria": [{"description": "Secure."}]},
            {"id": "NFR-002", "title": "Performance", "description": "Fast.", "priority": "SHOULD_HAVE", "actors": [], "acceptance_criteria": [{"description": "Fast."}]}
        ]
    )

    architecture = ArchitectureDocument(
        system_architecture="Three-tier monolith.",
        components=[{"name": "Frontend", "responsibility": "UI", "technologies": ["React"]}],
        technology_stack=[{"category": "Frontend", "technology": "React", "reason": "UI"}],
        data_architecture=[{"name": "User", "purpose": "Accounts", "important_fields": ["id"]}],
        api_design=[{"name": "Auth", "purpose": "Login", "endpoints": ["POST /api/auth/login"]}],
        security=[{"area": "Passwords", "decision": "bcrypt", "reason": "Security"}],
        deployment=[{"environment": "Production", "services": ["Docker"], "reason": "Deploy"}]
    )

    context = ImplementationContext(
        project_title="Yibe Market",
        project_summary="Online supermarket.",
        problem="Customers need online shopping.",
        target_users=["Customer", "Administrator"],
        functional_requirements=[
            "FR-001: Browse Products - Customers can view products.",
            "FR-002: Place Orders - Customers can place orders.",
            "FR-003: Payment - System processes payments.",
            "FR-004: Notifications - System sends notifications.",
            "FR-005: Auth - Customers can login.",
            "FR-006: Admin Auth - Admins can login.",
            "FR-007: Manage Products - Admins manage products.",
            "FR-008: Manage Orders - Admins manage orders."
        ],
        non_functional_requirements=[
            "NFR-001: Security - Protect user data.",
            "NFR-002: Performance - Fast response times."
        ],
        architecture_summary="Three-tier monolith with React and Node.js.",
        technology_stack=["React", "Node.js", "PostgreSQL", "Stripe", "Docker"],
        data_model=["User: id, email", "Product: id, name"],
        api_contract=["POST /api/auth/login", "GET /api/products"],
        security_requirements=["Use bcrypt", "Enforce HTTPS"],
        implementation_phases=[{"phase": 1, "name": "Setup", "objective": "Init project", "tasks": ["Create repo"], "deliverables": ["Dev env"]}],
        agent_rules=[{"category": "Security", "rule": "No hardcoded secrets"}],
        definition_of_done=["All features implemented", "Tests pass"]
    )

    validation = validate_context(project, requirements, architecture, context)
    artifact = create_artifact(context=context, validation=validation)

    project_id = artifact.project_id
    print(f"\nProject ID: {project_id}")
    print(f"Project Name: {artifact.project_name}")
    print(f"Validation: {artifact.valid}")
    print(f"Score: {artifact.validation_score}")
    print(f"Markdown length: {len(artifact.markdown)}")

    # Verify artifact is stored
    stored = get_artifact(project_id)
    assert stored is not None, "Artifact not found in store!"
    print("Artifact stored in memory: OK")

    print("\n" + "=" * 60)
    print("TEST 1: Verify markdown content")
    print("=" * 60)

    assert "# Yibe Market" in artifact.markdown
    assert "FR-001" in artifact.markdown
    assert "React" in artifact.markdown
    assert "Definition of Done" in artifact.markdown
    print("Markdown content verified: PASSED")

    print("\n" + "=" * 60)
    print("TEST 2: Verify text content")
    print("=" * 60)

    assert artifact.text == artifact.markdown
    print("Text content matches markdown: PASSED")

    print("\n" + "=" * 60)
    print("TEST 3: Verify artifact store")
    print("=" * 60)

    assert get_artifact(project_id) is not None
    assert get_artifact("nonexistent") is None
    print("Artifact store works correctly: PASSED")

    print("\n" + "=" * 60)
    print("TEST 4: Verify invalid artifact rejected")
    print("=" * 60)

    from app.models.validation import ContextValidationResult

    broken_context = ImplementationContext(
        project_title="",
        project_summary="",
        problem="",
        target_users=[],
        functional_requirements=[],
        non_functional_requirements=[],
        architecture_summary="",
        technology_stack=[],
        data_model=[],
        api_contract=[],
        security_requirements=[],
        implementation_phases=[],
        agent_rules=[],
        definition_of_done=[]
    )

    broken_validation = validate_context(project, requirements, architecture, broken_context)

    try:
        create_artifact(context=broken_context, validation=broken_validation)
        print("ERROR: Should have raised ValueError!")
    except ValueError as error:
        print(f"Correctly rejected: {error}")
        print("Invalid artifact rejection: PASSED")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)

    print(f"\nTo download via API (after server restart):")
    print(f"  GET http://127.0.0.1:8000/export/{project_id}/markdown")
    print(f"  GET http://127.0.0.1:8000/export/{project_id}/txt")


main()
