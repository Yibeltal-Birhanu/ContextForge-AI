"""
Edge case and error handling tests for ContextForge.

Tests that the pipeline handles:
1. Empty project description
2. Incomplete requirements
3. No user-selected technologies
4. Many technologies
5. Conflicting technologies
6. Rejected alternatives
7. Duplicate technologies
8. Technology replacement
9. Multiple projects sequentially
10. Empty architecture
11. Empty context
12. Validation with missing sections
"""
import sys
import traceback


def run_test(name, func):
    try:
        func()
        print(f"  PASS: {name}")
        return True
    except Exception as e:
        print(f"  FAIL: {name}")
        print(f"    {e}")
        traceback.print_exc()
        return False


# ============================================================
# Test 1: Empty project description
# ============================================================
def test_empty_description():
    from app.models.project import ProjectState
    from app.engines.discovery import find_missing_fields

    project = ProjectState(
        name="Test",
        description=None,
        problem=None,
        target_users=[],
        core_features=[],
    )
    missing = find_missing_fields(project)
    assert "description" in missing
    assert "problem" in missing
    assert "target_users" in missing


# ============================================================
# Test 2: No user-selected technologies
# ============================================================
def test_no_user_selected_techs():
    from app.models.project import ProjectState
    from app.models.architecture import ArchitectureDocument, TechnologyChoice
    from app.models.context import ImplementationContext, ImplementationPhase, AgentRule
    from app.models.requirements import RequirementsDocument, Requirement
    from app.engines.agent_readiness import check_agent_readiness

    project = ProjectState(
        name="Simple App",
        description="A simple app.",
        problem="Problem.",
        target_users=["Users"],
        core_features=["Feature"],
        # No user_selected_technologies
    )

    reqs = RequirementsDocument(
        functional_requirements=[
            Requirement(id="FR-001", title="Feature", description="F", priority="MUST_HAVE"),
        ],
    )

    arch = ArchitectureDocument(
        system_architecture="Simple web app.",
        components=[],
        technology_stack=[
            TechnologyChoice(category="Frontend", technology="React", reason="Standard"),
        ],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )

    ctx = ImplementationContext(
        project_title="Simple App", project_summary="Simple.", problem="Problem.",
        target_users=["Users"],
        functional_requirements=["FR-001: Feature"],
        non_functional_requirements=[],
        architecture_summary="Simple web app.",
        technology_stack=["React"],
        data_model=[], api_contract=[], security_requirements=[],
        implementation_phases=[ImplementationPhase(phase=1, name="F", objective="Setup", tasks=["Setup"], deliverables=["App"])],
        agent_rules=[AgentRule(category="Architecture", rule="Simple"), AgentRule(category="Security", rule="JWT"), AgentRule(category="Testing", rule="Tests")],
        definition_of_done=["Done"],
    )

    result = check_agent_readiness(project, reqs, arch, ctx)
    # Should work without crashing
    assert result.score >= 0
    assert result.score <= 100


# ============================================================
# Test 3: Many technologies
# ============================================================
def test_many_technologies():
    from app.models.project import ProjectState, UserSelectedTechnology
    from app.utils.tech_normalizer import normalize_tech_list, find_substituted_technologies

    techs = [
        "React", "Vue", "Angular", "Svelte",  # 4 frontend frameworks (unusual)
        "Node.js", "Express", "FastAPI", "Django",  # 4 backends (unusual)
        "PostgreSQL", "MongoDB", "Redis", "MySQL",  # 4 databases (unusual)
        "Docker", "Kubernetes", "AWS", "GCP",  # 4 infrastructure
    ]

    project = ProjectState(
        name="Mega Stack",
        description="Many technologies.",
        problem="Problem.",
        target_users=["Users"],
        core_features=["Feature"],
        technologies=techs,
        user_selected_technologies=[
            UserSelectedTechnology(name=t, purpose="general", category="OTHER")
            for t in techs
        ],
    )

    # Should handle many technologies without crashing
    norm = normalize_tech_list(techs)
    assert len(norm) > 0

    # No substitutions among user-selected (all are user-selected)
    subs = find_substituted_technologies(techs, techs)
    assert len(subs) == 0


# ============================================================
# Test 4: Conflicting technologies (same category)
# ============================================================
def test_conflicting_technologies():
    from app.utils.tech_normalizer import find_substituted_technologies

    # User selects React, architecture uses Angular
    subs = find_substituted_technologies(["React"], ["Angular"])
    assert len(subs) == 1
    assert subs[0]["category"] == "FRONTEND_FRAMEWORK"

    # User selects PostgreSQL, architecture uses MongoDB
    subs = find_substituted_technologies(["PostgreSQL"], ["MongoDB"])
    assert len(subs) == 1
    assert subs[0]["category"] == "DATABASE"


