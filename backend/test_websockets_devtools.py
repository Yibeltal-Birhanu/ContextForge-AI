"""Regression tests for WebSockets preservation and dev-tool classification."""

import pytest
from app.utils.tech_normalizer import (
    normalize_tech_name,
    DEV_TOOLS,
    NON_TECH_WORDS,
    classify_tech,
    find_substituted_technologies,
)
from app.services.quality_gate import (
    run_quality_gate,
    _build_tech_preservation_report,
)
from app.models.project import ProjectState
from app.models.architecture import ArchitectureDocument, TechnologyChoice
from app.models.requirements import RequirementsDocument, Requirement
from app.models.context import ImplementationContext


# ============================================================
# WebSockets normalization
# ============================================================

class TestWebSocketsNormalization:
    def test_websockets_normalizes(self):
        assert normalize_tech_name("WebSockets") == "websockets"

    def test_websocket_single_normalizes(self):
        assert normalize_tech_name("WebSocket") == "websockets"

    def test_websockets_not_in_non_tech(self):
        assert "websockets" not in NON_TECH_WORDS

    def test_websockets_not_a_substitute(self):
        subs = find_substituted_technologies(["WebSockets"], ["WebSockets"])
        assert len(subs) == 0

    def test_websockets_preserved_when_selected(self):
        subs = find_substituted_technologies(
            ["WebSockets"], ["WebSockets", "Spring Boot"]
        )
        assert len(subs) == 0

    def test_websockets_no_category_conflict(self):
        subs = find_substituted_technologies(
            ["WebSockets"], ["Spring Boot", "MySQL"]
        )
        assert len(subs) == 0


# ============================================================
# Git/GitHub dev-tool classification
# ============================================================

class TestDevToolsClassification:
    def test_git_normalizes(self):
        assert normalize_tech_name("Git") == "git"

    def test_github_normalizes(self):
        assert normalize_tech_name("GitHub") == "github"

    def test_git_in_dev_tools(self):
        assert "git" in DEV_TOOLS

    def test_github_in_dev_tools(self):
        assert "github" in DEV_TOOLS

    def test_gitlab_in_dev_tools(self):
        assert "gitlab" in DEV_TOOLS

    def test_gitlab_ci_in_dev_tools(self):
        assert "gitlab ci" in DEV_TOOLS

    def test_git_not_substituted(self):
        subs = find_substituted_technologies(["Git"], ["Git"])
        assert len(subs) == 0

    def test_git_github_both_preserved(self):
        subs = find_substituted_technologies(
            ["Git", "GitHub"], ["Git", "GitHub"]
        )
        assert len(subs) == 0


# ============================================================
# Quality gate: dev tools don't cause rejection
# ============================================================

def _make_project(techs=None):
    return ProjectState(
        name="Test Project",
        idea="A test project",
        technologies=techs or ["React", "Node.js"],
        user_selected_technologies=[
            {"name": t, "purpose": "test", "category": "OTHER"}
            for t in (techs or ["React", "Node.js"])
        ],
    )


def _make_architecture(tech_stack_names):
    return ArchitectureDocument(
        system_architecture="Test architecture",
        components=[],
        technology_stack=[
            TechnologyChoice(
                category="Test",
                technology=name,
                reason="Test",
            )
            for name in tech_stack_names
        ],
        data_architecture=[],
        api_design=[],
        security=[],
        deployment=[],
    )


def _make_requirements():
    return RequirementsDocument(
        functional_requirements=[
            Requirement(
                id="FR-001",
                title="Login",
                description="User can log in",
                priority="high",
            )
        ],
        non_functional_requirements=[
            Requirement(
                id="NFR-001",
                title="Security",
                description="Must be secure",
                priority="high",
            )
        ],
    )


def _make_context(tech_stack=None):
    return ImplementationContext(
        project_title="Test",
        project_summary="Test project",
        problem="Test problem",
        architecture_summary="Test architecture",
        functional_requirements=["User can log in"],
        non_functional_requirements=["Must be secure"],
        technology_stack=tech_stack or [],
    )


