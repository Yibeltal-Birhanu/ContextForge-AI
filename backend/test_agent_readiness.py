import json
import os
os.environ.setdefault("OPENROUTER_API_KEY", "test")
os.environ.setdefault("OPENROUTER_MODEL", "test")

from app.models.project import ProjectState
from app.models.requirements import RequirementsDocument
from app.models.architecture import ArchitectureDocument
from app.models.context import ImplementationContext
from app.engines.agent_readiness import check_agent_readiness
from app.services.context_quality import assess_context_quality, generate_quality_summary


# ============================================================
# Real project data from previous tasks
# ============================================================

project = ProjectState(
    name="Yibe Market",
    description="An online supermarket where customers can browse products and place orders.",
    problem="Customers need a convenient way to shop for supermarket products online.",
    target_users=["Customers", "Administrators"],
    core_features=[
        "Browse products",
        "Add products to cart",
        "Place orders",
        "Online payment",
        "Order notifications",
        "Manage products",
        "Manage orders",
    ],
    platform="Both web and mobile",
    technologies=[],
    database=None,
    authentication="Customer accounts and admin accounts",
    integrations=["Online payment", "Order notifications"],
    constraints=["Limited budget"],
    deployment="Cloud hosting",
)

requirements = RequirementsDocument(
    functional_requirements=[
        {
            "id": "FR-001",
            "title": "Browse Product Catalog",
            "description": "Customers can browse available supermarket products.",
            "priority": "MUST_HAVE",
            "actors": ["Customer"],
            "acceptance_criteria": [
                {"description": "Customer can view available products."},
                {"description": "Customer can view product details."},
                {"description": "Product has name, price, image, category."},
                {"description": "Out-of-stock products are clearly indicated."},
            ],
        },
        {
            "id": "FR-002",
            "title": "Add to Cart and Place Order",
            "description": "Customers can add products to cart and place orders.",
            "priority": "MUST_HAVE",
            "actors": ["Customer"],
            "acceptance_criteria": [
                {"description": "Customer can add items to cart."},
                {"description": "Customer can view and modify cart."},
                {"description": "Customer can place an order from the cart."},
                {"description": "Order confirmation is displayed after placement."},
            ],
        },
        {
            "id": "FR-003",
            "title": "Online Payment Processing",
            "description": "Customers can pay for orders online.",
            "priority": "MUST_HAVE",
            "actors": ["Customer"],
            "acceptance_criteria": [
                {"description": "Customer can select a payment method."},
                {"description": "Payment status is recorded."},
                {"description": "Failed payments do not create completed orders."},
                {"description": "Successful payment updates order status."},
            ],
        },
        {
            "id": "FR-004",
            "title": "Order Notifications",
            "description": "Users receive notifications about order status changes.",
            "priority": "SHOULD_HAVE",
            "actors": ["Customer", "Administrator"],
            "acceptance_criteria": [
                {"description": "Customer receives notification when order status changes."},
                {"description": "Administrator receives notification for new orders."},
            ],
        },
        {
            "id": "FR-005",
            "title": "Customer Authentication",
            "description": "Customers can create accounts and log in.",
            "priority": "MUST_HAVE",
            "actors": ["Customer"],
            "acceptance_criteria": [
                {"description": "Customer can register with email/password."},
                {"description": "Customer can log in and log out."},
                {"description": "Session is maintained across requests."},
            ],
        },
        {
            "id": "FR-006",
            "title": "Administrator Authentication",
            "description": "Administrators can access the admin dashboard.",
            "priority": "MUST_HAVE",
            "actors": ["Administrator"],
            "acceptance_criteria": [
                {"description": "Admin can log in with admin credentials."},
                {"description": "Admin has elevated permissions."},
            ],
        },
        {
            "id": "FR-007",
            "title": "Manage Products (Admin)",
            "description": "Administrators can manage the product catalog.",
            "priority": "MUST_HAVE",
            "actors": ["Administrator"],
            "acceptance_criteria": [
                {"description": "Admin can add, edit, and delete products."},
                {"description": "Admin can manage product categories."},
                {"description": "Changes are reflected immediately for customers."},
            ],
        },
        {
            "id": "FR-008",
            "title": "Manage Orders (Admin)",
            "description": "Administrators can view and manage customer orders.",
            "priority": "MUST_HAVE",
            "actors": ["Administrator"],
            "acceptance_criteria": [
                {"description": "Admin can view all orders."},
                {"description": "Admin can update order status."},
                {"description": "Admin can filter and search orders."},
            ],
        },
    ],
    non_functional_requirements=[
        {
            "id": "NFR-001",
            "title": "Security",
            "description": "System must be secure against common attacks.",
            "priority": "MUST_HAVE",
            "actors": [],
            "acceptance_criteria": [
                {"description": "Passwords are hashed with bcrypt."},
                {"description": "API endpoints are protected with JWT."},
                {"description": "Input validation prevents injection."},
            ],
        },
        {
            "id": "NFR-002",
            "title": "Performance",
            "description": "System should load within acceptable times.",
            "priority": "SHOULD_HAVE",
            "actors": [],
            "acceptance_criteria": [
                {"description": "Product catalog loads within 2 seconds."},
                {"description": "API responses within 500ms."},
            ],
        },
        {
            "id": "NFR-003",
            "title": "Scalability and Deployment",
            "description": "System must be deployable and scalable.",
            "priority": "MUST_HAVE",
            "actors": [],
            "acceptance_criteria": [
                {"description": "System can be containerized with Docker."},
                {"description": "System can be deployed to cloud hosting."},
            ],
        },
        {
            "id": "NFR-004",
            "title": "Usability",
            "description": "System must be user-friendly.",
            "priority": "SHOULD_HAVE",
            "actors": [],
            "acceptance_criteria": [
                {"description": "Non-technical users can navigate the store."},
                {"description": "Admin dashboard is intuitive."},
            ],
        },
    ],
)

