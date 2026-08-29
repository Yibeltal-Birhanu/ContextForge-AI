"""
HealthLink Ethiopia regression test.

Verifies that user-selected technologies are:
1. Extracted and tracked during discovery
2. Preserved through the architecture engine
3. Preserved in the context engineering output
4. Detected when silently substituted
5. Reported correctly in the quality gate
"""

import asyncio
import json

from app.models.project import ProjectState, UserSelectedTechnology
from app.models.requirements import RequirementsDocument, Requirement, AcceptanceCriterion
from app.models.architecture import ArchitectureDocument, TechnologyChoice
from app.models.context import ImplementationContext, ImplementationPhase, AgentRule
from app.engines.agent_readiness import check_agent_readiness
from app.services.quality_gate import run_quality_gate
from app.utils.tech_normalizer import (
    classify_tech,
    find_substituted_technologies,
    normalize_tech_name,
)


# ============================================================
# Test 1: Technology category classification
# ============================================================

def test_classify_tech():
    print("=" * 60)
    print("TEST 1: Technology category classification")
    print("=" * 60)

    test_cases = [
        ("OpenAI API", "AI_PROVIDER"),
        ("Anthropic", "AI_PROVIDER"),
        ("TensorFlow", "AI_PROVIDER"),
        ("Telebirr", "PAYMENT_PROVIDER"),
        ("Stripe", "PAYMENT_PROVIDER"),
        ("Chapa", "PAYMENT_PROVIDER"),
        ("Africa's Talking", "SMS_PROVIDER"),
        ("Twilio", "SMS_PROVIDER"),
        ("Google Maps", "MAP_PROVIDER"),
        ("Mapbox", "MAP_PROVIDER"),
        ("PostgreSQL", "DATABASE"),
        ("MongoDB", "DATABASE"),
        ("AWS", "CLOUD_PROVIDER"),
        ("React", "FRONTEND_FRAMEWORK"),
        ("Next.js", "FRONTEND_FRAMEWORK"),
        ("Node.js", "BACKEND_FRAMEWORK"),
        ("FastAPI", "BACKEND_FRAMEWORK"),
        ("Docker", "HOSTING"),
    ]

    all_pass = True
    for tech, expected in test_cases:
        result = classify_tech(tech)
        status = "PASS" if result == expected else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"  {status}: {tech:25s} -> {result:25s} (expected: {expected})")

    print(f"\n  Result: {'ALL PASSED' if all_pass else 'SOME FAILED'}\n")
    return all_pass


# ============================================================
# Test 2: Silent substitution detection
# ============================================================

def test_substitution_detection():
    print("=" * 60)
    print("TEST 2: Silent substitution detection")
    print("=" * 60)

    user_techs = ["OpenAI API", "Google Maps", "Telebirr", "Africa's Talking"]

    # Architecture that correctly preserves them
    arch_correct = ["OpenAI API", "Google Maps", "Telebirr", "Africa's Talking", "PostgreSQL"]
    subs = find_substituted_technologies(user_techs, arch_correct)
    print(f"  Correct arch: {len(subs)} substitutions detected (expected: 0)")
    assert len(subs) == 0, "Should not detect substitutions when arch matches"

    # Architecture that silently substitutes
    arch_wrong = ["Amazon Bedrock", "Mapbox", "Stripe", "Twilio", "PostgreSQL"]
    subs = find_substituted_technologies(user_techs, arch_wrong)
    print(f"  Wrong arch: {len(subs)} substitutions detected (expected: 4)")
    for sub in subs:
        print(f"    {sub['category']}: {sub['user_techs']} -> {sub['arch_techs']}")
    assert len(subs) == 4, f"Expected 4 substitutions, got {len(subs)}"

    # Partial substitution
    arch_partial = ["OpenAI API", "Mapbox", "Telebirr", "Africa's Talking"]
    subs = find_substituted_technologies(user_techs, arch_partial)
    print(f"  Partial arch: {len(subs)} substitutions detected (expected: 1)")
    assert len(subs) == 1, f"Expected 1 substitution, got {len(subs)}"

    print("\n  Result: ALL PASSED\n")
    return True


# ============================================================
# Test 3: Agent readiness with correct architecture
# ============================================================

