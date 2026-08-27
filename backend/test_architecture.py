import asyncio
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.engines.architecture import generate_architecture
from app.models.project import ProjectState
from app.models.requirements import RequirementsDocument


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
                {"description": "When an order is successfully created, the system sends an order confirmation notification (email or SMS) to the customer."},
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


async def main():

    architecture = await generate_architecture(
        project,
        requirements
    )

    print(
        architecture.model_dump_json(
            indent=2
        )
    )


asyncio.run(main())
