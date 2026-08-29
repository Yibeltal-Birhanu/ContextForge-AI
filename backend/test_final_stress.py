"""
Final Stress Test — Brand-New Projects + Real LLM Architecture Preservation

Tests 1-6: QueueLess, brand-new project, substitution attack, dev tools,
WebSockets end-to-end, and resume functionality.
"""

import json
import time
import urllib.request
import urllib.error
import uuid
import pytest

BASE = "http://127.0.0.1:8000"


def api_get(path, timeout=30):
    return json.load(urllib.request.urlopen(f"{BASE}{path}", timeout=timeout))


def api_post(path, data, timeout=300):
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        f"{BASE}{path}", data=body,
        headers={"Content-Type": "application/json"},
    )
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def api_delete(path, timeout=30):
    req = urllib.request.Request(f"{BASE}{path}", method="DELETE")
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def create_project(name, idea):
    return api_post("/projects", {"name": name, "idea": idea})


def continue_project(project, answers, history=None):
    return api_post("/projects/continue", {
        "project": project,
        "answers": answers,
        "conversation_history": history or [],
    })


def save_state(project_id, project_data, status="discovery", current_stage="discovery"):
    return api_post(f"/projects/{project_id}/resume", {
        "project_data": project_data,
        "status": status,
        "current_stage": current_stage,
    })





def get_project(project_id):
    resp = api_get(f"/projects/{project_id}")
    return resp["project"]


def run_full_pipeline(name, idea, answers, history=None):
    """Create project, answer all questions, run through to validation/completion."""
    # Create
    proj_resp = create_project(name, idea)
    project_id = proj_resp["id"]
    project = get_project(project_id)

    # Continue with all answers
    result = continue_project(project, answers, history)

    stage = result.get("stage", "unknown")
    complete = result.get("complete", False)
    proj = result.get("project", {})
    if hasattr(proj, "model_dump"):
        pd = proj.model_dump()
    else:
        pd = proj if isinstance(proj, dict) else {}

    quality = result.get("quality")
    questions = result.get("questions", [])

    # Save state
    pd["_conversation_history"] = result.get("conversation_history", [])
    save_state(project_id, pd,
               status="completed" if complete else "discovery",
               current_stage=stage)

    return {
        "project_id": project_id,
        "stage": stage,
        "complete": complete,
        "project_data": pd,
        "quality": quality,
        "questions": questions,
        "architecture": result.get("architecture"),
        "context": result.get("context"),
    }


# ============================================================
# Test 1: QueueLess Ethiopia — Full Pipeline
# ============================================================

class Test1QueueLessFullPipeline:
    def test_queueless_full_pipeline(self):
        """Run complete QueueLess pipeline and verify WebSockets in architecture."""
        result = run_full_pipeline(
            name="QueueLess Ethiopia Stress Test",
            idea="QueueLess Ethiopia is a digital queue and appointment platform. "
                 "Customers join queues remotely, track position, receive notifications. "
                 "Staff manage queues. Admins manage service centers.",
            answers={
                "technologies": "Java, Spring Boot, Vue.js, TypeScript, Flutter, MySQL, "
                               "Spring Data JPA, Hibernate, JWT, WebSockets, "
                               "Firebase Cloud Messaging, Google Maps API, Docker, Nginx, "
                               "Git, GitHub",
                "problem": "Physical waiting lines at Ethiopian service centers.",
                "target_users": "Customers, Staff, Organization admins, Platform admins.",
                "core_features": "Queue joining, tracking, notifications, appointments, auth.",
                "platform": "Flutter mobile plus Vue.js web",
                "constraints": "Low budget, 3-4 months, 2-3 devs, slow internet, English and Amharic",
                "deployment": "Docker on cloud VPS, Docker Compose, Nginx reverse proxy.",
            },
        )

        assert result["stage"] in ("validation", "complete"), \
            f"Expected validation or complete, got {result['stage']}"

        # Check technologies captured
        pd = result["project_data"]
        techs = pd.get("technologies", [])
        assert "WebSockets" in techs or "websockets" in [t.lower() for t in techs], \
            f"WebSockets not in project technologies: {techs}"
        assert "Java" in techs or "java" in [t.lower() for t in techs], \
            f"Java not in project technologies: {techs}"
        assert "MySQL" in techs or "mysql" in [t.lower() for t in techs], \
            f"MySQL not in project technologies: {techs}"

        # Check quality gate
        q = result.get("quality")
        if q:
            print(f"  Quality: overall={q.get('overall_score')}, "
                  f"validation={q.get('validation_score')}, "
                  f"readiness={q.get('readiness_score')}")
            # Tech preservation should show 0 missing runtime techs
            tech_pres = q.get("tech_preservation", {})
            missing = tech_pres.get("missing", [])
            preserved = tech_pres.get("preserved", [])
            print(f"  Preserved: {preserved}")
            print(f"  Missing: {missing}")
            # WebSockets should be preserved
            ws_preserved = any("websocket" in p.lower() for p in preserved)
            assert ws_preserved, f"WebSockets not in preserved list: {preserved}"

        # Clean up
        api_delete(f"/projects/{result['project_id']}")