def test_readiness_correct_arch():
    print("=" * 60)
    print("TEST 3: Agent readiness — correct architecture (all preserved)")
    print("=" * 60)

    project = ProjectState(
        name="HealthLink Ethiopia",
        description="A health platform connecting patients with clinics.",
        problem="Patients in Ethiopia struggle to find and access healthcare.",
        target_users=["Patients", "Clinics", "Admins"],
        core_features=[
            "Patient registration",
            "Clinic search with maps",
            "AI health guidance",
            "Appointment booking",
            "SMS reminders",
            "Telebirr payments",
        ],
        platform="Web and mobile",
        technologies=["React", "Node.js"],
        user_selected_technologies=[
            UserSelectedTechnology(name="OpenAI API", purpose="AI-assisted health guidance", category="AI_PROVIDER"),
            UserSelectedTechnology(name="Google Maps", purpose="clinic and hospital locations", category="MAP_PROVIDER"),
            UserSelectedTechnology(name="Telebirr", purpose="online payments", category="PAYMENT_PROVIDER"),
            UserSelectedTechnology(name="Africa's Talking", purpose="SMS reminders", category="SMS_PROVIDER"),
            UserSelectedTechnology(name="PostgreSQL", purpose="primary database", category="DATABASE"),
            UserSelectedTechnology(name="AWS", purpose="cloud hosting", category="CLOUD_PROVIDER"),
        ],
        database="PostgreSQL",
        authentication="Email and password with JWT",
        integrations=["Telebirr payments", "Africa's Talking SMS", "Google Maps", "OpenAI API"],
        constraints=["Low budget", "Must work in Ethiopia"],
        deployment="Cloud hosting on AWS",
    )

    requirements = RequirementsDocument(
        functional_requirements=[
            Requirement(id="FR-001", title="Patient Registration", description="Patients can register accounts.", priority="MUST_HAVE", actors=["Patient"], acceptance_criteria=[AcceptanceCriterion(description="Patient can create account")]),
            Requirement(id="FR-002", title="Clinic Search with Maps", description="Patients can find clinics on a map.", priority="MUST_HAVE", actors=["Patient"], acceptance_criteria=[AcceptanceCriterion(description="Map displays clinic locations")]),
            Requirement(id="FR-003", title="AI Health Guidance", description="Patients get AI-assisted health advice.", priority="MUST_HAVE", actors=["Patient"], acceptance_criteria=[AcceptanceCriterion(description="AI provides health guidance")]),
            Requirement(id="FR-004", title="SMS Reminders", description="Patients receive appointment reminders via SMS.", priority="MUST_HAVE", actors=["Patient"], acceptance_criteria=[AcceptanceCriterion(description="SMS sent before appointment")]),
            Requirement(id="FR-005", title="Telebirr Payments", description="Patients pay via Telebirr.", priority="MUST_HAVE", actors=["Patient"], acceptance_criteria=[AcceptanceCriterion(description="Payment processed via Telebirr")]),
        ],
    )

    # Architecture that CORRECTLY preserves all user-selected techs
    architecture = ArchitectureDocument(
        system_architecture="Client-server architecture with React frontend, Node.js backend, and external service integrations.",
        components=[],
        technology_stack=[
            TechnologyChoice(category="Frontend", technology="React", reason="User specified"),
            TechnologyChoice(category="Backend", technology="Node.js", reason="User specified"),
            TechnologyChoice(category="AI Provider", technology="OpenAI API", reason="User selected for health guidance"),
            TechnologyChoice(category="Maps", technology="Google Maps", reason="User selected for clinic locations"),
            TechnologyChoice(category="Payments", technology="Telebirr", reason="User selected for payments"),
            TechnologyChoice(category="SMS", technology="Africa's Talking", reason="User selected for SMS reminders"),
            TechnologyChoice(category="Database", technology="PostgreSQL", reason="User selected"),
            TechnologyChoice(category="Cloud", technology="AWS", reason="User selected"),
        ],
        data_architecture=[],
        api_design=[],
        security=[],
        deployment=[],
    )

    context = ImplementationContext(
        project_title="HealthLink Ethiopia",
        project_summary="A health platform connecting patients with clinics.",
        problem="Patients struggle to access healthcare.",
        target_users=["Patients", "Clinics", "Admins"],
        functional_requirements=[
            "FR-001: Patient Registration",
            "FR-002: Clinic Search with Maps",
            "FR-003: AI Health Guidance",
            "FR-004: SMS Reminders",
            "FR-005: Telebirr Payments",
        ],
        non_functional_requirements=["NFR-001: Security"],
        architecture_summary="React + Node.js with OpenAI, Google Maps, Telebirr, Africa's Talking.",
        technology_stack=[
            "React - Frontend",
            "Node.js - Backend",
            "OpenAI API - AI health guidance",
            "Google Maps - Clinic locations",
            "Telebirr - Payments",
            "Africa's Talking - SMS",
            "PostgreSQL - Database",
            "AWS - Hosting",
        ],
        data_model=["Patient", "Clinic", "Appointment", "Payment"],
        api_contract=["POST /api/patients", "GET /api/clinics", "POST /api/guidance"],
        security_requirements=["JWT authentication", "Encrypted health data"],
        implementation_phases=[
            ImplementationPhase(phase=1, name="Foundation", objective="Setup", tasks=["Setup project"], deliverables=["Working app"]),
        ],
        agent_rules=[
            AgentRule(category="Architecture", rule="Modular monolith"),
            AgentRule(category="Security", rule="JWT tokens"),
            AgentRule(category="Testing", rule="Write tests"),
        ],
        definition_of_done=["All features implemented", "Tests passing"],
    )

    result = check_agent_readiness(project, requirements, architecture, context)

    print(f"  Ready: {result.ready}")
    print(f"  Score: {result.score}")
    print(f"  Technology consistency: {result.checks.technology_consistency}%")
    print(f"  Warnings: {len(result.warnings)}")

    # Check no substitution warnings
    sub_warnings = [w for w in result.warnings if "substitut" in w.message.lower() or "replace" in w.message.lower() or "CONTRADICTION" in w.message]
    print(f"  Substitution warnings: {len(sub_warnings)} (expected: 0)")
    for w in sub_warnings:
        print(f"    {w.message}")

    assert result.checks.technology_consistency >= 90, f"Tech consistency should be >= 90%, got {result.checks.technology_consistency}%"
    assert len(sub_warnings) == 0, f"Expected 0 substitution warnings, got {len(sub_warnings)}"

    print("\n  Result: PASSED\n")
    return True