# ============================================================
# Test 5: Rejected alternatives
# ============================================================
def test_rejected_alternatives():
    from app.utils.tech_normalizer import find_substituted_technologies

    # User selects PostgreSQL (MongoDB is rejected)
    # Architecture uses PostgreSQL — no substitution
    subs = find_substituted_technologies(["PostgreSQL"], ["PostgreSQL"])
    assert len(subs) == 0

    # User selects PostgreSQL, architecture uses MongoDB — substitution detected
    subs = find_substituted_technologies(["PostgreSQL"], ["MongoDB"])
    assert len(subs) == 1


# ============================================================
# Test 6: Duplicate technologies
# ============================================================
def test_duplicate_technologies():
    from app.utils.tech_normalizer import normalize_tech_list

    # Duplicate entries should normalize to single entry
    techs = ["React", "react", "REACT", "React "]
    norm = normalize_tech_list(techs)
    assert len(norm) == 1


# ============================================================
# Test 7: Technology replacement
# ============================================================
def test_technology_replacement():
    """User replaces Django with FastAPI — latest decision wins."""
    from app.models.project import ProjectState, UserSelectedTechnology

    project = ProjectState(
        name="App",
        description="App.",
        problem="Problem.",
        target_users=["Users"],
        core_features=["Feature"],
        technologies=["FastAPI"],  # User switched from Django to FastAPI
        user_selected_technologies=[
            UserSelectedTechnology(name="FastAPI", purpose="backend", category="BACKEND_FRAMEWORK"),
        ],
    )

    # Django should NOT be in user_selected_technologies
    ust_names = {t.name for t in project.user_selected_technologies}
    assert "Django" not in ust_names
    assert "FastAPI" in ust_names


# ============================================================
# Test 8: Empty architecture
# ============================================================
def test_empty_architecture():
    from app.models.project import ProjectState
    from app.models.architecture import ArchitectureDocument
    from app.models.context import ImplementationContext, ImplementationPhase, AgentRule
    from app.models.requirements import RequirementsDocument, Requirement
    from app.engines.agent_readiness import check_agent_readiness

    project = ProjectState(
        name="Empty", description="Empty.", problem="Problem.",
        target_users=["Users"], core_features=["Feature"],
    )
    reqs = RequirementsDocument(
        functional_requirements=[
            Requirement(id="FR-001", title="Feature", description="F", priority="MUST_HAVE"),
        ],
    )
    arch = ArchitectureDocument(
        system_architecture="",
        components=[],
        technology_stack=[],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )
    ctx = ImplementationContext(
        project_title="Empty", project_summary="Empty.", problem="Problem.",
        target_users=["Users"],
        functional_requirements=["FR-001: Feature"],
        non_functional_requirements=[],
        architecture_summary="",
        technology_stack=[],
        data_model=[], api_contract=[], security_requirements=[],
        implementation_phases=[],
        agent_rules=[],
        definition_of_done=[],
    )

    result = check_agent_readiness(project, reqs, arch, ctx)
    # Should produce warnings, not crash
    assert result.score >= 0
    assert len(result.warnings) > 0


# ============================================================
# Test 9: Validation with missing sections
# ============================================================
def test_validation_missing_sections():
    from app.models.project import ProjectState
    from app.models.architecture import ArchitectureDocument
    from app.models.context import ImplementationContext
    from app.models.requirements import RequirementsDocument, Requirement
    from app.engines.validation import validate_context

    project = ProjectState(
        name="Sparse", description="Sparse.", problem="Problem.",
        target_users=["Users"], core_features=["Feature"],
    )
    reqs = RequirementsDocument(
        functional_requirements=[
            Requirement(id="FR-001", title="Feature", description="F", priority="MUST_HAVE"),
        ],
    )
    arch = ArchitectureDocument(
        system_architecture="Minimal.", components=[], technology_stack=[],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )
    ctx = ImplementationContext(
        project_title="", project_summary="", problem="",
        target_users=[],
        functional_requirements=[],
        non_functional_requirements=[],
        architecture_summary="",
        technology_stack=[],
        data_model=[], api_contract=[], security_requirements=[],
        implementation_phases=[],
        agent_rules=[],
        definition_of_done=[],
    )

    result = validate_context(project, reqs, arch, context=ctx)
    # Should produce many issues, not crash
    assert not result.valid
    assert result.score < 80
    assert len(result.issues) > 0


