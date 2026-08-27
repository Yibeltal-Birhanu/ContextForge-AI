import os
os.environ.setdefault("OPENROUTER_API_KEY", "test")
os.environ.setdefault("OPENROUTER_MODEL", "test")

from app.models.project import ProjectState
from app.models.context import ImplementationContext
from app.engines.context_improvement import _identify_issues


# ============================================================
# Test 1: Good context -> no issues
# ============================================================

print("=" * 60)
print("TEST 1: Good context -> no issues")
print("=" * 60)

good_checks = {
    "checks": {
        "requirements_coverage": 100,
        "architecture_consistency": 100,
        "technology_consistency": 100,
        "api_coverage": 95,
        "data_model_coverage": 100,
        "security_coverage": 100,
        "implementation_coverage": 90,
        "agent_rules_quality": 100,
        "definition_of_done": 100,
    }
}

good_context = ImplementationContext(
    project_title="Yibe Market",
    project_summary="Online supermarket.",
    problem="Convenient shopping.",
    target_users=["Customer"],
    functional_requirements=["FR-001: Browse products"],
    non_functional_requirements=["NFR-001: Security"],
    architecture_summary="Monolith.",
    technology_stack=["React", "Node.js"],
    data_model=["Product"],
    api_contract=["GET /products"],
    security_requirements=["JWT auth"],
    implementation_phases=[
        {"phase": 1, "name": "Foundation", "objective": "Setup", "tasks": ["Init"], "deliverables": ["Done"]}
    ],
    agent_rules=[{"category": "Security", "rule": "Use env vars"}],
    definition_of_done=["All features working"],
)

issues = _identify_issues(good_context, good_checks)
print(f"  Issues found: {len(issues)}")
assert len(issues) == 0, f"Expected 0 issues, got {len(issues)}"
print("  >>> PASS\n")


# ============================================================
# Test 2: API weakness -> API issue identified
# ============================================================

print("=" * 60)
print("TEST 2: API weakness -> API issue identified")
print("=" * 60)

api_weak_checks = {
    "checks": {
        "requirements_coverage": 100,
        "architecture_consistency": 100,
        "technology_consistency": 100,
        "api_coverage": 60,
        "data_model_coverage": 100,
        "security_coverage": 100,
        "implementation_coverage": 90,
        "agent_rules_quality": 100,
        "definition_of_done": 100,
    }
}

issues = _identify_issues(good_context, api_weak_checks)
print(f"  Issues found: {len(issues)}")
for i, issue in enumerate(issues):
    print(f"  - {issue}")
assert len(issues) == 1, f"Expected 1 issue, got {len(issues)}"
assert "API Coverage" in issues[0]
print("  >>> PASS\n")


# ============================================================
# Test 3: Multiple weaknesses -> multiple issues
# ============================================================

print("=" * 60)
print("TEST 3: Multiple weaknesses -> multiple issues")
print("=" * 60)

multi_weak_checks = {
    "checks": {
        "requirements_coverage": 100,
        "architecture_consistency": 100,
        "technology_consistency": 100,
        "api_coverage": 50,
        "data_model_coverage": 60,
        "security_coverage": 70,
        "implementation_coverage": 40,
        "agent_rules_quality": 55,
        "definition_of_done": 45,
    }
}

issues = _identify_issues(good_context, multi_weak_checks)
print(f"  Issues found: {len(issues)}")
for i, issue in enumerate(issues):
    print(f"  - {issue[:80]}...")
assert len(issues) == 6, f"Expected 6 issues, got {len(issues)}"
print("  >>> PASS\n")


# ============================================================
# Test 4: Borderline scores (85+) -> no issues
# ============================================================

print("=" * 60)
print("TEST 4: Borderline scores (85+) -> no issues")
print("=" * 60)

borderline_checks = {
    "checks": {
        "requirements_coverage": 100,
        "architecture_consistency": 100,
        "technology_consistency": 100,
        "api_coverage": 85,
        "data_model_coverage": 85,
        "security_coverage": 100,
        "implementation_coverage": 85,
        "agent_rules_quality": 85,
        "definition_of_done": 85,
    }
}

issues = _identify_issues(good_context, borderline_checks)
print(f"  Issues found: {len(issues)}")
assert len(issues) == 0, f"Expected 0 issues, got {len(issues)}"
print("  >>> PASS\n")


# ============================================================
# Test 5: Empty checks dict -> no issues
# ============================================================

print("=" * 60)
print("TEST 5: Empty checks dict -> no issues")
print("=" * 60)

issues = _identify_issues(good_context, {})
print(f"  Issues found: {len(issues)}")
assert len(issues) == 0, f"Expected 0 issues, got {len(issues)}"
print("  >>> PASS\n")


# ============================================================
# Test 6: All weaknesses -> 9 issues
# ============================================================

print("=" * 60)
print("TEST 6: All weaknesses -> 9 issues")
print("=" * 60)

all_weak_checks = {
    "checks": {
        "requirements_coverage": 50,
        "architecture_consistency": 60,
        "technology_consistency": 70,
        "api_coverage": 40,
        "data_model_coverage": 55,
        "security_coverage": 65,
        "implementation_coverage": 30,
        "agent_rules_quality": 45,
        "definition_of_done": 35,
    }
}

issues = _identify_issues(good_context, all_weak_checks)
print(f"  Issues found: {len(issues)}")
assert len(issues) == 9, f"Expected 9 issues, got {len(issues)}"
print("  >>> PASS\n")


print("=" * 60)
print("ALL CONTEXT IMPROVEMENT TESTS COMPLETE")
print("=" * 60)