# ============================================================
# Test 4: Agent readiness with SUBSTITUTED architecture
# ============================================================

def test_readiness_wrong_arch():
    print("=" * 60)
    print("TEST 4: Agent readiness — WRONG architecture (substitutions)")
    print("=" * 60)

    project = ProjectState(
        name="HealthLink Ethiopia",
        description="A health platform connecting patients with clinics.",
        problem="Patients in Ethiopia struggle to find and access healthcare.",
        target_users=["Patients", "Clinics"],
        core_features=["Patient registration", "Clinic search", "AI health guidance", "SMS reminders", "Telebirr payments"],
        platform="Web and mobile",
        technologies=["React", "Node.js"],
        user_selected_technologies=[
            UserSelectedTechnology(name="OpenAI API", purpose="AI-assisted health guidance", category="AI_PROVIDER"),
            UserSelectedTechnology(name="Google Maps", purpose="clinic locations", category="MAP_PROVIDER"),
            UserSelectedTechnology(name="Telebirr", purpose="online payments", category="PAYMENT_PROVIDER"),
            UserSelectedTechnology(name="Africa's Talking", purpose="SMS reminders", category="SMS_PROVIDER"),
        ],
        database="PostgreSQL",
        authentication="JWT",
        integrations=["Telebirr", "Africa's Talking", "Google Maps", "OpenAI API"],
        deployment="AWS",
    )

    requirements = RequirementsDocument(
        functional_requirements=[
            Requirement(id="FR-001", title="AI Health Guidance", description="AI guidance.", priority="MUST_HAVE"),
            Requirement(id="FR-002", title="Clinic Maps", description="Map display.", priority="MUST_HAVE"),
            Requirement(id="FR-003", title="SMS Reminders", description="SMS.", priority="MUST_HAVE"),
            Requirement(id="FR-004", title="Telebirr Payments", description="Payments.", priority="MUST_HAVE"),
        ],
    )

    # Architecture that SILENTLY SUBSTITUTES user technologies
    architecture = ArchitectureDocument(
        system_architecture="Client-server with React and Node.js.",
        components=[],
        technology_stack=[
            TechnologyChoice(category="Frontend", technology="React", reason="Standard"),
            TechnologyChoice(category="Backend", technology="Node.js", reason="Standard"),
            TechnologyChoice(category="AI Provider", technology="Amazon Bedrock", reason="AI chose this"),
            TechnologyChoice(category="Maps", technology="Mapbox", reason="AI chose this"),
            TechnologyChoice(category="Payments", technology="Stripe", reason="AI chose this"),
            TechnologyChoice(category="SMS", technology="Twilio", reason="AI chose this"),
            TechnologyChoice(category="Database", technology="PostgreSQL", reason="Standard"),
        ],
        data_architecture=[],
        api_design=[],
        security=[],
        deployment=[],
    )

    context = ImplementationContext(
        project_title="HealthLink Ethiopia",
        project_summary="Health platform.",
        problem="Healthcare access.",
        target_users=["Patients"],
        functional_requirements=["FR-001: AI Health", "FR-002: Maps", "FR-003: SMS", "FR-004: Payments"],
        non_functional_requirements=[],
        architecture_summary="React + Node.js backend.",
        technology_stack=["React", "Node.js", "Amazon Bedrock", "Mapbox", "Stripe", "Twilio", "PostgreSQL"],
        data_model=["Patient", "Clinic"],
        api_contract=["POST /api/guidance"],
        security_requirements=["JWT"],
        implementation_phases=[ImplementationPhase(phase=1, name="Foundation", objective="Setup", tasks=["Setup"], deliverables=["App"])],
        agent_rules=[AgentRule(category="Architecture", rule="Monolith")],
        definition_of_done=["Done"],
    )

    result = check_agent_readiness(project, requirements, architecture, context)

    print(f"  Ready: {result.ready}")
    print(f"  Score: {result.score}")
    print(f"  Technology consistency: {result.checks.technology_consistency}%")

    # Should detect substitution warnings
    sub_warnings = [w for w in result.warnings if "substitut" in w.message.lower() or "replace" in w.message.lower() or "CONTRADICTION" in w.message]
    print(f"  Substitution warnings: {len(sub_warnings)} (expected: >= 4)")
    for w in sub_warnings:
        print(f"    {w.message}")

    assert len(sub_warnings) >= 4, f"Expected >= 4 substitution warnings, got {len(sub_warnings)}"
    assert result.checks.technology_consistency < 80, f"Tech consistency should be < 80% due to substitutions, got {result.checks.technology_consistency}%"

    print("\n  Result: PASSED (correctly detected substitutions)\n")
    return True