architecture = ArchitectureDocument(
    system_architecture=(
        "Three-tier monolithic architecture with separate frontend, "
        "backend API, and database layers. The frontend is split into "
        "a customer-facing web application and an admin dashboard. "
        "The backend provides a RESTful API. The database stores all "
        "persistent data."
    ),
    components=[
        {
            "name": "Customer Web Application",
            "responsibility": "Product browsing, cart management, checkout, order tracking.",
            "technologies": ["React", "TypeScript", "Tailwind CSS"],
        },
        {
            "name": "Admin Dashboard",
            "responsibility": "Product management, order management, user oversight.",
            "technologies": ["React", "TypeScript"],
        },
        {
            "name": "Backend API Service",
            "responsibility": "Business logic, authentication, data validation, payment processing.",
            "technologies": ["Node.js", "Express", "TypeScript"],
        },
        {
            "name": "Database",
            "responsibility": "Persistent storage for users, products, orders, payments.",
            "technologies": ["PostgreSQL"],
        },
    ],
    technology_stack=[
        {"category": "Frontend", "technology": "React", "reason": "Modern component-based UI library with strong ecosystem."},
        {"category": "Language", "technology": "TypeScript", "reason": "Type safety for both frontend and backend."},
        {"category": "CSS", "technology": "Tailwind CSS", "reason": "Rapid UI development with utility classes."},
        {"category": "Backend", "technology": "Node.js", "reason": "JavaScript runtime for full-stack consistency."},
        {"category": "Framework", "technology": "Express", "reason": "Minimal and flexible Node.js web framework."},
        {"category": "Database", "technology": "PostgreSQL", "reason": "Relational database suitable for structured e-commerce data."},
        {"category": "Auth", "technology": "JWT", "reason": "Stateless token-based authentication."},
        {"category": "Password Hashing", "technology": "bcrypt", "reason": "Industry-standard password hashing."},
        {"category": "Payments", "technology": "Stripe", "reason": "PCI-compliant payment processing API."},
        {"category": "Notifications", "technology": "SendGrid", "reason": "Email notification service."},
        {"category": "Containerization", "technology": "Docker", "reason": "Consistent deployment environments."},
        {"category": "Deployment", "technology": "AWS ECS Fargate", "reason": "Managed container service for scalability."},
    ],
    data_architecture=[
        {"name": "User", "purpose": "Store user accounts (customers and admins)", "important_fields": ["id", "email", "password_hash", "role", "created_at"]},
        {"name": "Product", "purpose": "Product catalog entries", "important_fields": ["id", "name", "description", "price", "image_url", "category_id", "stock"]},
        {"name": "Category", "purpose": "Product categories for browsing", "important_fields": ["id", "name", "description"]},
        {"name": "Cart", "purpose": "Shopping cart per user", "important_fields": ["id", "user_id", "created_at"]},
        {"name": "CartItem", "purpose": "Individual items in a cart", "important_fields": ["id", "cart_id", "product_id", "quantity"]},
        {"name": "Order", "purpose": "Customer orders", "important_fields": ["id", "user_id", "status", "total", "created_at"]},
        {"name": "OrderItem", "purpose": "Items in a placed order", "important_fields": ["id", "order_id", "product_id", "quantity", "price_at_purchase"]},
        {"name": "Payment", "purpose": "Payment records linked to orders", "important_fields": ["id", "order_id", "amount", "method", "status", "stripe_id"]},
    ],
    api_design=[
        {"name": "Auth", "purpose": "User registration and authentication", "endpoints": ["POST /auth/register", "POST /auth/login", "GET /auth/me"]},
        {"name": "Products", "purpose": "Product catalog CRUD", "endpoints": ["GET /products", "GET /products/:id", "POST /products", "PUT /products/:id", "DELETE /products/:id"]},
        {"name": "Categories", "purpose": "Category management", "endpoints": ["GET /categories", "POST /categories", "PUT /categories/:id", "DELETE /categories/:id"]},
        {"name": "Cart", "purpose": "Shopping cart operations", "endpoints": ["GET /cart", "POST /cart/items", "PUT /cart/items/:id", "DELETE /cart/items/:id"]},
        {"name": "Orders", "purpose": "Order placement and management", "endpoints": ["POST /orders", "GET /orders", "GET /orders/:id", "PUT /orders/:id/status"]},
        {"name": "Payments", "purpose": "Payment processing", "endpoints": ["POST /payments/create-intent", "POST /payments/confirm", "GET /payments/:id"]},
    ],
    security=[
        {"area": "Authentication", "decision": "JWT tokens with 24h expiry and refresh token support", "reason": "Stateless auth suitable for REST API"},
        {"area": "Password Storage", "decision": "bcrypt hashing with salt rounds 12", "reason": "Industry standard for password security"},
        {"area": "API Security", "decision": "Rate limiting, CORS, input validation", "reason": "Protection against abuse and injection"},
        {"area": "Payment Security", "decision": "PCI compliance via Stripe, no raw card storage", "reason": "Avoid PCI compliance burden"},
        {"area": "Data Security", "decision": "Environment variables for secrets, encrypted connections", "reason": "Protect sensitive configuration"},
        {"area": "Admin Access", "decision": "Role-based access control, admin-only endpoints", "reason": "Separate admin and customer permissions"},
    ],
    deployment=[
        {"environment": "Development", "services": ["Docker Compose", "PostgreSQL", "Node.js API", "React Dev Server"], "reason": "Local development setup"},
        {"environment": "Production", "services": ["AWS ECS Fargate", "RDS PostgreSQL", "CloudFront CDN", "S3 Static Assets"], "reason": "Scalable managed cloud deployment"},
    ],
)