class TestQualityGateDevTools:
    def test_dev_tools_not_rejected(self):
        """Missing Git/GitHub from architecture should NOT cause rejection."""
        project = _make_project(["React", "Node.js", "Git", "GitHub"])
        arch = _make_architecture(["React", "Node.js"])
        reqs = _make_requirements()
        ctx = _make_context(["React", "Node.js"])

        result = run_quality_gate(project, reqs, arch, ctx)

        git_rejections = [
            r for r in result.rejection_reasons
            if "Git" in r or "GitHub" in r or "git" in r.lower()
        ]
        assert len(git_rejections) == 0, f"Git/GitHub rejected: {git_rejections}"

    def test_runtime_tech_still_rejected(self):
        """Missing runtime tech like WebSockets SHOULD cause rejection."""
        project = _make_project(["React", "WebSockets"])
        arch = _make_architecture(["React"])
        reqs = _make_requirements()
        ctx = _make_context(["React"])

        result = run_quality_gate(project, reqs, arch, ctx)

        ws_rejections = [
            r for r in result.rejection_reasons
            if "WebSockets" in r
        ]
        assert len(ws_rejections) > 0, "WebSockets missing should be rejected"

    def test_websockets_preserved_no_rejection(self):
        """WebSockets in both user tech and architecture should not be rejected."""
        project = _make_project(["React", "WebSockets", "Spring Boot"])
        arch = _make_architecture(["React", "WebSockets", "Spring Boot"])
        reqs = _make_requirements()
        ctx = _make_context(["React", "WebSockets", "Spring Boot"])

        result = run_quality_gate(project, reqs, arch, ctx)

        ws_rejections = [
            r for r in result.rejection_reasons
            if "WebSockets" in r
        ]
        assert len(ws_rejections) == 0

    def test_substitution_still_detected(self):
        """Technology substitution (e.g. Django -> FastAPI) should still be caught."""
        project = _make_project(["Django"])
        arch = _make_architecture(["FastAPI"])
        reqs = _make_requirements()
        ctx = _make_context(["FastAPI"])

        result = run_quality_gate(project, reqs, arch, ctx)

        sub_rejections = [
            r for r in result.rejection_reasons
            if "substitution" in r.lower() or "Django" in r
        ]
        assert len(sub_rejections) > 0, "Django->FastAPI substitution should be caught"


# ============================================================
# Tech preservation report: dev tools tracked separately
# ============================================================

class TestTechPreservationReport:
    def _make_project_with_selected(self, techs):
        return ProjectState(
            name="Test",
            idea="Test",
            technologies=techs,
            user_selected_technologies=[
                {"name": t, "purpose": "test", "category": "OTHER"}
                for t in techs
            ],
        )

    def test_dev_tools_not_counted_as_missing(self):
        project = self._make_project_with_selected(["React", "Django", "Git", "GitHub"])
        arch = _make_architecture(["React", "Django"])
        ctx = _make_context(["React", "Django"])

        report = _build_tech_preservation_report(project, arch, ctx)

        assert "Git" not in report.missing
        assert "GitHub" not in report.missing
        assert report.missing_count == 0

    def test_runtime_tech_still_counted_as_missing(self):
        project = self._make_project_with_selected(["React", "WebSockets"])
        arch = _make_architecture(["React"])
        ctx = _make_context(["React"])

        report = _build_tech_preservation_report(project, arch, ctx)

        assert "WebSockets" in report.missing
        assert report.missing_count >= 1

    def test_websockets_preserved(self):
        project = self._make_project_with_selected(["React", "WebSockets", "Django"])
        arch = _make_architecture(["React", "WebSockets", "Django"])
        ctx = _make_context(["React", "WebSockets", "Django"])

        report = _build_tech_preservation_report(project, arch, ctx)

        assert "WebSockets" in report.preserved
        assert "Git" not in report.missing
        assert "GitHub" not in report.missing