# ============================================================
# Test 10: Multiple projects sequentially
# ============================================================
def test_sequential_projects():
    """Process multiple projects one after another — no state leakage."""
    from app.models.project import ProjectState, UserSelectedTechnology
    from app.models.architecture import ArchitectureDocument, TechnologyChoice
    from app.models.context import ImplementationContext, ImplementationPhase, AgentRule
    from app.models.requirements import RequirementsDocument, Requirement
    from app.engines.agent_readiness import check_agent_readiness

    projects = [
        {
            "name": "Project A",
            "techs": ["React", "Node.js", "PostgreSQL"],
            "ust": [
                UserSelectedTechnology(name="React", purpose="frontend", category="FRONTEND_FRAMEWORK"),
            ],
        },
        {
            "name": "Project B",
            "techs": ["Django", "PostgreSQL", "Redis"],
            "ust": [
                UserSelectedTechnology(name="Django", purpose="backend", category="BACKEND_FRAMEWORK"),
            ],
        },
        {
            "name": "Project C",
            "techs": ["Flutter", "Dart", "Firebase"],
            "ust": [
                UserSelectedTechnology(name="Flutter", purpose="mobile", category="FRONTEND_FRAMEWORK"),
            ],
        },
    ]

    for p in projects:
        project = ProjectState(
            name=p["name"],
            description=f"{p['name']} description.",
            problem="Problem.",
            target_users=["Users"],
            core_features=["Feature"],
            technologies=p["techs"],
            user_selected_technologies=p["ust"],
        )

        reqs = RequirementsDocument(
            functional_requirements=[
                Requirement(id="FR-001", title="Feature", description="F", priority="MUST_HAVE"),
            ],
        )

        arch = ArchitectureDocument(
            system_architecture=f"{p['name']} architecture.",
            components=[],
            technology_stack=[
                TechnologyChoice(category="Main", technology=t, reason="User")
                for t in p["techs"]
            ],
            data_architecture=[], api_design=[], security=[], deployment=[],
        )

        ctx = ImplementationContext(
            project_title=p["name"], project_summary=f"{p['name']} summary.",
            problem="Problem.", target_users=["Users"],
            functional_requirements=["FR-001: Feature"],
            non_functional_requirements=[],
            architecture_summary=f"{p['name']} arch.",
            technology_stack=p["techs"],
            data_model=[], api_contract=[], security_requirements=[],
            implementation_phases=[ImplementationPhase(phase=1, name="F", objective="Setup", tasks=["Setup"], deliverables=["App"])],
            agent_rules=[AgentRule(category="Architecture", rule="Simple"), AgentRule(category="Security", rule="JWT"), AgentRule(category="Testing", rule="Tests")],
            definition_of_done=["Done"],
        )

        result = check_agent_readiness(project, reqs, arch, ctx)

        # Each project should have its own tech in the results
        ust_names = {t.name for t in project.user_selected_technologies}
        assert p["ust"][0].name in ust_names

        # No cross-contamination: techs UNIQUE to other projects should not appear
        # (shared techs like PostgreSQL are OK)
        my_techs = set(t.lower() for t in p["techs"])
        for other in projects:
            if other["name"] != p["name"]:
                other_unique = set(t.lower() for t in other["techs"]) - my_techs
                arch_techs = {tc.technology.lower() for tc in arch.technology_stack}
                leaked = arch_techs & other_unique
                assert len(leaked) == 0, (
                    f"Project {p['name']} has techs unique to {other['name']}: {leaked}"
                )


# ============================================================
# Test 11: Technology not in lookup table
# ============================================================
def test_unknown_technology():
    """Unknown technologies should be classified as OTHER, not rejected."""
    from app.utils.tech_normalizer import classify_tech, normalize_tech_name

    # Unknown technology
    cat = classify_tech("Bun")
    assert cat == "OTHER"  # Not in lookup table

    # But it should still be normalizable
    norm = normalize_tech_name("Bun")
    assert norm == "bun"  # Can be normalized