context = ImplementationContext(
    project_title="Yibe Market",
    project_summary=(
        "Yibe Market is an online supermarket platform where customers "
        "can browse products, add them to a shopping cart, place orders, "
        "make online payments, and receive order notifications. "
        "Administrators can manage products and orders through a dedicated dashboard."
    ),
    problem="Customers need a convenient way to shop for supermarket products online without visiting a physical store.",
    target_users=["Customer", "Administrator"],
    functional_requirements=[
        "FR-001: Browse Product Catalog - Customers can view products with name, price, image, category. Out-of-stock products are clearly indicated.",
        "FR-002: Add to Cart and Place Order - Customers can add items to cart, modify quantities, and place orders.",
        "FR-003: Online Payment Processing - Customers can pay via Stripe. Payment status is recorded. Failed payments do not complete orders.",
        "FR-004: Order Notifications - Customers and admins receive email notifications on order status changes.",
        "FR-005: Customer Authentication - Registration, login, logout with JWT session management.",
        "FR-006: Administrator Authentication - Admin login with elevated permissions.",
        "FR-007: Manage Products (Admin) - CRUD operations on product catalog and categories.",
        "FR-008: Manage Orders (Admin) - View, filter, and update order status.",
    ],
    non_functional_requirements=[
        "NFR-001: Security - bcrypt password hashing, JWT auth, input validation, rate limiting.",
        "NFR-002: Performance - Product catalog loads within 2s, API responses within 500ms.",
        "NFR-003: Scalability - Docker containerization, cloud deployment on AWS ECS Fargate.",
        "NFR-004: Usability - Intuitive navigation for customers and admin dashboard.",
    ],
    architecture_summary=(
        "Three-tier monolithic architecture: React frontend for customers and admins, "
        "Node.js/Express RESTful API backend, PostgreSQL database. "
        "Stateless JWT authentication, Stripe payment integration, "
        "SendGrid email notifications, Docker containerization, "
        "AWS ECS Fargate deployment."
    ),
    technology_stack=[
        "React", "TypeScript", "Tailwind CSS", "Node.js", "Express",
        "PostgreSQL", "JWT", "bcrypt", "Stripe", "SendGrid",
        "Docker", "AWS ECS Fargate",
    ],
    data_model=[
        "User: id, email, password_hash, role, created_at",
        "Product: id, name, description, price, image_url, category_id, stock",
        "Category: id, name, description",
        "Cart: id, user_id, created_at",
        "CartItem: id, cart_id, product_id, quantity",
        "Order: id, user_id, status, total, created_at",
        "OrderItem: id, order_id, product_id, quantity, price_at_purchase",
        "Payment: id, order_id, amount, method, status, stripe_id",
    ],
    api_contract=[
        "POST /auth/register - Register new user",
        "POST /auth/login - Authenticate user",
        "GET /auth/me - Get current user",
        "GET /products - List products",
        "GET /products/:id - Get product detail",
        "POST /products - Create product (admin)",
        "PUT /products/:id - Update product (admin)",
        "DELETE /products/:id - Delete product (admin)",
        "GET /categories - List categories",
        "POST /categories - Create category (admin)",
        "GET /cart - Get user cart",
        "POST /cart/items - Add item to cart",
        "PUT /cart/items/:id - Update cart item",
        "DELETE /cart/items/:id - Remove cart item",
        "POST /orders - Place order",
        "GET /orders - List user orders",
        "GET /orders/:id - Get order detail",
        "PUT /orders/:id/status - Update order status (admin)",
        "POST /payments/create-intent - Create Stripe payment intent",
        "POST /payments/confirm - Confirm payment",
    ],
    security_requirements=[
        "Passwords hashed with bcrypt (salt rounds 12)",
        "JWT tokens with 24h expiry for stateless authentication",
        "All API endpoints validated for input sanitization",
        "Rate limiting on authentication endpoints",
        "CORS configured for frontend origin only",
        "Stripe handles PCI compliance - no raw card data stored",
        "Admin endpoints require admin role verification",
        "Environment variables used for all secrets and API keys",
    ],
    implementation_phases=[
        {
            "phase": 1,
            "name": "Project Foundation",
            "objective": "Set up project structure, database, and basic auth.",
            "tasks": [
                "Initialize Node.js/Express project with TypeScript",
                "Set up PostgreSQL database and migrations",
                "Implement User model and auth endpoints",
                "Configure Docker for development",
            ],
            "deliverables": [
                "Working Express server",
                "Database migrations running",
                "Register and login endpoints working",
                "Docker Compose setup",
            ],
        },
        {
            "phase": 2,
            "name": "Product Catalog",
            "objective": "Build product browsing and admin management.",
            "tasks": [
                "Create Product and Category models",
                "Implement product CRUD API endpoints",
                "Add category management endpoints",
                "Seed database with sample products",
            ],
            "deliverables": [
                "Product API endpoints",
                "Category management",
                "Sample data seeded",
            ],
        },
        {
            "phase": 3,
            "name": "Shopping Cart and Orders",
            "objective": "Implement cart management and order placement.",
            "tasks": [
                "Create Cart and CartItem models",
                "Implement cart API endpoints",
                "Create Order and OrderItem models",
                "Implement order placement flow",
            ],
            "deliverables": [
                "Cart CRUD operations",
                "Order placement working",
                "Order history available",
            ],
        },
        {
            "phase": 4,
            "name": "Payments and Notifications",
            "objective": "Integrate Stripe payments and email notifications.",
            "tasks": [
                "Integrate Stripe payment intents",
                "Implement payment confirmation flow",
                "Set up SendGrid email notifications",
                "Send order confirmation emails",
            ],
            "deliverables": [
                "Stripe payment working",
                "Email notifications sending",
                "Payment status recorded",
            ],
        },
        {
            "phase": 5,
            "name": "Frontend and Deployment",
            "objective": "Build React frontend and deploy to production.",
            "tasks": [
                "Build customer-facing React frontend",
                "Build admin dashboard",
                "Configure production Docker setup",
                "Deploy to AWS ECS Fargate",
            ],
            "deliverables": [
                "Customer web app working",
                "Admin dashboard working",
                "Production deployment live",
            ],
        },
    ],
    agent_rules=[
        {"category": "Architecture", "rule": "Keep the backend as a modular monolith. Do not introduce microservices."},
        {"category": "Database", "rule": "Use PostgreSQL as the primary relational database. Run migrations for schema changes."},
        {"category": "Security", "rule": "Never hardcode secrets or API keys. Use environment variables."},
        {"category": "API Design", "rule": "Follow RESTful conventions. Use proper HTTP status codes and error responses."},
        {"category": "Testing", "rule": "Write integration tests for all API endpoints. Test auth, CRUD, and error flows."},
        {"category": "Development", "rule": "Implement and verify each phase before moving to the next."},
    ],
    definition_of_done=[
        "All functional requirements (FR-001 through FR-008) implemented and verified",
        "All non-functional requirements met (security, performance, scalability, usability)",
        "All API endpoints tested with integration tests",
        "Authentication flow works end-to-end (register, login, logout, JWT refresh)",
        "Payment flow works end-to-end (create intent, confirm, record)",
        "Admin dashboard allows full product and order management",
        "System deployed and accessible via cloud hosting URL",
    ],
)