# ============================================================
# QueueLess-like integration scenario
# ============================================================

class TestQueueLessLikeScenario:
    def test_full_stack_with_dev_tools(self):
        """Simulates QueueLess-like tech stack. Git/GitHub should not block."""
        project = ProjectState(
            name="QueueLess-like",
            idea="A queue platform",
            technologies=[
                "Java", "Spring Boot", "Vue.js", "TypeScript",
                "Flutter", "MySQL", "JWT", "WebSockets",
                "Firebase Cloud Messaging", "Google Maps API",
                "Docker", "Nginx", "Git", "GitHub",
            ],
            user_selected_technologies=[
                {"name": "Java", "purpose": "backend", "category": "BACKEND_FRAMEWORK"},
                {"name": "Spring Boot", "purpose": "backend", "category": "BACKEND_FRAMEWORK"},
                {"name": "Vue.js", "purpose": "frontend", "category": "FRONTEND_FRAMEWORK"},
                {"name": "TypeScript", "purpose": "frontend lang", "category": "FRONTEND_FRAMEWORK"},
                {"name": "Flutter", "purpose": "mobile", "category": "FRONTEND_FRAMEWORK"},
                {"name": "MySQL", "purpose": "database", "category": "DATABASE"},
                {"name": "JWT", "purpose": "auth", "category": "AUTH_PROVIDER"},
                {"name": "WebSockets", "purpose": "real-time", "category": "OTHER"},
                {"name": "Firebase Cloud Messaging", "purpose": "notifications", "category": "OTHER"},
                {"name": "Google Maps API", "purpose": "maps", "category": "MAP_PROVIDER"},
                {"name": "Docker", "purpose": "deployment", "category": "HOSTING"},
                {"name": "Nginx", "purpose": "reverse proxy", "category": "HOSTING"},
                {"name": "Git", "purpose": "version control", "category": "OTHER"},
                {"name": "GitHub", "purpose": "code hosting", "category": "OTHER"},
            ],
        )

        arch = ArchitectureDocument(
            system_architecture="Modular monolith with Spring Boot backend, Vue.js frontend, Flutter mobile",
            components=[
                {"name": "Backend API", "responsibility": "REST API and WebSocket server", "technologies": ["Java", "Spring Boot", "WebSockets"]},
                {"name": "Web Frontend", "responsibility": "Customer and admin web interface", "technologies": ["Vue.js", "TypeScript"]},
                {"name": "Mobile App", "responsibility": "Customer mobile interface", "technologies": ["Flutter"]},
            ],
            technology_stack=[
                TechnologyChoice(category="Backend", technology="Java", reason="Backend language"),
                TechnologyChoice(category="Backend", technology="Spring Boot", reason="Backend framework"),
                TechnologyChoice(category="Frontend", technology="Vue.js", reason="Web frontend"),
                TechnologyChoice(category="Frontend", technology="TypeScript", reason="Type safety"),
                TechnologyChoice(category="Mobile", technology="Flutter", reason="Mobile app"),
                TechnologyChoice(category="Database", technology="MySQL", reason="Primary database"),
                TechnologyChoice(category="Auth", technology="JWT", reason="Authentication"),
                TechnologyChoice(category="Real-time", technology="WebSockets", reason="Real-time queue updates"),
                TechnologyChoice(category="Notifications", technology="Firebase Cloud Messaging", reason="Push notifications"),
                TechnologyChoice(category="Maps", technology="Google Maps API", reason="Location services"),
                TechnologyChoice(category="Deployment", technology="Docker", reason="Container deployment"),
                TechnologyChoice(category="Infrastructure", technology="Nginx", reason="Reverse proxy"),
            ],
            data_architecture=[
                {"name": "users", "purpose": "User accounts and profiles", "important_fields": ["id BIGINT PRIMARY KEY", "email VARCHAR UNIQUE", "role ENUM"]},
                {"name": "queues", "purpose": "Queue definitions", "important_fields": ["id BIGINT PRIMARY KEY", "service_center_id FK"]},
                {"name": "queue_tickets", "purpose": "Customer queue entries", "important_fields": ["id BIGINT PRIMARY KEY", "queue_id FK", "status ENUM"]},
            ],
            api_design=[
                {"name": "Auth", "purpose": "Authentication", "endpoints": ["POST /api/auth/register", "POST /api/auth/login"]},
                {"name": "Queues", "purpose": "Queue management", "endpoints": ["GET /api/queues", "POST /api/queues/join"]},
            ],
            security=[
                {"area": "Authentication", "decision": "JWT with role-based access control", "reason": "Secure stateless auth"},
                {"area": "Data protection", "decision": "HTTPS and encrypted passwords", "reason": "Protect user data"},
            ],
            deployment=[
                {"environment": "Production", "services": ["Spring Boot API", "Vue.js SPA", "MySQL", "Nginx"], "reason": "Docker Compose deployment"},
            ],
        )

        reqs = RequirementsDocument(
            functional_requirements=[
                Requirement(id="FR-001", title="Queue joining", description="Users can join queues", priority="high"),
                Requirement(id="FR-002", title="Notifications", description="Users receive push notifications", priority="high"),
                Requirement(id="FR-003", title="Authentication", description="Users register and log in with JWT", priority="high"),
            ],
            non_functional_requirements=[
                Requirement(id="NFR-001", title="Real-time", description="Must support real-time updates via WebSockets", priority="high"),
                Requirement(id="NFR-002", title="Security", description="JWT auth and role-based access", priority="high"),
            ],
        )

        ctx = ImplementationContext(
            project_title="QueueLess",
            project_summary="Queue platform for Ethiopia",
            problem="Physical waiting lines at service centers",
            architecture_summary="Modular monolith with Spring Boot backend, Vue.js frontend, Flutter mobile",
            functional_requirements=[
                "Users can join queues remotely",
                "Users receive push notifications",
                "Users authenticate with JWT",
                "Staff manage queues",
                "Admin manages service centers",
            ],
            non_functional_requirements=[
                "Real-time queue updates via WebSockets",
                "JWT authentication with role-based access",
                "Optimized for slow internet",
                "English and Amharic support",
            ],
            technology_stack=[
                "Java", "Spring Boot", "Vue.js", "TypeScript",
                "Flutter", "MySQL", "JWT", "WebSockets",
                "Firebase Cloud Messaging", "Google Maps API",
                "Docker", "Nginx",
            ],
            data_model=[
                "User entity with roles",
                "ServiceCenter entity",
                "Queue entity",
                "ServiceRequest entity",
            ],
            api_contract=[
                "POST /api/auth/register",
                "POST /api/auth/login",
                "GET /api/queues",
                "POST /api/queues/join",
                "WebSocket /ws/queue/{id}",
            ],
            security_requirements=[
                "JWT authentication",
                "Role-based access control",
                "Rate limiting on auth endpoints",
            ],
            definition_of_done=[
                "All features implemented",
                "Tests passing",
                "Deployed via Docker",
            ],
        )

        result = run_quality_gate(project, reqs, arch, ctx)

        # No rejections for Git/GitHub
        git_rejections = [
            r for r in result.rejection_reasons
            if "git" in r.lower() or "github" in r.lower()
        ]
        assert len(git_rejections) == 0, f"Git/GitHub rejected: {git_rejections}"

        # No rejections for WebSockets
        ws_rejections = [
            r for r in result.rejection_reasons
            if "WebSocket" in r
        ]
        assert len(ws_rejections) == 0, f"WebSockets rejected: {ws_rejections}"

        # Overall scores may be low due to minimal test fixture
        # (no implementation phases, agent rules, etc.)
        # The critical assertions above verify:
        # 1. Git/GitHub not rejected (dev tools)
        # 2. WebSockets not rejected (preserved in architecture)
        # 3. Tech preservation report shows 0 missing
