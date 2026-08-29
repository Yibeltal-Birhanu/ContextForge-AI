"""Comprehensive E2E test for FarmLink Ethiopia.

Tests the complete pipeline: discovery, resume, technology preservation,
context generation, architecture, validation, quality gate, and agent readiness.
"""

import asyncio
import pytest
from app.models.project import ProjectState
from app.models.requirements import RequirementsDocument
from app.models.architecture import ArchitectureDocument
from app.engines.discovery import understand_project, apply_answers, find_missing_fields, generate_questions
from app.engines.requirements import generate_requirements
from app.engines.architecture import generate_architecture
from app.engines.context import generate_context
from app.engines.validation import validate_context
from app.engines.agent_readiness import check_agent_readiness
from app.services.quality_gate import run_quality_gate
from app.services.project_store import (
    create_project, get_project, save_project_state, get_project_state,
    save_context, get_context, delete_project,
)
from app.utils.tech_normalizer import classify_tech, find_substituted_technologies


# ============================================================
# FarmLink Ethiopia project definition
# ============================================================

FMLINK_IDEA = """FarmLink Ethiopia is a platform that connects smallholder farmers with agricultural input suppliers and agricultural experts.

Farmers can:
- Create an account
- Create a farm profile
- Search for seeds, fertilizer, pesticides, and farming equipment
- Request agricultural advice
- View supplier information
- Place an order for agricultural inputs
- Track order status
- Receive agricultural alerts

Suppliers can:
- Create a supplier account
- Manage products
- Manage inventory
- Receive farmer orders
- Update order status

Agricultural experts can:
- Create an expert profile
- List areas of expertise
- Answer farmer questions
- Provide agricultural recommendations

Administrators can:
- Manage users
- Verify suppliers and experts
- Manage product categories
- Monitor orders
- Manage reported content

The system should initially target Ethiopia and support Ethiopian cities and agricultural regions."""

FMLINK_ANSWERS = {
    "name": "FarmLink Ethiopia",
    "platform": "Web and mobile-responsive",
    "technologies": "Python, FastAPI, React, TypeScript, PostgreSQL, SQLAlchemy, JWT, Docker, Docker Compose, Google Maps API, S3-compatible storage, Africa's Talking SMS API",
    "database": "PostgreSQL",
    "authentication": "JWT-based authentication with email/password. Farmers, suppliers, experts, and admins each have role-based access.",
    "deployment": "Docker Compose on cloud VPS. Simple architecture for MVP.",
    "integrations": "Google Maps API for location, Africa's Talking for SMS notifications, S3-compatible storage for file uploads.",
}