# ============================================================
# Test 2: Brand-New Unrelated Project
# ============================================================

class Test2BrandNewProject:
    def test_art_platform_full_pipeline(self):
        """Test with a completely new project: ArtShare — art marketplace."""
        result = run_full_pipeline(
            name="ArtShare Platform",
            idea="ArtShare is an online marketplace for African artists to sell digital "
                 "art, prints, and commissions. Artists create profiles showcasing their "
                 "portfolio. Buyers browse by style, medium, and price range. The platform "
                 "supports direct purchases, commission requests, and artist following. "
                 "Features include image galleries, secure payment via Stripe, artist "
                 "analytics dashboard, and order tracking.",
            answers={
                "technologies": "Python, FastAPI, React, TypeScript, PostgreSQL, "
                               "SQLAlchemy, Stripe, Docker, Redis, AWS S3",
                "problem": "African artists lack accessible online platforms to sell "
                          "digital art and commissions globally.",
                "target_users": "Artists who create art, Buyers who purchase art, "
                               "Platform administrators.",
                "core_features": "Artist profiles, portfolio galleries, search and "
                                "filtering, purchasing, commission requests, order "
                                "tracking, analytics dashboard.",
                "platform": "Responsive web application",
                "constraints": "Low budget MVP, 3 month timeline, 2 developers, "
                              "must handle image uploads efficiently.",
                "deployment": "Docker on AWS, S3 for image storage.",
            },
        )

        pd = result["project_data"]
        techs = pd.get("technologies", [])

        # Verify this is NOT a QueueLess/HealthLink project
        assert "Java" not in techs, f"QueueLess tech leaked: Java found"
        assert "Spring Boot" not in techs, f"QueueLess tech leaked: Spring Boot found"
        assert "MySQL" not in techs, f"QueueLess tech leaked: MySQL found"

        # Verify correct technologies
        assert "Python" in techs or "python" in [t.lower() for t in techs], \
            f"Python not in technologies: {techs}"
        assert "FastAPI" in techs or "fastapi" in [t.lower() for t in techs], \
            f"FastAPI not in technologies: {techs}"
        assert "PostgreSQL" in techs or "postgresql" in [t.lower() for t in techs], \
            f"PostgreSQL not in technologies: {techs}"
        assert "React" in techs or "react" in [t.lower() for t in techs], \
            f"React not in technologies: {techs}"

        # Verify domain is correct
        assert "art" in pd.get("problem", "").lower() or \
               "art" in pd.get("core_features", "").lower() or \
               "art" in pd.get("description", "").lower() or \
               "ArtShare" in str(techs), \
            "Project doesn't appear to be about art"

        # No QueueLess/HealthLink leakage
        all_text = json.dumps(pd).lower()
        assert "queue" not in all_text or "queue" in pd.get("problem", "").lower(), \
            "QueueLess terminology leaked into ArtShare"
        assert "patient" not in all_text, "HealthLink terminology leaked"
        assert "telebirr" not in all_text, "HealthLink technology leaked"

        # Clean up
        api_delete(f"/projects/{result['project_id']}")


