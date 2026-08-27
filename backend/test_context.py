import asyncio
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.engines.context import generate_context

from app.models.project import ProjectState
from app.models.requirements import RequirementsDocument
from app.models.architecture import ArchitectureDocument


project = ProjectState(
    name="Yibe Market",
    description="An online supermarket where customers can browse products and place orders.",
    problem="Customers need a convenient way to shop for supermarket products online.",
    target_users=[
        "Customers",
        "Administrators"
    ],
    core_features=[
        "Browse products",
        "Add products to cart",
        "Place orders",
        "Online payment",
        "Order notifications",
        "Manage products",
        "Manage orders"
    ],
    platform="Both web and mobile",
    technologies=[],
    database=None,
    authentication="Customer accounts and admin accounts",
    integrations=[
        "Online payment",
        "Order notifications"
    ],
    constraints=[
        "Limited budget"
    ],
    deployment="Cloud hosting"
)


requirements = RequirementsDocument(
    functional_requirements=[
        {
            "id": "FR-001",
            "title": "Browse Product Catalog",
            "description": "Customers can view a list of available products with essential details such as name, price, and image.",
            "priority": "MUST_HAVE",
            "actors": ["Customer"],
            "acceptance_criteria": [
                {"description": "When a customer navigates to the product listing page, the system displays a list of products each showing name, price, and thumbnail image."},
                {"description": "When a customer selects a product, the system displays a product detail page showing name, description, price, availability, and larger images."}
            ]
        },
        {
            "id": "FR-002",
            "title": "Add to Cart and Place Order",
            "description": "Customers can add products to a shopping cart and submit an order with payment.",
            "priority": "MUST_HAVE",
            "actors": ["Customer"],
            "acceptance_criteria": [
                {"description": "When a customer adds a product to the cart, the cart quantity updates accordingly and the item persists across page navigations."},
                {"description": "When a customer proceeds to checkout, the system presents a summary of cart items, total price, and prompts for payment information."},
                {"description": "When the customer submits valid payment details, the system creates an order record, marks the order as 'Pending Payment', and clears the cart."}
            ]
        },
        {
            "id": "FR-003",
            "title": "Online Payment Processing",
            "description": "The system integrates with an online payment gateway to process payments for placed orders.",
            "priority": "MUST_HAVE",
            "actors": ["Customer"],
            "acceptance_criteria": [
                {"description": "When a customer enters payment information and confirms payment, the system forwards the payment request to the integrated payment gateway."},
                {"description": "Upon receiving a successful payment response from the gateway, the system updates the order status to 'Paid'."},
                {"description": "Upon receiving a failed or declined payment response, the system retains the order status as 'Pending Payment' and notifies the customer of the failure."}
            ]
        },
        {
            "id": "FR-004",
            "title": "Order Notifications",
            "description": "The system sends notifications to customers and administrators upon order creation and status changes.",
            "priority": "SHOULD_HAVE",
            "actors": ["Customer", "Administrator"],
            "acceptance_criteria": [
                {"description": "When an order is successfully created, the system sends an order confirmation notification to the customer."},
                {"description": "When an order status changes, the system sends a status update notification to the customer."},
                {"description": "When a new order is placed, the system sends a notification to the administrator indicating a new order requires processing."}
            ]
        },
        {
            "id": "FR-005",
            "title": "Customer Authentication",
            "description": "Customers can register, log in, and log out of their accounts.",
            "priority": "MUST_HAVE",
            "actors": ["Customer"],
            "acceptance_criteria": [
                {"description": "When a customer provides valid registration details, the system creates an account and allows login."},
                {"description": "When a customer provides correct login credentials, the system authenticates and grants access."},
                {"description": "When a customer logs out, the system invalidates the session."}
            ]
        },
        {
            "id": "FR-006",
            "title": "Administrator Authentication",
            "description": "Administrators can log in to manage the system.",
            "priority": "MUST_HAVE",
            "actors": ["Administrator"],
            "acceptance_criteria": [
                {"description": "When an administrator provides valid admin credentials, the system authenticates and grants access to admin functionality."},
                {"description": "When an administrator logs out, the system ends the admin session."}
            ]
        },
        {
            "id": "FR-007",
            "title": "Manage Products (Admin)",
            "description": "Administrators can create, read, update, and delete product information.",
            "priority": "MUST_HAVE",
            "actors": ["Administrator"],
            "acceptance_criteria": [
                {"description": "When an administrator submits a valid product form, the system creates the product."},
                {"description": "When an administrator edits a product and saves, the system updates the product."},
                {"description": "When an administrator deletes a product, the system removes it from the catalog."}
            ]
        },
        {
            "id": "FR-008",
            "title": "Manage Orders (Admin)",
            "description": "Administrators can view orders and update their status.",
            "priority": "MUST_HAVE",
            "actors": ["Administrator"],
            "acceptance_criteria": [
                {"description": "When an administrator accesses the order management page, the system lists all orders."},
                {"description": "When an administrator changes an order status, the system persists the new status and triggers a notification."},
                {"description": "When an administrator views an order detail, the system shows line items, quantities, prices, and customer shipping information."}
            ]
        }
    ],
    non_functional_requirements=[
        {
            "id": "NFR-001",
            "title": "Security",
            "description": "The system must protect user credentials and personal data using industry-standard security practices.",
            "priority": "MUST_HAVE",
            "actors": [],
            "acceptance_criteria": [
                {"description": "Passwords are stored using a strong, adaptive hashing algorithm."},
                {"description": "All authentication and payment-related communications occur over HTTPS/TLS."}
            ]
        },
        {
            "id": "NFR-002",
            "title": "Performance",
            "description": "The system should respond to user interactions within an acceptable time.",
            "priority": "SHOULD_HAVE",
            "actors": [],
            "acceptance_criteria": [
                {"description": "Page load times for product listing and detail pages are under 3 seconds."},
                {"description": "Checkout process completes within 5 seconds after payment gateway response."}
            ]
        },
        {
            "id": "NFR-003",
            "title": "Scalability & Deployment",
            "description": "The system shall be deployable on cloud hosting services.",
            "priority": "MUST_HAVE",
            "actors": [],
            "acceptance_criteria": [
                {"description": "The application can be deployed to a cloud provider using containerization."},
                {"description": "The system supports horizontal scaling to handle increased load."}
            ]
        },
        {
            "id": "NFR-004",
            "title": "Usability",
            "description": "The user interface should be accessible and intuitive for both web and mobile users.",
            "priority": "SHOULD_HAVE",
            "actors": [],
            "acceptance_criteria": [
                {"description": "The layout adapts to different screen sizes (responsive design)."},
                {"description": "Key actions are reachable within three taps or clicks from the home page."}
            ]
        }
    ]
)


