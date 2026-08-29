"""Regression tests for generic discovery technology extraction."""

from unittest.mock import AsyncMock, patch

import pytest

from app.engines.discovery import apply_answers, _extract_technologies_with_status
from app.engines.architecture import generate_architecture
from app.engines.context import generate_context
from app.models.architecture import ArchitectureDocument
from app.models.project import ProjectState
from app.models.requirements import RequirementsDocument
from app.services.project_pipeline import _merge_user_selected_technologies
from app.utils.tech_normalizer import dedupe_technology_strings


def test_readiness_allows_legitimate_healthcare_vocabulary():
    from app.engines.agent_readiness import _check_context_isolation
    from app.models.architecture import ArchitectureDocument
    from app.models.context import ImplementationContext
    from app.models.requirements import RequirementsDocument

    project = ProjectState(
        name="MobiCare",
        description="A platform connecting patients with clinics.",
        problem="Patients need easier healthcare access.",
        target_users=["Patients"],
    )
    context = ImplementationContext(
        project_title="MobiCare",
        project_summary="A healthcare platform for patients.",
        problem="Patients need easier healthcare access.",
        architecture_summary="A simple healthcare platform.",
        target_users=["Patients"],
    )
    warnings = []
    _check_context_isolation(
        project, RequirementsDocument(), ArchitectureDocument(system_architecture=""), context, warnings
    )
    assert warnings == []


def test_readiness_reports_patient_domain_leakage():
    from app.engines.agent_readiness import _check_context_isolation
    from app.models.architecture import ArchitectureDocument
    from app.models.context import ImplementationContext
    from app.models.requirements import RequirementsDocument

    project = ProjectState(name="LocalMarket", description="A marketplace for local goods.")
    context = ImplementationContext(
        project_title="LocalMarket",
        project_summary="A marketplace for patients and local goods.",
        problem="Patients can order goods.",
        architecture_summary="A simple marketplace.",
    )
    warnings = []
    _check_context_isolation(
        project, RequirementsDocument(), ArchitectureDocument(system_architecture=""), context, warnings
    )
    assert any(w.category == "context_isolation" for w in warnings)


def test_context_prompt_does_not_unconditionally_require_healthcare_roles():
    from app.prompts.context import CONTEXT_ENGINEERING_SYSTEM_PROMPT

    assert "For healthcare projects" in CONTEXT_ENGINEERING_SYSTEM_PROMPT
    assert "Users can only access resources authorized for their account and role" in CONTEXT_ENGINEERING_SYSTEM_PROMPT


AUTH_PROSE = (
    "Primary: Email + password. Optional: Google and LinkedIn sign-in. "
    "Not required for MVP: Apple sign-in and Facebook/social platforms. "
    "Users should be able to create an account with email/password and "
    "optionally use Google or LinkedIn..."
)


def test_authentication_prose_is_not_a_technology():
    project = ProjectState(authentication=AUTH_PROSE)

    _merge_user_selected_technologies(
        project,
        [{"field": "authentication", "answer": AUTH_PROSE}],
    )

    names = [technology.name for technology in project.user_selected_technologies]
    assert names == []
    assert AUTH_PROSE not in names


def test_concrete_technologies_in_prose_are_preserved():
    project = ProjectState()
    answer = (
        "Python, FastAPI, PostgreSQL, SQLAlchemy, Docker, "
        "S3-compatible storage, GitHub Actions, Google OAuth, "
        "LinkedIn OAuth, JWT/session authentication"
    )

    _merge_user_selected_technologies(
        project,
        [{"field": "technologies", "answer": answer}],
    )

    names = {technology.name for technology in project.user_selected_technologies}
    assert {
        "python",
        "fastapi",
        "postgresql",
        "sqlalchemy",
        "docker",
        "s3-compatible storage",
        "github actions",
        "google oauth",
        "linkedin oauth",
        "jwt",
    } <= names
    assert all(len(name.split()) < 6 for name in names)


def test_lifecycle_classification_keeps_future_and_alternatives_inactive():
    answer = (
        "PostgreSQL and Redis are required for MVP. Chapa is active. "
        "Telebirr is a future provider, post-MVP. DigitalOcean is selected "
        "for MVP hosting; Hetzner is an alternative."
    )

    statuses = dict(_extract_technologies_with_status(answer))

    assert statuses["postgresql"] == "MVP_REQUIRED"
    assert statuses["redis"] == "MVP_REQUIRED"
    assert statuses["chapa"] == "MVP_REQUIRED"
    assert statuses["telebirr"] == "FUTURE"
    assert statuses["digitalocean"] == "MVP_REQUIRED"
    assert statuses["hetzner"] == "ALTERNATIVE"