# ============================================================
# Test 5: Full quality gate with correct architecture
# ============================================================

def test_quality_gate_correct():
    print("=" * 60)
    print("TEST 5: Full quality gate — correct architecture")
    print("=" * 60)

    project = ProjectState(
        name="HealthLink Ethiopia",
        description="Health platform.",
        problem="Healthcare access.",
        target_users=["Patients"],
        core_features=["AI guidance", "Maps", "SMS"],
        user_selected_technologies=[
            UserSelectedTechnology(name="OpenAI API", purpose="AI guidance", category="AI_PROVIDER"),
            UserSelectedTechnology(name="Google Maps", purpose="locations", category="MAP_PROVIDER"),
            UserSelectedTechnology(name="Telebirr", purpose="payments", category="PAYMENT_PROVIDER"),
            UserSelectedTechnology(name="Africa's Talking", purpose="SMS", category="SMS_PROVIDER"),
        ],
    )

    requirements = RequirementsDocument(
        functional_requirements=[
            Requirement(id="FR-001", title="AI Guidance", description="AI health.", priority="MUST_HAVE"),
            Requirement(id="FR-002", title="Maps", description="Clinic maps.", priority="MUST_HAVE"),
        ],
    )

    architecture = ArchitectureDocument(
        system_architecture="Client-server.",
        components=[],
        technology_stack=[
            TechnologyChoice(category="AI", technology="OpenAI API", reason="User selected"),
            TechnologyChoice(category="Maps", technology="Google Maps", reason="User selected"),
            TechnologyChoice(category="Payments", technology="Telebirr", reason="User selected"),
            TechnologyChoice(category="SMS", technology="Africa's Talking", reason="User selected"),
        ],
        data_architecture=[],
        api_design=[],
        security=[],
        deployment=[],
    )

    context = ImplementationContext(
        project_title="HealthLink Ethiopia",
        project_summary="Health platform.",
        problem="Healthcare.",
        target_users=["Patients"],
        functional_requirements=["FR-001: AI", "FR-002: Maps"],
        non_functional_requirements=[],
        architecture_summary="With OpenAI, Google Maps, Telebirr, Africa's Talking.",
        technology_stack=["OpenAI API", "Google Maps", "Telebirr", "Africa's Talking", "PostgreSQL", "React", "Node.js"],
        data_model=["Patient"],
        api_contract=["POST /api/guidance"],
        security_requirements=["JWT"],
        implementation_phases=[ImplementationPhase(phase=1, name="F", objective="Setup", tasks=["Setup"], deliverables=["App"])],
        agent_rules=[
            AgentRule(category="Architecture", rule="Monolith"),
            AgentRule(category="Security", rule="JWT"),
            AgentRule(category="Testing", rule="Write tests"),
        ],
        definition_of_done=["Complete"],
    )

    result = run_quality_gate(project, requirements, architecture, context)

    print(f"  Passed: {result.passed}")
    print(f"  Overall: {result.overall_score}")
    print(f"  Tech preservation:")
    tp = result.tech_preservation
    print(f"    User-selected: {tp.user_selected_count}")
    print(f"    Preserved: {tp.preserved_count} -> {tp.preserved}")
    print(f"    Missing: {tp.missing_count} -> {tp.missing}")
    print(f"    Substituted: {tp.substituted_count}")

    assert tp.preserved_count == 4, f"Expected 4 preserved, got {tp.preserved_count}"
    assert tp.substituted_count == 0, f"Expected 0 substituted, got {tp.substituted_count}"

    print("\n  Result: PASSED\n")
    return True