# ============================================================
# Test 12: Quality gate with empty context
# ============================================================
def test_quality_gate_empty():
    from app.models.project import ProjectState
    from app.models.architecture import ArchitectureDocument
    from app.models.context import ImplementationContext
    from app.models.requirements import RequirementsDocument, Requirement
    from app.services.quality_gate import run_quality_gate

    project = ProjectState(
        name="Empty", description="Empty.", problem="Problem.",
        target_users=["Users"], core_features=["Feature"],
    )
    reqs = RequirementsDocument(
        functional_requirements=[
            Requirement(id="FR-001", title="Feature", description="F", priority="MUST_HAVE"),
        ],
    )
    arch = ArchitectureDocument(
        system_architecture="Empty.", components=[], technology_stack=[],
        data_architecture=[], api_design=[], security=[], deployment=[],
    )
    ctx = ImplementationContext(
        project_title="", project_summary="", problem="",
        target_users=[], functional_requirements=[],
        non_functional_requirements=[], architecture_summary="",
        technology_stack=[], data_model=[], api_contract=[],
        security_requirements=[], implementation_phases=[],
        agent_rules=[], definition_of_done=[],
    )

    result = run_quality_gate(project, reqs, arch, ctx)
    # Should produce a low score, not crash
    assert result.overall_score >= 0
    assert result.overall_score < 80
    assert not result.ready_for_agent


# ============================================================
# Test 13: find_missing_fields edge cases
# ============================================================
def test_missing_fields_edge_cases():
    from app.models.project import ProjectState
    from app.engines.discovery import find_missing_fields

    # All fields empty
    project = ProjectState()
    missing = find_missing_fields(project)
    assert len(missing) > 0
    assert "name" in missing

    # Only name provided
    project = ProjectState(name="Test")
    missing = find_missing_fields(project)
    assert "name" not in missing
    assert "description" in missing

    # Empty list fields count as missing
    project = ProjectState(
        name="Test", description="Test.", problem="Test.",
        target_users=[], core_features=[],
    )
    missing = find_missing_fields(project)
    assert "target_users" in missing
    assert "core_features" in missing


# ============================================================
# Test 14: Assembly with invalid context
# ============================================================
def test_assembly_rejects_invalid():
    from app.models.context import ImplementationContext
    from app.models.validation import ContextValidationResult
    from app.engines.assembly import assemble_markdown

    ctx = ImplementationContext(
        project_title="Test", project_summary="Test.", problem="Test.",
        target_users=["Users"], functional_requirements=["FR-001"],
        non_functional_requirements=[], architecture_summary="Test.",
        technology_stack=["React"], data_model=[], api_contract=[],
        security_requirements=[], implementation_phases=[],
        agent_rules=[], definition_of_done=[],
    )

    validation = ContextValidationResult(valid=False, score=50, issues=[])

    try:
        assemble_markdown(context=ctx, validation=validation)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "invalid" in str(e).lower()


# ============================================================
# Test 15: Artifact creation with invalid context
# ============================================================
def test_artifact_rejects_invalid():
    from app.models.context import ImplementationContext
    from app.models.validation import ContextValidationResult
    from app.engines.artifact import create_artifact

    ctx = ImplementationContext(
        project_title="Test", project_summary="Test.", problem="Test.",
        target_users=["Users"], functional_requirements=["FR-001"],
        non_functional_requirements=[], architecture_summary="Test.",
        technology_stack=["React"], data_model=[], api_contract=[],
        security_requirements=[], implementation_phases=[],
        agent_rules=[], definition_of_done=[],
    )

    validation = ContextValidationResult(valid=False, score=50, issues=[])

    try:
        create_artifact(context=ctx, validation=validation)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "invalid" in str(e).lower()


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    tests = [
        ("Empty project description", test_empty_description),
        ("No user-selected technologies", test_no_user_selected_techs),
        ("Many technologies", test_many_technologies),
        ("Conflicting technologies", test_conflicting_technologies),
        ("Rejected alternatives", test_rejected_alternatives),
        ("Duplicate technologies", test_duplicate_technologies),
        ("Technology replacement", test_technology_replacement),
        ("Empty architecture", test_empty_architecture),
        ("Validation missing sections", test_validation_missing_sections),
        ("Multiple projects sequentially", test_sequential_projects),
        ("Unknown technology", test_unknown_technology),
        ("Quality gate empty", test_quality_gate_empty),
        ("Missing fields edge cases", test_missing_fields_edge_cases),
        ("Assembly rejects invalid", test_assembly_rejects_invalid),
        ("Artifact rejects invalid", test_artifact_rejects_invalid),
    ]

    print("=" * 60)
    print("EDGE CASE & ERROR HANDLING TESTS")
    print("=" * 60)

    results = []
    for name, func in tests:
        results.append(run_test(name, func))

    passed = sum(results)
    total = len(results)

    print(f"\n{'=' * 60}")
    print(f"RESULTS: {passed}/{total} passed")
    print(f"{'=' * 60}")

    if passed < total:
        sys.exit(1)
    else:
        print("ALL TESTS PASSED")
