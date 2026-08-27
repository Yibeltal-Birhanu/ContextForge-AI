import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.engines.artifact import create_artifact
from app.engines.validation import validate_context

from app.models.project import ProjectState
from app.models.requirements import RequirementsDocument
from app.models.architecture import ArchitectureDocument
from app.models.context import ImplementationContext


project = ProjectState(
    name="Yibe Market",
    description="An online supermarket where customers can browse products and place orders.",
    problem="Customers need a convenient way to shop for supermarket products online.",
    target_users=["Customers", "Administrators"],
    core_features=["Browse products", "Add products to cart", "Place orders", "Online payment", "Order notifications", "Manage products", "Manage orders"],
    platform="Both web and mobile",
    technologies=[],
    database=None,
    authentication="Customer accounts and admin accounts",
    integrations=["Online payment", "Order notifications"],
    constraints=["Limited budget"],
    deployment="Cloud hosting"
)


requirements = RequirementsDocument(
    functional_requirements=[
        {"id": "FR-001", "title": "Browse Product Catalog", "description": "Customers can view products.", "priority": "MUST_HAVE", "actors": ["Customer"], "acceptance_criteria": [{"description": "Customer can view products."}]},
        {"id": "FR-002", "title": "Add to Cart and Place Order", "description": "Customers can add to cart and order.", "priority": "MUST_HAVE", "actors": ["Customer"], "acceptance_criteria": [{"description": "Customer can add to cart."}]},
        {"id": "FR-003", "title": "Online Payment Processing", "description": "System processes payments.", "priority": "MUST_HAVE", "actors": ["Customer"], "acceptance_criteria": [{"description": "Payment is processed."}]},
        {"id": "FR-004", "title": "Order Notifications", "description": "System sends notifications.", "priority": "SHOULD_HAVE", "actors": ["Customer", "Administrator"], "acceptance_criteria": [{"description": "Notifications are sent."}]},
        {"id": "FR-005", "title": "Customer Authentication", "description": "Customers can register and login.", "priority": "MUST_HAVE", "actors": ["Customer"], "acceptance_criteria": [{"description": "Customer can login."}]},
        {"id": "FR-006", "title": "Administrator Authentication", "description": "Admins can login.", "priority": "MUST_HAVE", "actors": ["Administrator"], "acceptance_criteria": [{"description": "Admin can login."}]},
        {"id": "FR-007", "title": "Manage Products (Admin)", "description": "Admins can manage products.", "priority": "MUST_HAVE", "actors": ["Administrator"], "acceptance_criteria": [{"description": "Admin can manage products."}]},
        {"id": "FR-008", "title": "Manage Orders (Admin)", "description": "Admins can manage orders.", "priority": "MUST_HAVE", "actors": ["Administrator"], "acceptance_criteria": [{"description": "Admin can manage orders."}]}
    ],
    non_functional_requirements=[
        {"id": "NFR-001", "title": "Security", "description": "Protect user credentials.", "priority": "MUST_HAVE", "actors": [], "acceptance_criteria": [{"description": "Credentials are protected."}]},
        {"id": "NFR-002", "title": "Performance", "description": "Fast response times.", "priority": "SHOULD_HAVE", "actors": [], "acceptance_criteria": [{"description": "Pages load quickly."}]},
        {"id": "NFR-003", "title": "Scalability & Deployment", "description": "Deployable on cloud.", "priority": "MUST_HAVE", "actors": [], "acceptance_criteria": [{"description": "Can be deployed to cloud."}]},
        {"id": "NFR-004", "title": "Usability", "description": "Intuitive UI.", "priority": "SHOULD_HAVE", "actors": [], "acceptance_criteria": [{"description": "UI is intuitive."}]}
    ]
)