def test_excluded_technologies_and_implementation_details_are_not_mvp():
    answer = (
        "Node.js, Express, TypeScript, PostgreSQL, Prisma, Android/Kotlin, "
        "Jetpack Compose, React, Vite, Docker are MVP technologies. "
        "MongoDB is explicitly excluded from MVP. Use PostgreSQL SELECT "
        "FOR UPDATE SKIP LOCKED for job claiming."
    )

    statuses = dict(_extract_technologies_with_status(answer))

    assert statuses["mongodb"] == "EXCLUDED"
    assert "for update" not in statuses
    assert statuses["postgresql"] == "MVP_REQUIRED"


def test_backup_provider_is_alternative_not_required():
    statuses = dict(_extract_technologies_with_status(
        "Africa's Talking is primary for SMS; Twilio is a backup provider."
    ))

    assert statuses["africas talking"] == "MVP_REQUIRED"
    assert statuses["twilio"] == "ALTERNATIVE"


def test_detailed_stack_deduplicates_later_bare_aliases():
    stack = dedupe_technology_strings([
        "PostgreSQL - Primary relational database",
        "S3-compatible object storage (DigitalOcean Spaces)",
        "Docker Compose - Container orchestration",
        "postgresql",
        "s3-compatible storage",
        "docker compose",
    ])

    assert stack == [
        "PostgreSQL - Primary relational database",
        "S3-compatible object storage (DigitalOcean Spaces)",
        "Docker Compose - Container orchestration",
    ]


@pytest.mark.asyncio
async def test_llm_cannot_inject_an_entire_natural_language_technology():
    project = ProjectState()
    llm_result = {
        **project.model_dump(),
        "authentication": AUTH_PROSE,
        "user_selected_technologies": [
            {
                "name": "Use a combination, but keep the MVP simple: " + AUTH_PROSE,
                "purpose": "authentication",
                "category": "AUTH_PROVIDER",
            }
        ],
    }

    with patch(
        "app.engines.discovery.generate_structured",
        new=AsyncMock(return_value=llm_result),
    ):
        updated = await apply_answers(project, [{"field": "authentication", "answer": AUTH_PROSE}])

    assert updated.user_selected_technologies == []
    assert updated.authentication == AUTH_PROSE


@pytest.mark.asyncio
async def test_selected_technologies_are_restored_when_ai_omits_them():
    project = ProjectState(
        user_selected_technologies=[
            {"name": "mongodb", "purpose": "database", "category": "DATABASE"},
            {"name": "s3-compatible storage", "purpose": "files", "category": "STORAGE"},
        ]
    )
    requirements = RequirementsDocument()
    architecture_result = {
        "system_architecture": "Simple application.",
        "technology_stack": [],
    }
    context_result = {
        "project_title": "Test",
        "project_summary": "Test.",
        "problem": "Test.",
        "architecture_summary": "Simple application.",
        "technology_stack": [
            "MongoDB - Document database",
            "S3-compatible object storage - User uploads",
        ],
    }

    with patch(
        "app.engines.architecture.generate_structured",
        new=AsyncMock(return_value=architecture_result),
    ), patch(
        "app.engines.context.generate_structured",
        new=AsyncMock(return_value=context_result),
    ):
        architecture = await generate_architecture(project, requirements)
        context = await generate_context(project, requirements, architecture)

    assert {choice.technology for choice in architecture.technology_stack} == {
        "mongodb", "s3-compatible storage"
    }
    assert context.technology_stack == [
        "MongoDB - Document database",
        "S3-compatible object storage - User uploads",
    ]


@pytest.mark.asyncio
async def test_future_and_alternative_technologies_stay_out_of_active_stack():
    project = ProjectState(
        user_selected_technologies=[
            {"name": "digitalocean", "category": "HOSTING", "status": "MVP_REQUIRED"},
            {"name": "telebirr", "category": "PAYMENT_PROVIDER", "status": "FUTURE"},
            {"name": "hetzner", "category": "HOSTING", "status": "ALTERNATIVE"},
        ]
    )
    requirements = RequirementsDocument()

    with patch(
        "app.engines.architecture.generate_structured",
        new=AsyncMock(return_value={
            "system_architecture": "MVP application.",
            "technology_stack": [
                {"category": "Hosting", "technology": "DigitalOcean", "reason": "MVP"},
                {"category": "Payments", "technology": "Telebirr", "reason": "Later"},
                {"category": "Hosting", "technology": "Hetzner", "reason": "Backup"},
            ],
        }),
    ):
        architecture = await generate_architecture(project, requirements)

    assert [choice.technology for choice in architecture.technology_stack] == [
        "DigitalOcean"
    ]