# ============================================================
# Test 1: Agent Readiness Check
# ============================================================

print("=" * 60)
print("TEST 1: Agent Readiness Check")
print("=" * 60)

result = check_agent_readiness(project, requirements, architecture, context)

print(f"\nReady: {result.ready}")
print(f"Score: {result.score}/100")
print(f"\nCheck Scores:")
print(f"  Requirements Coverage:   {result.checks.requirements_coverage}%")
print(f"  Architecture Consistency: {result.checks.architecture_consistency}%")
print(f"  Technology Consistency:  {result.checks.technology_consistency}%")
print(f"  API Coverage:            {result.checks.api_coverage}%")
print(f"  Data Model Coverage:     {result.checks.data_model_coverage}%")
print(f"  Security Coverage:       {result.checks.security_coverage}%")
print(f"  Implementation Coverage: {result.checks.implementation_coverage}%")
print(f"  Agent Rules Quality:     {result.checks.agent_rules_quality}%")
print(f"  Definition of Done:      {result.checks.definition_of_done}%")

if result.errors:
    print(f"\nErrors ({len(result.errors)}):")
    for e in result.errors:
        print(f"  - {e}")

if result.warnings:
    print(f"\nWarnings ({len(result.warnings)}):")
    for w in result.warnings:
        print(f"  - [{w.category}] {w.message}")