architecture = ArchitectureDocument(
    system_architecture="Three-tier monolith: React frontend, Node.js/Express API, PostgreSQL database.",
    components=[{"name": "Frontend", "responsibility": "UI", "technologies": ["React"]}, {"name": "Backend", "responsibility": "API", "technologies": ["Node.js"]}, {"name": "Database", "responsibility": "Storage", "technologies": ["PostgreSQL"]}],
    technology_stack=[{"category": "Frontend", "technology": "React", "reason": "Component-based UI"}, {"category": "Backend", "technology": "Node.js/Express", "reason": "JavaScript reuse"}, {"category": "Database", "technology": "PostgreSQL", "reason": "ACID compliance"}],
    data_architecture=[{"name": "User", "purpose": "Accounts", "important_fields": ["id", "email"]}],
    api_design=[{"name": "Auth", "purpose": "Authentication", "endpoints": ["POST /api/auth/login"]}],
    security=[{"area": "Passwords", "decision": "Use bcrypt", "reason": "Security"}],
    deployment=[{"environment": "Production", "services": ["Docker"], "reason": "Deployment"}]
)


context = ImplementationContext(
    project_title="Yibe Market",
    project_summary="An online supermarket where customers can browse products, add them to a cart, place orders with online payment, and receive notifications. Administrators can manage products and orders.",
    problem="Customers need a convenient way to shop for supermarket products online.",
    target_users=["Customer", "Administrator"],
    functional_requirements=[
        "FR-001: Browse Product Catalog - Customers can view products.",
        "FR-002: Add to Cart and Place Order - Customers can add to cart and order.",
        "FR-003: Online Payment Processing - System processes payments via Stripe.",
        "FR-004: Order Notifications - System sends notifications.",
        "FR-005: Customer Authentication - Customers can register and login.",
        "FR-006: Administrator Authentication - Admins can login.",
        "FR-007: Manage Products (Admin) - Admins can manage products.",
        "FR-008: Manage Orders (Admin) - Admins can manage orders."
    ],
    non_functional_requirements=[
        "NFR-001: Security - Protect user credentials with bcrypt.",
        "NFR-002: Performance - Fast response times.",
        "NFR-003: Scalability & Deployment - Deployable on cloud.",
        "NFR-004: Usability - Intuitive UI."
    ],
    architecture_summary="Three-tier monolithic architecture with React TypeScript frontend, Node.js/Express REST API, PostgreSQL database. Dockerized and deployed to AWS ECS Fargate.",
    technology_stack=["React", "Node.js/Express", "PostgreSQL", "Stripe", "Docker"],
    data_model=["User: id, email, password_hash, role", "Product: id, name, price"],
    api_contract=["POST /api/auth/login", "GET /api/products", "POST /api/orders"],
    security_requirements=["Use bcrypt for passwords", "Enforce HTTPS", "JWT authentication"],
    implementation_phases=[{"phase": 1, "name": "Setup", "objective": "Initialize project", "tasks": ["Create repo", "Setup Docker"], "deliverables": ["Working dev environment"]}],
    agent_rules=[{"category": "Security", "rule": "Never hardcode secrets"}],
    definition_of_done=["All requirements implemented", "Tests passing"]
)


def main():

    print("=" * 60)
    print("TEST 1: Create real artifact")
    print("=" * 60)

    validation = validate_context(
        project,
        requirements,
        architecture,
        context,
    )

    artifact = create_artifact(
        context=context,
        validation=validation,
    )

    print(f"\nProject ID:\n{artifact.project_id}")
    print(f"\nProject Name:\n{artifact.project_name}")
    print(f"\nValidation:\n{artifact.valid}")
    print(f"\nScore:\n{artifact.validation_score}")
    print(f"\nMarkdown length:\n{len(artifact.markdown)}")

    print("\n" + "=" * 60)
    print("TEST 2: Reject invalid artifact")
    print("=" * 60)

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

    broken_validation = validate_context(
        project,
        requirements,
        architecture,
        broken_context,
    )

    try:
        create_artifact(
            context=broken_context,
            validation=broken_validation,
        )
        print("ERROR: Should have raised ValueError!")
    except ValueError as error:
        print(f"Correctly rejected invalid artifact: {error}")


main()