architecture = ArchitectureDocument(
    system_architecture="A three-tier monolithic architecture: a responsive single-page frontend (React) serves both web and mobile browsers, a Node.js/Express REST API handles business logic, authentication, order/cart management, payment gateway integration, and notification dispatch, and a PostgreSQL database stores all persistent data. The application is containerized with Docker and deployed to a cloud hosting provider supporting horizontal scaling.",
    components=[
        {"name": "Frontend Application", "responsibility": "Render UI for product browsing, cart management, checkout, user profile, and admin dashboard; communicate with backend via REST API; responsive design for web and mobile.", "technologies": ["React", "TypeScript", "Redux Toolkit", "React Router", "Axios", "Tailwind CSS"]},
        {"name": "Backend API Service", "responsibility": "Expose REST endpoints for authentication, product catalog, cart, orders, payments, and notifications; enforce role-based access control; integrate with Stripe for payment processing; send email/SMS notifications.", "technologies": ["Node.js", "Express.js", "JWT", "bcryptjs", "Sequelize", "Stripe", "SendGrid", "Twilio"]},
        {"name": "Database", "responsibility": "Persist users, products, carts, orders, order items, payments, and notifications; ensure ACID transactions.", "technologies": ["PostgreSQL"]}
    ],
    technology_stack=[
        {"category": "Frontend Framework", "technology": "React with TypeScript", "reason": "Component-based, maintainable UI; large ecosystem; responsive for web and mobile browsers."},
        {"category": "Backend Language/Framework", "technology": "Node.js/Express", "reason": "JavaScript/TypeScript reuse across stack; non-blocking I/O; mature middleware ecosystem."},
        {"category": "Database", "technology": "PostgreSQL", "reason": "Reliable, open-source relational DB with strong ACID guarantees; suitable for product catalog and orders."},
        {"category": "Authentication", "technology": "JWT + bcryptjs", "reason": "Stateless tokens for SPA; bcrypt for password hashing."},
        {"category": "Payment Integration", "technology": "Stripe API", "reason": "Industry-standard PCI-compliant gateway; supports multiple payment methods."},
        {"category": "Notifications", "technology": "SendGrid (email) & Twilio (SMS)", "reason": "Scalable, cost-effective SaaS providers for order confirmations."},
        {"category": "Containerization", "technology": "Docker", "reason": "Encapsulates services; enables consistent dev/test/prod environments."},
        {"category": "Deployment", "technology": "AWS ECS Fargate", "reason": "Managed container service; supports auto-scaling; fits limited budget."}
    ],
    data_architecture=[
        {"name": "User", "purpose": "Store customer and administrator accounts.", "important_fields": ["id", "email", "password_hash", "role", "first_name", "last_name", "phone_number"]},
        {"name": "Product", "purpose": "Catalog of items available for purchase.", "important_fields": ["id", "name", "description", "price_cents", "sku", "stock_quantity", "image_url", "is_active"]},
        {"name": "Cart", "purpose": "Temporary holder of items a customer intends to buy.", "important_fields": ["id", "user_id"]},
        {"name": "CartItem", "purpose": "Link between a cart and products with quantities.", "important_fields": ["id", "cart_id", "product_id", "quantity"]},
        {"name": "Order", "purpose": "Record of a completed purchase.", "important_fields": ["id", "user_id", "status", "total_amount_cents", "payment_intent_id"]},
        {"name": "OrderItem", "purpose": "Line items belonging to an order.", "important_fields": ["id", "order_id", "product_id", "quantity", "unit_price_cents"]},
        {"name": "Payment", "purpose": "Log of payment attempts and outcomes.", "important_fields": ["id", "order_id", "amount_cents", "provider", "status"]},
        {"name": "Notification", "purpose": "Track sent notifications for audit.", "important_fields": ["id", "user_id", "type", "channel", "status"]}
    ],
    api_design=[
        {"name": "Authentication", "purpose": "Register, login, logout, and token refresh.", "endpoints": ["POST /api/auth/register", "POST /api/auth/login", "POST /api/auth/logout", "POST /api/auth/refresh"]},
        {"name": "Products", "purpose": "Browse catalog and manage products (admin).", "endpoints": ["GET /api/products", "GET /api/products/:id", "POST /api/products (admin)", "PUT /api/products/:id (admin)", "DELETE /api/products/:id (admin)"]},
        {"name": "Cart", "purpose": "Manage shopping cart for logged-in customer.", "endpoints": ["GET /api/cart", "POST /api/cart/items", "PUT /api/cart/items/:itemId", "DELETE /api/cart/items/:itemId"]},
        {"name": "Orders", "purpose": "Create orders, retrieve history, admin management.", "endpoints": ["POST /api/orders", "GET /api/orders", "GET /api/orders/:id", "GET /api/admin/orders", "PATCH /api/admin/orders/:id/status"]},
        {"name": "Payments", "purpose": "Initiate payment with Stripe and handle webhooks.", "endpoints": ["POST /api/payments/create-intent", "POST /api/payments/webhook"]},
        {"name": "Notifications", "purpose": "Trigger notifications after order actions.", "endpoints": ["POST /api/notifications"]}
    ],
    security=[
        {"area": "Password Storage", "decision": "Use bcryptjs with cost factor 12.", "reason": "Strong adaptive hashing for password storage."},
        {"area": "Transport Security", "decision": "Enforce HTTPS/TLS for all communication.", "reason": "Prevents eavesdropping and MITM attacks."},
        {"area": "Authentication", "decision": "Issue short-lived JWT (15 min) with refresh token in HTTP-only cookie.", "reason": "Stateless yet secure; role-based access control."},
        {"area": "Input Validation", "decision": "Use express-validator middleware on all requests.", "reason": "Defends against injection attacks."},
        {"area": "Rate Limiting", "decision": "Apply rate limits on auth endpoints.", "reason": "Reduces credential stuffing and brute-force attacks."},
        {"area": "Payment Data", "decision": "Never store raw card details; use Stripe Payment Intents.", "reason": "PCI DSS compliance outsourced to Stripe."}
    ],
    deployment=[
        {"environment": "Development", "services": ["React dev server", "Node.js with nodemon", "PostgreSQL via Docker Compose"], "reason": "Rapid iteration with hot reloading."},
        {"environment": "Staging", "services": ["React static build", "Node.js production", "Managed PostgreSQL", "Stripe test mode"], "reason": "Mirrors production for QA and testing."},
        {"environment": "Production", "services": ["React on CDN/NGINX", "Node.js containers behind load balancer", "Managed PostgreSQL with backups", "Stripe live", "SendGrid/Twilio live"], "reason": "Managed container platform with auto-scaling."}
    ]
)


async def main():

    context = await generate_context(
        project,
        requirements,
        architecture,
    )

    print(
        context.model_dump_json(
            indent=2
        )
    )


asyncio.run(main())