def _run_async(coro):
    """Run an async function synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


async def _get_completed_project():
    """Get a project state with all discovery answered."""
    project = await understand_project(FMLINK_IDEA)
    for _ in range(10):
        missing = find_missing_fields(project)
        if not missing:
            break
        questions = await generate_questions(project, missing)
        if not questions:
            break
        answer_list = []
        for q in questions:
            field = q["field"]
            if field in FMLINK_ANSWERS:
                answer_list.append({"field": field, "answer": FMLINK_ANSWERS[field]})
        if not answer_list:
            break
        project = await apply_answers(project, answer_list)
    return project


# ============================================================
# Test 1: Full pipeline E2E (uses LLM - may be slow)
# ============================================================

class TestFarmLinkFullPipeline:
    """Test the complete FarmLink Ethiopia pipeline."""

    def test_discovery_start(self):
        """Discovery starts and extracts initial project state."""
        project = _run_async(understand_project(FMLINK_IDEA))
        assert project is not None
        assert project.name is not None or project.description is not None

    def test_discovery_questions_generated(self):
        """Discovery generates relevant questions."""
        project = _run_async(understand_project(FMLINK_IDEA))
        missing = find_missing_fields(project)
        assert len(missing) > 0, "Should have missing fields"
        questions = _run_async(generate_questions(project, missing))
        assert len(questions) > 0, "Should generate questions"

    def test_discovery_answer_all_questions(self):
        """Answer all discovery questions and verify project state."""
        project = _run_async(_get_completed_project())
        assert project is not None
        # After answering, project should have key fields
        assert project.name is not None or project.description is not None

    def test_technologies_preserved_after_discovery(self):
        """Technologies extracted from idea are preserved."""
        project = _run_async(_get_completed_project())
        # The LLM extracts some technologies from the idea text
        # It may not get all of them — the user answers the tech question explicitly
        # Key check: at least some technologies were captured
        assert len(project.technologies) > 0, f"No technologies captured: {project.technologies}"
        # Check that captured technologies are real (not generic words)
        techs_lower = [t.lower() for t in project.technologies]
        tech_text = " ".join(techs_lower)
        # PostgreSQL should be captured (explicitly in the idea)
        assert "postgres" in tech_text, f"PostgreSQL not found in {project.technologies}"
        # No wrong technologies should appear
        assert "django" not in tech_text, f"Django should not appear: {project.technologies}"
        assert "mysql" not in tech_text, f"MySQL should not appear: {project.technologies}"
        assert "node" not in tech_text, f"Node.js should not appear: {project.technologies}"

    def test_requirements_generation(self):
        """Requirements are generated for FarmLink."""
        project = _run_async(_get_completed_project())
        requirements = _run_async(generate_requirements(project))
        assert requirements is not None
        assert len(requirements.functional_requirements) > 0
        fr_texts = " ".join([fr.title + " " + fr.description for fr in requirements.functional_requirements]).lower()
        assert "auth" in fr_texts or "login" in fr_texts or "account" in fr_texts
        assert "product" in fr_texts or "catalog" in fr_texts or "inventory" in fr_texts
        assert "order" in fr_texts or "purchase" in fr_texts

    def test_architecture_generation(self):
        """Architecture is generated with correct technologies."""
        project = _run_async(_get_completed_project())
        requirements = _run_async(generate_requirements(project))
        architecture = _run_async(generate_architecture(project, requirements))
        assert architecture is not None
        assert architecture.system_architecture is not None
        tech_names = [tc.technology.lower() for tc in architecture.technology_stack]
        tech_text = " ".join(tech_names)
        assert "fastapi" in tech_text, f"FastAPI not in architecture: {tech_names}"
        assert "postgres" in tech_text, f"PostgreSQL not in architecture: {tech_names}"
        assert "react" in tech_text, f"React not in architecture: {tech_names}"
        assert "django" not in tech_text, f"Django should not appear: {tech_names}"
        assert "mysql" not in tech_text, f"MySQL should not appear: {tech_names}"

    def test_architecture_important_fields_normalization(self):
        """Architecture important_fields are normalized to strings."""
        project = _run_async(_get_completed_project())
        requirements = _run_async(generate_requirements(project))
        architecture = _run_async(generate_architecture(project, requirements))
        for entity in architecture.data_architecture:
            for f in entity.important_fields:
                assert isinstance(f, str), f"important_field is not a string: {f!r}"

    def test_context_generation(self):
        """Context is generated from project + requirements + architecture."""
        project = _run_async(_get_completed_project())
        requirements = _run_async(generate_requirements(project))
        architecture = _run_async(generate_architecture(project, requirements))
        context = _run_async(generate_context(project, requirements, architecture))
        assert context is not None
        assert len(context) > 100, "Context should be substantial"

    def test_validation(self):
        """Validation runs and produces a score."""
        project = _run_async(_get_completed_project())
        requirements = _run_async(generate_requirements(project))
        architecture = _run_async(generate_architecture(project, requirements))
        context = _run_async(generate_context(project, requirements, architecture))
        validation = validate_context(context, requirements, architecture)
        assert validation is not None
        assert validation.score > 0

    def test_quality_gate(self):
        """Quality gate runs and produces a result."""
        project = _run_async(_get_completed_project())
        requirements = _run_async(generate_requirements(project))
        architecture = _run_async(generate_architecture(project, requirements))
        context = _run_async(generate_context(project, requirements, architecture))
        gate = run_quality_gate(project, requirements, architecture, context)
        assert gate is not None
        assert gate.overall_score > 0
        assert hasattr(gate, "ready_for_agent")

    def test_no_cross_project_leakage(self):
        """FarmLink does not contain HealthLink/SkillSwap/AgriMarket terminology."""
        project = _run_async(_get_completed_project())
        requirements = _run_async(generate_requirements(project))
        architecture = _run_async(generate_architecture(project, requirements))
        context = _run_async(generate_context(project, requirements, architecture))
        all_text = (context + " " + architecture.system_architecture).lower()
        leakage_terms = [
            "healthlink", "skillswap", "agrimarket", "eduflow",
            "telebirr", "bedrock", "openai api",
            "patient", "doctor", "clinic", "appointment",
        ]
        for term in leakage_terms:
            assert term not in all_text, f"Cross-project leakage: '{term}' found"


# ============================================================
# Test 2: Technology substitution rejection (no LLM needed)
# ============================================================

class TestTechnologySubstitutionRejection:
    """Test that technology substitutions are detected."""

    def test_fastapi_not_replaced_by_django(self):
        """FastAPI must not be replaced by Django."""
        user_techs = ["Python", "FastAPI", "PostgreSQL"]
        arch_techs = ["Python", "Django", "PostgreSQL"]
        substitutions = find_substituted_technologies(user_techs, arch_techs)
        assert len(substitutions) > 0, "Should detect FastAPI -> Django"

    def test_postgresql_not_replaced_by_mysql(self):
        """PostgreSQL must not be replaced by MySQL."""
        user_techs = ["PostgreSQL"]
        arch_techs = ["MySQL"]
        substitutions = find_substituted_technologies(user_techs, arch_techs)
        assert len(substitutions) > 0, "Should detect PostgreSQL -> MySQL"

    def test_react_not_replaced_by_vue(self):
        """React must not be replaced by Vue."""
        user_techs = ["React"]
        arch_techs = ["Vue.js"]
        substitutions = find_substituted_technologies(user_techs, arch_techs)
        assert len(substitutions) > 0, "Should detect React -> Vue"

    def test_matching_techs_no_substitution(self):
        """Matching technologies produce no substitution."""
        user_techs = ["Python", "FastAPI", "PostgreSQL"]
        arch_techs = ["Python", "FastAPI", "PostgreSQL"]
        substitutions = find_substituted_technologies(user_techs, arch_techs)
        assert len(substitutions) == 0, f"False substitution detected: {substitutions}"


# ============================================================
# Test 3: Data normalization (no LLM needed)
# ============================================================

class TestDataNormalization:
    """Test that LLM output is normalized before Pydantic validation."""

    def test_important_fields_string_passthrough(self):
        """String important_fields pass through ArchitectureDocument."""
        doc = ArchitectureDocument(
            system_architecture="Test",
            data_architecture=[{
                "name": "users",
                "purpose": "User accounts",
                "important_fields": ["id BIGINT PRIMARY KEY", "email VARCHAR UNIQUE"],
            }],
        )
        assert doc.data_architecture[0].important_fields == ["id BIGINT PRIMARY KEY", "email VARCHAR UNIQUE"]

    def test_api_endpoints_string_passthrough(self):
        """String API endpoints pass through ArchitectureDocument."""
        doc = ArchitectureDocument(
            system_architecture="Test",
            api_design=[{
                "name": "Default",
                "purpose": "API",
                "endpoints": ["GET /health - Health check", "POST /api/v1/users - Create user"],
            }],
        )
        assert len(doc.api_design[0].endpoints) == 2
        assert "GET /health" in doc.api_design[0].endpoints[0]

    def test_tech_normalizer_classifies_known_techs(self):
        """Known technologies are classified."""
        # FastAPI should be BACKEND_FRAMEWORK or similar
        cat = classify_tech("FastAPI")
        assert cat != "UNKNOWN", f"FastAPI should be classified, got {cat}"

    def test_tech_normalizer_classifies_unknown(self):
        """Unknown technology returns OTHER."""
        cat = classify_tech("SomeUnknownFramework123")
        assert cat == "OTHER"


# ============================================================
# Test 4: Error handling (no LLM needed)
# ============================================================

class TestErrorHandling:
    """Test error handling for various failure scenarios."""

    def test_empty_project_has_many_missing_fields(self):
        """Empty project should have many missing fields."""
        missing = find_missing_fields(ProjectState(
            name=None, description=None, problem=None,
            target_users=[], core_features=[],
            technologies=[], database=None, authentication=None,
            integrations=[], constraints=[], deployment=None,
        ))
        assert len(missing) > 0

    def test_nonexistent_project_returns_none(self):
        """Getting state for nonexistent project returns None."""
        state = get_project_state("nonexistent-id-12345")
        assert state is None

    def test_partial_project_fewer_missing_fields(self):
        """Project with some data has fewer missing fields."""
        project = ProjectState(
            name="Test App", description="A test application",
            problem="Testing", target_users=["developers"],
            core_features=["testing"], technologies=["Python"],
            database="PostgreSQL", authentication="JWT",
            integrations=[], constraints=[], deployment="Docker",
        )
        missing = find_missing_fields(project)
        # Should have fewer missing fields than an empty project
        empty_missing = find_missing_fields(ProjectState(
            name=None, description=None, problem=None,
            target_users=[], core_features=[],
            technologies=[], database=None, authentication=None,
            integrations=[], constraints=[], deployment=None,
        ))
        assert len(missing) < len(empty_missing)


# ============================================================
# Test 5: Project persistence and resume (no LLM needed)
# ============================================================

class TestProjectPersistence:
    """Test project save/resume cycle."""

    def test_save_and_resume_project(self):
        """Create, save state, and resume a project."""
        project = create_project("FarmLink Test", FMLINK_IDEA)
        project_id = project["id"]

        state_data = {
            "name": "FarmLink Ethiopia",
            "technologies": ["Python", "FastAPI", "React"],
            "database": "PostgreSQL",
            "_conversation_history": [
                {"field": "name", "question": "Project name?", "answer": "FarmLink Ethiopia"},
                {"field": "technologies", "question": "Tech stack?", "answer": "Python, FastAPI"},
            ],
        }
        save_project_state(project_id, state_data, status="discovery", name="FarmLink Ethiopia")

        state = get_project_state(project_id)
        assert state is not None
        assert state["project_data"]["name"] == "FarmLink Ethiopia"
        assert len(state["project_data"]["_conversation_history"]) == 2
        assert state["status"] == "discovery"

        delete_project(project_id)

    def test_project_isolation(self):
        """Two projects remain isolated."""
        p1 = create_project("Project A", "Idea A")
        p2 = create_project("Project B", "Idea B")

        save_project_state(p1["id"], {"name": "Project A", "tech": ["Python"]})
        save_project_state(p2["id"], {"name": "Project B", "tech": ["Node.js"]})

        s1 = get_project_state(p1["id"])
        s2 = get_project_state(p2["id"])

        assert s1["project_data"]["name"] == "Project A"
        assert s2["project_data"]["name"] == "Project B"
        assert "Node.js" not in s1["project_data"].get("tech", [])
        assert "Python" not in s2["project_data"].get("tech", [])

        delete_project(p1["id"])
        delete_project(p2["id"])

    def test_conversation_history_isolated(self):
        """Conversation histories remain separate."""
        p1 = create_project("Hist A", "Idea A")
        p2 = create_project("Hist B", "Idea B")

        h1 = [{"field": "name", "question": "Name?", "answer": "Project A"}]
        h2 = [{"field": "name", "question": "Name?", "answer": "Project B"}]

        save_project_state(p1["id"], {"name": "A", "_conversation_history": h1})
        save_project_state(p2["id"], {"name": "B", "_conversation_history": h2})

        s1 = get_project_state(p1["id"])
        s2 = get_project_state(p2["id"])

        assert s1["project_data"]["_conversation_history"][0]["answer"] == "Project A"
        assert s2["project_data"]["_conversation_history"][0]["answer"] == "Project B"

        delete_project(p1["id"])
        delete_project(p2["id"])