# ============================================================
# Test 6: Full quality gate with WRONG architecture
# ============================================================

def test_quality_gate_wrong():
    print("=" * 60)
    print("TEST 6: Full quality gate — WRONG architecture")
    print("=" * 60)

    project = ProjectState(
        name="HealthLink Ethiopia",
        description="Health platform.",
        problem="Healthcare access.",
        target_users=["Patients"],
        core_features=["AI guidance", "Maps", "SMS"],
        user_selected_technologies=[
            UserSelectedTechnology(name="OpenAI API", purpose="AI guidance", category="AI_PROVIDER"),
            UserSelectedTechnology(name="Google Maps", purpose="locations", category="MAP_PROVIDER"),
            UserSelectedTechnology(name="Telebirr", purpose="payments", category="PAYMENT_PROVIDER"),
            UserSelectedTechnology(name="Africa's Talking", purpose="SMS", category="SMS_PROVIDER"),
        ],
    )

    requirements = RequirementsDocument(
        functional_requirements=[
            Requirement(id="FR-001", title="AI Guidance", description="AI health.", priority="MUST_HAVE"),
        ],
    )

    architecture = ArchitectureDocument(
        system_architecture="Client-server.",
        components=[],
        technology_stack=[
            TechnologyChoice(category="AI", technology="Amazon Bedrock", reason="AI chose"),
            TechnologyChoice(category="Maps", technology="Mapbox", reason="AI chose"),
            TechnologyChoice(category="Payments", technology="Stripe", reason="AI chose"),
            TechnologyChoice(category="SMS", technology="Twilio", reason="AI chose"),
        ],
        data_architecture=[],
        api_design=[],
        security=[],
        deployment=[],
    )

    context = ImplementationContext(
        project_title="HealthLink Ethiopia",
        project_summary="Health platform.",
        problem="Healthcare.",
        target_users=["Patients"],
        functional_requirements=["FR-001: AI"],
        non_functional_requirements=[],
        architecture_summary="With Bedrock, Mapbox, Stripe, Twilio.",
        technology_stack=["Amazon Bedrock", "Mapbox", "Stripe", "Twilio"],
        data_model=[],
        api_contract=[],
        security_requirements=[],
        implementation_phases=[],
        agent_rules=[],
        definition_of_done=[],
    )

    result = run_quality_gate(project, requirements, architecture, context)

    print(f"  Passed: {result.passed}")
    print(f"  Overall: {result.overall_score}")
    print(f"  Tech preservation:")
    tp = result.tech_preservation
    print(f"    User-selected: {tp.user_selected_count}")
    print(f"    Preserved: {tp.preserved_count} -> {tp.preserved}")
    print(f"    Missing: {tp.missing_count} -> {tp.missing}")
    print(f"    Substituted: {tp.substituted_count}")
    for sub in tp.substituted:
        print(f"      {sub['category']}: {sub['user_techs']} -> {sub['arch_techs']}")

    assert tp.substituted_count == 4, f"Expected 4 substitutions, got {tp.substituted_count}"
    assert tp.preserved_count == 0, f"Expected 0 preserved, got {tp.preserved_count}"

    print("\n  Result: PASSED (correctly detected all 4 substitutions)\n")
    return True


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    results = []
    results.append(("Classification", test_classify_tech()))
    results.append(("Substitution Detection", test_substitution_detection()))
    results.append(("Readiness - Correct Arch", test_readiness_correct_arch()))
    results.append(("Readiness - Wrong Arch", test_readiness_wrong_arch()))
    results.append(("Quality Gate - Correct", test_quality_gate_correct()))
    results.append(("Quality Gate - Wrong", test_quality_gate_wrong()))

    print("=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    all_pass = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(f"  {status}: {name}")

    print(f"\n{'ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED'}")
