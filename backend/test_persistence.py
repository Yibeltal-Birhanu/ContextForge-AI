import os
os.environ.setdefault("OPENROUTER_API_KEY", "test")
os.environ.setdefault("OPENROUTER_MODEL", "test")

from app.services.project_store import (
    create_project,
    get_project,
    list_projects,
    update_project,
    delete_project,
    save_context,
    get_context,
    save_artifact,
    get_artifacts,
    get_latest_artifact,
)


# ============================================================
# Test 1: Create and retrieve project
# ============================================================

print("=" * 60)
print("TEST 1: Create and retrieve project")
print("=" * 60)

project = create_project(
    name="Yibe Market",
    idea="Online supermarket for customers to browse and order products.",
    description="An e-commerce platform.",
)

print(f"  ID: {project['id']}")
print(f"  Name: {project['name']}")
print(f"  Status: {project['status']}")
print(f"  Stage: {project['current_stage']}")

assert project["name"] == "Yibe Market"
assert project["status"] == "discovery"
print("  >>> PASS\n")


# ============================================================
# Test 2: List projects
# ============================================================

print("=" * 60)
print("TEST 2: List projects")
print("=" * 60)

projects = list_projects()
print(f"  Projects found: {len(projects)}")
assert len(projects) >= 1
print("  >>> PASS\n")


# ============================================================
# Test 3: Update project
# ============================================================

print("=" * 60)
print("TEST 3: Update project")
print("=" * 60)

updated = update_project(
    project["id"],
    name="Yibe Market v2",
    status="complete",
    current_stage="complete",
    project_data={"name": "Yibe Market v2", "description": "Updated"},
)

print(f"  Name: {updated['name']}")
print(f"  Status: {updated['status']}")
assert updated["name"] == "Yibe Market v2"
assert updated["status"] == "complete"
print("  >>> PASS\n")


# ============================================================
# Test 4: Save and retrieve context
# ============================================================

print("=" * 60)
print("TEST 4: Save and retrieve context")
print("=" * 60)

save_context(
    project["id"],
    requirements={"functional": ["FR-001: Browse products"]},
    architecture={"system": "Three-tier monolith"},
    implementation_context={"title": "Yibe Market"},
    quality_result={"score": 96, "passed": True},
)

context = get_context(project["id"])
print(f"  Requirements: {context['requirements']}")
print(f"  Architecture: {context['architecture']}")
print(f"  Quality: {context['quality_result']}")
assert context is not None
assert context["requirements"]["functional"][0] == "FR-001: Browse products"
print("  >>> PASS\n")


# ============================================================
# Test 5: Save and retrieve artifact
# ============================================================

print("=" * 60)
print("TEST 5: Save and retrieve artifact")
print("=" * 60)

artifact = save_artifact(
    project["id"],
    markdown="# Yibe Market\n\nAI Agent Context...",
    txt="Yibe Market\n\nAI Agent Context...",
    quality_score=96,
)

print(f"  Artifact ID: {artifact['id']}")
print(f"  Score: {artifact['quality_score']}")

artifacts = get_artifacts(project["id"])
print(f"  Total artifacts: {len(artifacts)}")
assert len(artifacts) >= 1

latest = get_latest_artifact(project["id"])
assert latest["quality_score"] == 96
print("  >>> PASS\n")


# ============================================================
# Test 6: Create second project (isolation)
# ============================================================

print("=" * 60)
print("TEST 6: Two projects remain isolated")
print("=" * 60)

project2 = create_project(
    name="CareerBridge",
    idea="Job platform for students.",
    description="Connect students with employers.",
)

projects = list_projects()
print(f"  Total projects: {len(projects)}")
assert len(projects) >= 2

ctx1 = get_context(project["id"])
ctx2 = get_context(project2["id"])
print(f"  Project 1 has context: {ctx1 is not None}")
print(f"  Project 2 has context: {ctx2 is not None}")
# Project 2 should not have context yet
assert ctx2 is None or ctx2.get("requirements") is None
print("  >>> PASS\n")


# ============================================================
# Test 7: Delete project
# ============================================================

print("=" * 60)
print("TEST 7: Delete project and associated data")
print("=" * 60)

deleted = delete_project(project2["id"])
print(f"  Deleted: {deleted}")
assert deleted

remaining = get_project(project2["id"])
print(f"  Project exists: {remaining is not None}")
assert remaining is None

# Original project should still exist
original = get_project(project["id"])
assert original is not None
print(f"  Original project still exists: True")
print("  >>> PASS\n")


# ============================================================
# Test 8: Project data persistence
# ============================================================

print("=" * 60)
print("TEST 8: Project data is persisted")
print("=" * 60)

# Simulate re-read (like after restart)
retrieved = get_project(project["id"])
print(f"  Name: {retrieved['name']}")
print(f"  Status: {retrieved['status']}")
print(f"  Data: {retrieved['project_data']}")
assert retrieved["name"] == "Yibe Market v2"
assert retrieved["project_data"]["name"] == "Yibe Market v2"
print("  >>> PASS\n")


# Cleanup
delete_project(project["id"])

print("=" * 60)
print("ALL PERSISTENCE TESTS COMPLETE")
print("=" * 60)
