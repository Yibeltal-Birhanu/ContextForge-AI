"""Tests for the improve-context feature: persistence, artifact, project_id."""

import os
os.environ.setdefault("OPENROUTER_API_KEY", "test")
os.environ.setdefault("OPENROUTER_MODEL", "test")

import asyncio
import pytest
from unittest.mock import patch, AsyncMock
from app.models.project import ProjectState
from app.models.context import ImplementationContext
from app.models.requirements import RequirementsDocument, Requirement
from app.models.architecture import (
    ArchitectureDocument, DataEntity, TechnologyChoice,
    ArchitectureComponent,
)
from app.engines.context_improvement import _identify_issues
from app.services.project_store import (
    create_project, save_context, get_context,
    delete_project, get_project,
)


# ============================================================
# Test data builders
# ============================================================

def make_project():
    return ProjectState(
        name="Test Improve Project",
        description="A test project for improvement",
        problem="Testing improvement flow",
        target_users=["Developers"],
        core_features=["Core feature 1"],
        platform="Web",
        technologies=["Python", "FastAPI", "PostgreSQL"],
        database="PostgreSQL",
        authentication="JWT",
        integrations=[],
        constraints=[],
        deployment="Docker",
    )


def _reqs_dict():
    return {
        "functional_requirements": [
            {"id": "FR-001", "title": "User login", "description": "User login", "priority": "high"},
            {"id": "FR-002", "title": "Dashboard", "description": "Dashboard", "priority": "medium"},
        ],
        "non_functional_requirements": [
            {"id": "NFR-001", "title": "Security", "description": "Security", "priority": "high"},
        ],
    }


def _arch_dict():
    return {
        "system_architecture": "Monolith API server with PostgreSQL database",
        "components": [
            {"name": "API Server", "responsibility": "Handle HTTP requests", "technologies": ["Python", "FastAPI"]}
        ],
        "technology_stack": [
            {"category": "LANGUAGE", "technology": "Python", "reason": "Backend"},
            {"category": "BACKEND_FRAMEWORK", "technology": "FastAPI", "reason": "API"},
            {"category": "DATABASE", "technology": "PostgreSQL", "reason": "Data"},
        ],
        "data_architecture": [
            {"name": "users", "purpose": "User accounts", "important_fields": ["id BIGINT PRIMARY KEY", "email VARCHAR"]}
        ],
        "api_design": [],
        "security": [],
        "deployment": [],
    }


def _ctx_dict():
    return {
        "project_title": "Test Improve Project",
        "project_summary": "Test project",
        "problem": "Testing",
        "target_users": ["Developers"],
        "functional_requirements": ["FR-001: User login"],
        "non_functional_requirements": ["NFR-001: Security"],
        "architecture_summary": "Monolith API",
        "technology_stack": ["Python", "FastAPI", "PostgreSQL"],
        "data_model": ["User"],
        "api_contract": ["GET /users"],
        "security_requirements": ["JWT auth"],
        "implementation_phases": [
            {"phase": 1, "name": "Foundation", "objective": "Setup",
             "tasks": ["Init"], "deliverables": ["Done"]}
        ],
        "agent_rules": [{"category": "Security", "rule": "Use env vars"}],
        "definition_of_done": ["All features working"],
    }


def make_context():
    return ImplementationContext(**_ctx_dict())


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _mock_all_engines():
    """Create mocks for all engine modules and return the context improvement mock."""
    import app.engines.context_improvement as cim
    import app.engines.requirements as req_mod
    import app.engines.architecture as arch_mod
    import app.engines.context as ctx_mod

    mock_reqs = AsyncMock(return_value=_reqs_dict())
    mock_arch = AsyncMock(return_value=_arch_dict())
    mock_ctx = AsyncMock(return_value=_ctx_dict())
    mock_improve = AsyncMock(return_value=_ctx_dict())

    patches = [
        patch.object(req_mod, "generate_structured", mock_reqs),
        patch.object(arch_mod, "generate_structured", mock_arch),
        patch.object(ctx_mod, "generate_structured", mock_ctx),
        patch.object(cim, "generate_structured", mock_improve),
    ]

    return patches, mock_improve


# ============================================================
# Tests for _identify_issues
# ============================================================

class TestIdentifyIssues:

    def test_good_context_no_issues(self):
        good_checks = {"checks": {k: 100 for k in [
            "requirements_coverage", "architecture_consistency",
            "technology_consistency", "api_coverage", "data_model_coverage",
            "security_coverage", "implementation_coverage",
            "agent_rules_quality", "definition_of_done",
        ]}}
        issues = _identify_issues(make_context(), good_checks)
        assert len(issues) == 0

    def test_weak_api_creates_issue(self):
        issues = _identify_issues(make_context(), {"checks": {"api_coverage": 50}})
        assert len(issues) == 1
        assert "API Coverage" in issues[0]

    def test_multiple_weaknesses(self):
        issues = _identify_issues(make_context(), {"checks": {
            "api_coverage": 40, "data_model_coverage": 50, "security_coverage": 60,
        }})
        assert len(issues) == 3

    def test_empty_checks(self):
        issues = _identify_issues(make_context(), {})
        assert len(issues) == 0

    def test_borderline_85_no_issues(self):
        issues = _identify_issues(make_context(), {"checks": {"api_coverage": 85}})
        assert len(issues) == 0

    def test_all_weaknesses(self):
        issues = _identify_issues(make_context(), {"checks": {
            "requirements_coverage": 50, "architecture_consistency": 60,
            "technology_consistency": 70, "api_coverage": 40,
            "data_model_coverage": 55, "security_coverage": 65,
            "implementation_coverage": 30, "agent_rules_quality": 45,
            "definition_of_done": 35,
        }})
        assert len(issues) == 9