if result.assumptions:
    print(f"\nAssumptions ({len(result.assumptions)}):")
    for a in result.assumptions:
        icon = "INFO" if a.severity == "info" else "WARN" if a.severity == "warning" else "CRIT"
        print(f"  - [{icon}] [{a.area}] {a.assumption}")


# ============================================================
# Test 2: Full Quality Assessment
# ============================================================

print("\n" + "=" * 60)
print("TEST 2: Full Quality Assessment")
print("=" * 60)

quality = assess_context_quality(
    project, requirements, architecture, context,
)

print(f"\nOverall Ready: {quality['overall_ready']}")
print(f"Overall Score: {quality['overall_score']}/100")
print(f"Validation Score: {quality['validation'].score}/100")
print(f"Readiness Score: {quality['readiness'].score}/100")


# ============================================================
# Test 3: Quality Summary
# ============================================================

print("\n" + "=" * 60)
print("TEST 3: Quality Summary")
print("=" * 60)

summary = generate_quality_summary(quality)
print(summary)


# ============================================================
# Test 4: Intentionally degraded context
# ============================================================

print("\n" + "=" * 60)
print("TEST 4: Degraded Context (fewer requirements in context)")
print("=" * 60)

degraded_context = ImplementationContext(
    project_title="Yibe Market",
    project_summary="An online supermarket.",
    problem="Shopping convenience.",
    target_users=["Customer"],
    functional_requirements=[
        "Browse products",
        "Place orders",
    ],
    non_functional_requirements=[],
    architecture_summary="Monolithic web application.",
    technology_stack=["React", "Node.js"],
    data_model=["Product"],
    api_contract=["GET /products"],
    security_requirements=[],
    implementation_phases=[],
    agent_rules=[],
    definition_of_done=[],
)

