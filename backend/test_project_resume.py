"""Tests for project state save/resume functionality."""

import pytest
from app.services.project_store import (
    create_project,
    get_project,
    update_project,
    save_project_state,
    get_project_state,
    save_context,
    get_context,
    save_artifact,
    get_artifacts,
    delete_project,
)


class TestProjectStateSaveResume:
    """Test saving and resuming project state."""

    def test_create_and_get_project(self):
        """Create a project and retrieve it."""
        project = create_project("Test Project", "I want to build a test app")
        assert project["name"] == "Test Project"
        assert project["status"] == "discovery"
        assert project["project_data"] == {}

        fetched = get_project(project["id"])
        assert fetched is not None
        assert fetched["name"] == "Test Project"

        delete_project(project["id"])

    def test_save_and_get_project_state(self):
        """Save project state and retrieve it."""
        project = create_project("Resume Test", "Test idea")

        state_data = {
            "name": "Resume Test",
            "description": "A test project",
            "problem": "Testing resume",
            "target_users": ["developers"],
            "core_features": ["feature1"],
            "technologies": ["Python", "Django"],
            "database": "PostgreSQL",
            "_conversation_history": [
                {"field": "name", "question": "What is the name?", "answer": "Resume Test"},
            ],
        }

        updated = save_project_state(
            project["id"],
            state_data,
            status="discovery",
            current_stage="discovery",
            name="Resume Test",
        )
        assert updated is not None
        assert updated["project_data"] is not None
        assert updated["project_data"]["name"] == "Resume Test"
        assert updated["project_data"]["technologies"] == ["Python", "Django"]
        assert len(updated["project_data"]["_conversation_history"]) == 1

        # Retrieve via get_project_state
        state = get_project_state(project["id"])
        assert state is not None
        assert state["project_data"]["name"] == "Resume Test"
        assert state["status"] == "discovery"

        delete_project(project["id"])

    def test_save_state_preserves_conversation_history(self):
        """Conversation history is preserved in project state."""
        project = create_project("History Test", "Test idea")

        history = [
            {"field": "name", "question": "Project name?", "answer": "MyApp"},
            {"field": "platform", "question": "What platform?", "answer": "Web"},
            {"field": "database", "question": "Which database?", "answer": "PostgreSQL"},
        ]

        state_data = {
            "name": "MyApp",
            "technologies": ["Python", "Django"],
            "_conversation_history": history,
        }

        save_project_state(project["id"], state_data, status="discovery")

        state = get_project_state(project["id"])
        saved_history = state["project_data"]["_conversation_history"]
        assert len(saved_history) == 3
        assert saved_history[0]["field"] == "name"
        assert saved_history[0]["answer"] == "MyApp"
        assert saved_history[2]["field"] == "database"
        assert saved_history[2]["answer"] == "PostgreSQL"

        delete_project(project["id"])

    def test_update_state_multiple_times(self):
        """State can be updated multiple times (simulating discovery rounds)."""
        project = create_project("Multi Update", "Test idea")

        # Round 1
        state1 = {"name": "App", "_conversation_history": [
            {"field": "name", "question": "Name?", "answer": "App"},
        ]}
        save_project_state(project["id"], state1, status="discovery")

        # Round 2
        state2 = {
            "name": "App",
            "technologies": ["React", "Node.js"],
            "_conversation_history": [
                {"field": "name", "question": "Name?", "answer": "App"},
                {"field": "technologies", "question": "Tech stack?", "answer": "React, Node.js"},
            ],
        }
        save_project_state(project["id"], state2, status="discovery")

        state = get_project_state(project["id"])
        assert state["project_data"]["technologies"] == ["React", "Node.js"]
        assert len(state["project_data"]["_conversation_history"]) == 2

        delete_project(project["id"])

    def test_complete_project_state(self):
        """Save a completed project state."""
        project = create_project("Complete Test", "Test idea")

        state_data = {
            "name": "Complete App",
            "technologies": ["Django", "PostgreSQL"],
            "status": "complete",
        }
        save_project_state(
            project["id"],
            state_data,
            status="complete",
            current_stage="complete",
            name="Complete App",
        )

        state = get_project_state(project["id"])
        assert state["status"] == "complete"
        assert state["current_stage"] == "complete"
        assert state["project_data"]["name"] == "Complete App"

        # Also save context and artifact
        save_context(
            project["id"],
            requirements={"functional_requirements": []},
            architecture={"system_architecture": "Django monolith"},
            quality_result={"overall_score": 95, "ready_for_agent": True},
        )
        save_artifact(project["id"], markdown="# Complete App", txt="Complete App", quality_score=95)

        # Verify full detail
        context = get_context(project["id"])
        assert context is not None
        assert context["quality_result"]["overall_score"] == 95

        artifacts = get_artifacts(project["id"])
        assert len(artifacts) == 1
        assert artifacts[0]["quality_score"] == 95

        delete_project(project["id"])

    def test_nonexistent_project_returns_none(self):
        """Getting state for nonexistent project returns None."""
        state = get_project_state("nonexistent-id-12345")
        assert state is None

    def test_empty_project_data(self):
        """Project with empty project_data returns empty dict."""
        project = create_project("Empty Test", "Test idea")
        state = get_project_state(project["id"])
        assert state is not None
        assert state["project_data"] == {}
        delete_project(project["id"])

    def test_project_list_reflects_updates(self):
        """Project list reflects status and name updates."""
        project = create_project("List Test", "Test idea")

        save_project_state(
            project["id"],
            {"name": "Updated Name"},
            status="complete",
            current_stage="complete",
            name="Updated Name",
        )

        from app.services.project_store import list_projects
        projects = list_projects()
        found = [p for p in projects if p["id"] == project["id"]]
        assert len(found) == 1
        assert found[0]["status"] == "complete"
        assert found[0]["name"] == "Updated Name"

        delete_project(project["id"])

    def test_delete_project_cleans_up(self):
        """Deleting a project removes all associated data."""
        project = create_project("Delete Test", "Test idea")

        save_project_state(
            project["id"],
            {"name": "Delete Me"},
            status="discovery",
        )
        save_context(project["id"], requirements={"test": True})
        save_artifact(project["id"], markdown="test", txt="test", quality_score=50)

        delete_project(project["id"])

        assert get_project(project["id"]) is None
        assert get_project_state(project["id"]) is None
        assert get_context(project["id"]) is None
        assert get_artifacts(project["id"]) == []