# ============================================================
# Test 3: Technology Substitution Attack
# ============================================================

class Test3SubstitutionAttack:
    def test_substitution_detected(self):
        """User selects Django/FastAPI stack, verify no silent substitution."""
        from app.utils.tech_normalizer import find_substituted_technologies
        from app.services.quality_gate import run_quality_gate
        from app.models.project import ProjectState
        from app.models.architecture import ArchitectureDocument, TechnologyChoice
        from app.models.requirements import RequirementsDocument, Requirement
        from app.models.context import ImplementationContext

        # User selected
        user_techs = ["Python", "FastAPI", "PostgreSQL", "React", "Docker", "Redis", "WebSockets"]

        # Simulate architecture that incorrectly uses Django instead of FastAPI
        bad_arch_techs = ["Python", "Django", "PostgreSQL", "React", "Docker", "Redis"]

        subs = find_substituted_technologies(user_techs, bad_arch_techs)
        assert len(subs) > 0, "Django->FastAPI substitution was NOT detected"

        # Verify which substitution was found
        categories = [s["category"] for s in subs]
        assert "BACKEND_FRAMEWORK" in categories, \
            f"BACKEND_FRAMEWORK substitution not found: {subs}"

        # Also test: correct architecture should have 0 substitutions
        correct_arch_techs = ["Python", "FastAPI", "PostgreSQL", "React", "Docker", "Redis", "WebSockets"]
        subs2 = find_substituted_technologies(user_techs, correct_arch_techs)
        assert len(subs2) == 0, f"False substitution detected: {subs2}"

        # Full quality gate test
        project = ProjectState(
            name="Substitution Test",
            idea="Test project",
            technologies=user_techs,
            user_selected_technologies=[
                {"name": t, "purpose": "test", "category": "OTHER"} for t in user_techs
            ],
        )
        arch = ArchitectureDocument(
            system_architecture="Test",
            components=[],
            technology_stack=[
                TechnologyChoice(category="Backend", technology=t, reason="Test")
                for t in bad_arch_techs
            ],
            data_architecture=[],
            api_design=[],
            security=[],
            deployment=[],
        )
        reqs = RequirementsDocument(
            functional_requirements=[
                Requirement(id="FR-001", title="Test", description="Test", priority="high")
            ],
            non_functional_requirements=[],
        )
        ctx = ImplementationContext(
            project_title="Test",
            project_summary="Test",
            problem="Test",
            architecture_summary="Test",
            functional_requirements=["Test"],
            non_functional_requirements=[],
            technology_stack=bad_arch_techs,
        )

        result = run_quality_gate(project, reqs, arch, ctx)

        # Must have rejection for Django substitution
        sub_rejections = [
            r for r in result.rejection_reasons
            if "substitution" in r.lower() or "Django" in r
        ]
        assert len(sub_rejections) > 0, \
            f"Django substitution not rejected: {result.rejection_reasons}"


# ============================================================
# Test 4: Development Tools
# ============================================================