# ============================================================
# Tests for improve_project_context (with mocked LLM)
# ============================================================

class TestImproveProjectContext:

    def test_improve_persists_context_when_gate_fails(self):
        """Context should be saved even when quality gate still fails."""
        from app.services.context_improvement import improve_project_context

        patches, _ = _mock_all_engines()
        project = create_project(name="Improve Persist Test", idea="Test")
        project_id = project["id"]
        quality_checks = {"checks": {"api_coverage": 50, "security_coverage": 50}}

        with patches[0], patches[1], patches[2], patches[3]:
            _run_async(improve_project_context(
                project_data=make_project().model_dump(),
                answers={},
                quality_checks=quality_checks,
                project_id=project_id,
            ))

        saved = get_context(project_id)
        assert saved is not None, "Context should be persisted even on quality gate failure"
        assert saved.get("implementation_context") is not None

        delete_project(project_id)

    def test_improve_without_project_id_works(self):
        """Improve without project_id should still work."""
        from app.services.context_improvement import improve_project_context

        patches, _ = _mock_all_engines()
        quality_checks = {"checks": {"api_coverage": 50}}

        with patches[0], patches[1], patches[2], patches[3]:
            result = _run_async(improve_project_context(
                project_data=make_project().model_dump(),
                answers={},
                quality_checks=quality_checks,
                project_id=None,
            ))

        assert result is not None
        assert result.stage.value in ("validation", "complete")

    def test_improve_no_issues_skips_llm(self):
        """When no issues, improvement should skip the LLM call."""
        from app.services.context_improvement import improve_project_context

        patches, mock_improve = _mock_all_engines()
        quality_checks = {"checks": {k: 100 for k in [
            "api_coverage", "security_coverage", "data_model_coverage",
            "implementation_coverage", "agent_rules_quality",
            "definition_of_done", "requirements_coverage",
            "architecture_consistency", "technology_consistency",
        ]}}

        with patches[0], patches[1], patches[2], patches[3]:
            _run_async(improve_project_context(
                project_data=make_project().model_dump(),
                answers={},
                quality_checks=quality_checks,
            ))

        mock_improve.assert_not_called()

    def test_improve_project_state_updated(self):
        """Project state should be updated after improvement."""
        from app.services.context_improvement import improve_project_context

        patches, _ = _mock_all_engines()
        project = create_project(name="State Update Test", idea="Test")
        project_id = project["id"]
        quality_checks = {"checks": {"api_coverage": 50}}

        with patches[0], patches[1], patches[2], patches[3]:
            _run_async(improve_project_context(
                project_data=make_project().model_dump(),
                answers={},
                quality_checks=quality_checks,
                project_id=project_id,
            ))

        updated = get_project(project_id)
        assert updated is not None
        assert updated["current_stage"] == "improvement"

        delete_project(project_id)

    def test_improvement_preserves_project_info(self):
        """Improvement does not lose project-specific information."""
        from app.services.context_improvement import improve_project_context

        patches, _ = _mock_all_engines()
        quality_checks = {"checks": {"api_coverage": 50}}

        with patches[0], patches[1], patches[2], patches[3]:
            result = _run_async(improve_project_context(
                project_data=make_project().model_dump(),
                answers={},
                quality_checks=quality_checks,
            ))

        assert result.project.name == "Test Improve Project"
        assert "PostgreSQL" in result.project.technologies
        assert "FastAPI" in result.project.technologies
        assert result.project.database == "PostgreSQL"
        assert result.project.authentication == "JWT"


# ============================================================
# Tests for project_id in request schema
# ============================================================

class TestImproveRequestSchema:

    def test_schema_accepts_project_id(self):
        from app.schemas.context_improvement import ImproveContextRequest
        req = ImproveContextRequest(
            project_id="test-project-id",
            project={"name": "test"},
            answers={},
            quality_checks={"checks": {}},
        )
        assert req.project_id == "test-project-id"

    def test_schema_works_without_project_id(self):
        from app.schemas.context_improvement import ImproveContextRequest
        req = ImproveContextRequest(
            project={"name": "test"},
            answers={},
            quality_checks={"checks": {}},
        )
        assert req.project_id is None


# ============================================================
# Tests for persistence flow
# ============================================================

class TestPersistenceFlow:

    def test_save_and_load_improved_context(self):
        project = create_project(name="Persistence Test", idea="Test")
        project_id = project["id"]

        context_data = _ctx_dict()
        context_data["project_title"] = "Persistence Test"

        save_context(
            project_id=project_id,
            implementation_context=context_data,
            quality_result={"overall_score": 95},
        )

        loaded = get_context(project_id)
        assert loaded is not None
        assert loaded["implementation_context"]["project_title"] == "Persistence Test"
        assert loaded["quality_result"]["overall_score"] == 95

        delete_project(project_id)

    def test_artifact_creation_and_retrieval(self):
        from app.models.validation import ContextValidationResult
        from app.engines.artifact import create_artifact
        from app.services.artifact_store import get_artifact

        ctx = make_context()
        validation = ContextValidationResult(valid=True, score=90)

        artifact = create_artifact(context=ctx, validation=validation)
        assert artifact is not None
        assert artifact.project_name == "Test Improve Project"
        assert artifact.validation_score == 90
        assert len(artifact.markdown) > 0

        retrieved = get_artifact(artifact.project_id)
        assert retrieved is not None
        assert retrieved.markdown == artifact.markdown