degraded_result = check_agent_readiness(
    project, requirements, architecture, degraded_context,
)

print(f"\nReady: {degraded_result.ready}")
print(f"Score: {degraded_result.score}/100")
print(f"\nCheck Scores:")
print(f"  Requirements Coverage:   {degraded_result.checks.requirements_coverage}%")
print(f"  Architecture Consistency: {degraded_result.checks.architecture_consistency}%")
print(f"  Technology Consistency:  {degraded_result.checks.technology_consistency}%")
print(f"  API Coverage:            {degraded_result.checks.api_coverage}%")
print(f"  Data Model Coverage:     {degraded_result.checks.data_model_coverage}%")
print(f"  Security Coverage:       {degraded_result.checks.security_coverage}%")
print(f"  Implementation Coverage: {degraded_result.checks.implementation_coverage}%")
print(f"  Agent Rules Quality:     {degraded_result.checks.agent_rules_quality}%")
print(f"  Definition of Done:      {degraded_result.checks.definition_of_done}%")

if degraded_result.warnings:
    print(f"\nWarnings ({len(degraded_result.warnings)}):")
    for w in degraded_result.warnings:
        print(f"  - [{w.category}] {w.message}")

if degraded_result.assumptions:
    print(f"\nAssumptions ({len(degraded_result.assumptions)}):")
    for a in degraded_result.assumptions:
        icon = "INFO" if a.severity == "info" else "WARN" if a.severity == "warning" else "CRIT"
        print(f"  - [{icon}] [{a.area}] {a.assumption}")


print("\n" + "=" * 60)
print("ALL TESTS COMPLETE")
print("=" * 60)