class Test4DevelopmentTools:
    def test_dev_tools_classification(self):
        """Git/GitHub/GitHub Actions classified as DEV_TOOLS."""
        from app.utils.tech_normalizer import normalize_tech_name, DEV_TOOLS

        assert normalize_tech_name("Git") == "git"
        assert normalize_tech_name("GitHub") == "github"
        assert normalize_tech_name("GitHub Actions") == "github actions"

        assert "git" in DEV_TOOLS
        assert "github" in DEV_TOOLS
        assert "github actions" in DEV_TOOLS

    def test_dev_tools_no_rejection(self):
        """Dev tools in user tech should not cause architecture rejection."""
        from app.services.quality_gate import run_quality_gate
        from app.models.project import ProjectState
        from app.models.architecture import ArchitectureDocument, TechnologyChoice
        from app.models.requirements import RequirementsDocument, Requirement
        from app.models.context import ImplementationContext

        project = ProjectState(
            name="DevTools Test",
            idea="Test",
            technologies=["Python", "FastAPI", "React", "Git", "GitHub", "GitHub Actions"],
            user_selected_technologies=[
                {"name": "Python", "purpose": "backend", "category": "BACKEND_FRAMEWORK"},
                {"name": "FastAPI", "purpose": "backend", "category": "BACKEND_FRAMEWORK"},
                {"name": "React", "purpose": "frontend", "category": "FRONTEND_FRAMEWORK"},
                {"name": "Git", "purpose": "vcs", "category": "OTHER"},
                {"name": "GitHub", "purpose": "code hosting", "category": "OTHER"},
                {"name": "GitHub Actions", "purpose": "CI/CD", "category": "OTHER"},
            ],
        )

        # Architecture has runtime techs but NOT Git/GitHub
        arch = ArchitectureDocument(
            system_architecture="Test",
            components=[],
            technology_stack=[
                TechnologyChoice(category="Backend", technology="Python", reason="Test"),
                TechnologyChoice(category="Backend", technology="FastAPI", reason="Test"),
                TechnologyChoice(category="Frontend", technology="React", reason="Test"),
            ],
            data_architecture=[],
            api_design=[],
            security=[],
            deployment=[],
        )

        reqs = RequirementsDocument(
            functional_requirements=[
                Requirement(id="FR-001", title="Test", description="Test", priority="high")
            ],
            non_functional_requirements=[],
        )
        ctx = ImplementationContext(
            project_title="Test",
            project_summary="Test",
            problem="Test",
            architecture_summary="Test",
            functional_requirements=["Test"],
            non_functional_requirements=[],
            technology_stack=["Python", "FastAPI", "React"],
        )

        result = run_quality_gate(project, reqs, arch, ctx)

        # No rejection for Git/GitHub
        git_rejections = [
            r for r in result.rejection_reasons
            if "git" in r.lower() or "github" in r.lower()
        ]
        assert len(git_rejections) == 0, \
            f"Dev tools incorrectly rejected: {git_rejections}"

        # Runtime tech still preserved
        tech_pres = result.tech_preservation
        assert "Git" not in tech_pres.missing, "Git should not be in missing"
        assert "GitHub" not in tech_pres.missing, "GitHub should not be in missing"


# ============================================================
# Test 5: WebSockets End-to-End
# ============================================================

class Test5WebSocketsEndToEnd:
    def test_websockets_full_pipeline(self):
        """Real-time project with WebSockets — verify it appears in architecture."""
        result = run_full_pipeline(
            name="LiveChat Ethiopia",
            idea="LiveChat Ethiopia is a real-time customer support platform. "
                 "Businesses can embed a chat widget on their websites. Customers "
                 "send messages and receive instant responses. Agents handle multiple "
                 "conversations. Features include typing indicators, message history, "
                 "file sharing, and offline message queuing.",
            answers={
                "technologies": "Python, FastAPI, React, TypeScript, PostgreSQL, "
                               "Redis, WebSockets, Docker, Nginx",
                "problem": "Ethiopian businesses need affordable real-time customer support.",
                "target_users": "Businesses, Support agents, Customers.",
                "core_features": "Real-time chat, typing indicators, message history, "
                                "file sharing, offline queuing.",
                "platform": "Responsive web application with embedded widget",
                "constraints": "Low budget, must handle slow internet gracefully.",
                "deployment": "Docker on cloud VPS.",
            },
        )

        pd = result["project_data"]
        techs = pd.get("technologies", [])

        # WebSockets MUST be in technologies
        ws_in_techs = any("websocket" in t.lower() for t in techs)
        assert ws_in_techs, f"WebSockets not captured in technologies: {techs}"

        # Check quality gate preservation
        q = result.get("quality")
        if q:
            tech_pres = q.get("tech_preservation", {})
            preserved = tech_pres.get("preserved", [])
            missing = tech_pres.get("missing", [])
            ws_preserved = any("websocket" in p.lower() for p in preserved)
            print(f"  WebSockets preserved: {ws_preserved}")
            print(f"  All preserved: {preserved}")
            print(f"  Missing: {missing}")
            assert ws_preserved, f"WebSockets not preserved: {preserved}"

        # Verify no QueueLess/HealthLink leakage
        all_text = json.dumps(pd).lower()
        assert "queue" not in all_text or "queue" in pd.get("problem", "").lower(), \
            "QueueLess terminology leaked"
        assert "patient" not in all_text, "HealthLink terminology leaked"

        api_delete(f"/projects/{result['project_id']}")


