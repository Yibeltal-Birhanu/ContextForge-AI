import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.engines.assembly import assemble_markdown
from app.engines.validation import validate_context

from app.models.project import ProjectState
from app.models.requirements import RequirementsDocument
from app.models.architecture import ArchitectureDocument
from app.models.context import ImplementationContext
from app.models.validation import ContextValidationResult


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
    technology_stack=[
        "React with TypeScript - Component-based UI",
        "Redux Toolkit - State management",
        "Node.js/Express - Backend framework",
        "PostgreSQL - Relational database",
        "JWT + bcryptjs - Authentication",
        "Stripe API - Payment processing",
        "SendGrid/Twilio - Notifications",
        "Docker - Containerization",
        "AWS ECS Fargate - Cloud deployment"
    ],
    data_model=[
        "User: id, email, password_hash, role, first_name, last_name",
        "Product: id, name, description, price_cents, sku, stock_quantity, image_url",
        "Cart: id, user_id",
        "CartItem: id, cart_id, product_id, quantity",
        "Order: id, user_id, status, total_amount_cents",
        "OrderItem: id, order_id, product_id, quantity, unit_price_cents",
        "Payment: id, order_id, amount_cents, provider, status",
        "Notification: id, user_id, type, channel, status"
    ],
    api_contract=[
        "POST /api/auth/register - Register new user",
        "POST /api/auth/login - Login and get JWT",
        "POST /api/auth/logout - Logout",
        "GET /api/products - List products",
        "GET /api/products/:id - Product details",
        "POST /api/products (admin) - Create product",
        "PUT /api/products/:id (admin) - Update product",
        "DELETE /api/products/:id (admin) - Delete product",
        "GET /api/cart - Get cart",
        "POST /api/cart/items - Add to cart",
        "PUT /api/cart/items/:id - Update cart item",
        "DELETE /api/cart/items/:id - Remove from cart",
        "POST /api/orders - Create order",
        "GET /api/orders - Order history",
        "GET /api/orders/:id - Order details",
        "GET /api/admin/orders (admin) - All orders",
        "PATCH /api/admin/orders/:id/status (admin) - Update status",
        "POST /api/payments/create-intent - Stripe payment",
        "POST /api/payments/webhook - Stripe webhook",
        "POST /api/notifications - Send notification"
    ],
    security_requirements=[
        "Password Storage: Use bcryptjs with cost factor 12",
        "Transport Security: Enforce HTTPS/TLS for all communication",
        "Authentication: Short-lived JWT (15 min) with refresh token",
        "Input Validation: express-validator on all requests",
        "Rate Limiting: Rate limits on auth endpoints",
        "Payment Data: Never store raw card details, use Stripe Payment Intents"
    ],
    implementation_phases=[
        {
            "phase": 1,
            "name": "Project Setup and Infrastructure",
            "objective": "Establish repository, CI/CD, Docker, and authentication.",
            "tasks": ["Initialize monorepo", "Set up Docker Compose", "Configure GitHub Actions", "Implement User model", "Create JWT auth middleware", "Configure environment variables"],
            "deliverables": ["Running Docker environment", "Authenticated API endpoints", "Frontend skeleton"]
        },
        {
            "phase": 2,
            "name": "Product Catalog and Cart",
            "objective": "Enable product browsing and cart persistence.",
            "tasks": ["Implement Product model and API", "Build product UI pages", "Implement Cart model and API", "Build cart UI", "Connect frontend to backend", "Write tests"],
            "deliverables": ["Product catalog browsable", "Functional cart", "API test coverage"]
        },
        {
            "phase": 3,
            "name": "Admin Features",
            "objective": "Provide admin product and order management.",
            "tasks": ["Implement admin role middleware", "Build admin product CRUD", "Implement admin order endpoints", "Create admin dashboard", "Wire notification placeholders", "Write admin tests"],
            "deliverables": ["Admin product management", "Admin order management", "Notification placeholder"]
        },
        {
            "phase": 4,
            "name": "Payment and Notifications",
            "objective": "Integrate Stripe payments and SendGrid/Twilio notifications.",
            "tasks": ["Configure Stripe API", "Implement checkout flow", "Handle Stripe webhook", "Develop notification service", "Wire notifications", "End-to-end testing"],
            "deliverables": ["Payment processing", "Order notifications", "Checkout validated"]
        },
        {
            "phase": 5,
            "name": "Testing and Deployment",
            "objective": "Ensure quality and deploy to cloud.",
            "tasks": ["Load testing", "Optimize queries", "Implement rate limiting", "Build production Docker images", "Deploy to ECS Fargate", "Usability testing", "Documentation"],
            "deliverables": ["Performance benchmarks met", "Cloud deployment", "All criteria met"]
        }
    ],
    agent_rules=[
        {"category": "Coding Standards", "rule": "Use ESLint with Airbnb + TypeScript rules; Prettier for formatting."},
        {"category": "Git Workflow", "rule": "Feature branches off develop; PRs require approval and passing CI."},
        {"category": "API Design", "rule": "Follow REST conventions; return JSON payloads."},
        {"category": "Security", "rule": "Never log passwords or payment details; enforce HTTPS; use helmet.js; validate all inputs."},
        {"category": "Testing", "rule": "Write unit tests for services; integration tests for APIs; aim for >80% coverage."},
        {"category": "Deployment", "rule": "Deploy via Docker to cloud; use rolling updates; rollback on health check failures."}
    ],
    definition_of_done=[
        "All functional requirements implemented and verified via tests",
        "Non-functional requirements satisfied or justified",
        "Code passes linting, type checking, and minimum test coverage",
        "Docker images build and run in staging and production",
        "Application deployed with monitoring and logging",
        "Documentation updated and accessible",
        "No critical security vulnerabilities"
    ]
)


def main():

    print("=" * 60)
    print("TEST 1: Assemble real context")
    print("=" * 60)

    validation = validate_context(
        project,
        requirements,
        architecture,
        context,
    )

    print(f"Validation: valid={validation.valid}, score={validation.score}")

    markdown = assemble_markdown(
        context=context,
        validation=validation,
    )

    print(f"\nMarkdown generated: {len(markdown)} characters")

    with open(
        "test_context.md",
        "w",
        encoding="utf-8",
    ) as file:
        file.write(markdown)

    print("Saved to test_context.md")

    print("\n" + "=" * 60)
    print("TEST 2: Reject invalid context")
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
        assemble_markdown(
            context=broken_context,
            validation=broken_validation,
        )
        print("ERROR: Should have raised ValueError!")
    except ValueError as error:
        print(f"Correctly rejected invalid context: {error}")


main()