# ============================================================
# Test 6: Resume Test
# ============================================================

class Test6Resume:
    def test_partial_answer_resume(self):
        """Create project, answer some questions, save, resume, continue."""
        # Create project
        proj_resp = create_project(
            "Resume Test Project",
            "A simple task management app for small teams."
        )
        project_id = proj_resp["id"]
        project = get_project(project_id)

        # Answer only first question
        result1 = continue_project(project, {
            "technologies": "Python, Django, PostgreSQL, React, Docker"
        })

        stage1 = result1.get("stage")
        assert stage1 == "discovery", f"Expected discovery, got {stage1}"
        assert not result1.get("complete"), "Should not be complete yet"

        # Save state
        proj1 = result1.get("project", {})
        pd1 = proj1.model_dump() if hasattr(proj1, "model_dump") else (proj1 if isinstance(proj1, dict) else {})
        pd1["_conversation_history"] = result1.get("conversation_history", [])
        save_state(project_id, pd1, status="discovery", current_stage="discovery")

        # Reload project (simulates page refresh / switch away)
        reloaded = get_project(project_id)
        assert reloaded.get("project_data"), "Project data not saved"

        # Continue answering remaining questions
        remaining = result1.get("questions", [])
        remaining_answers = {}
        for q in remaining:
            field = q.get("field", "")
            if field == "problem":
                remaining_answers[field] = "Small teams struggle with task tracking."
            elif field == "target_users":
                remaining_answers[field] = "Team members and project managers."
            elif field == "core_features":
                remaining_answers[field] = "Task creation, assignment, status tracking, notifications."
            elif field == "platform":
                remaining_answers[field] = "Web application"
            elif field == "constraints":
                remaining_answers[field] = "Low budget, 2 month MVP, 2 developers."
            elif field == "deployment":
                remaining_answers[field] = "Docker on cloud VPS."
            elif field == "authentication":
                remaining_answers[field] = "Email and password with JWT."
            elif field == "database":
                remaining_answers[field] = "PostgreSQL"
            else:
                remaining_answers[field] = f"Default answer for {field}"

        if remaining_answers:
            result2 = continue_project(
                get_project(project_id),
                remaining_answers,
                result1.get("conversation_history", []),
            )
            stage2 = result2.get("stage")
            complete2 = result2.get("complete", False)
            print(f"  After resume: stage={stage2}, complete={complete2}")

            # Save final state
            proj2 = result2.get("project", {})
            pd2 = proj2.model_dump() if hasattr(proj2, "model_dump") else (proj2 if isinstance(proj2, dict) else {})
            pd2["_conversation_history"] = result2.get("conversation_history", [])
            save_state(project_id, pd2,
                       status="completed" if complete2 else "discovery",
                       current_stage=stage2)

        # Verify project still exists and has state
        final = get_project(project_id)
        assert final.get("project_data"), "Final project data missing"

        # Clean up
        api_delete(f"/projects/{project_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-x"])
