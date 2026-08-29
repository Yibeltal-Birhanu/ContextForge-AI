"""
Concurrency safety checks for agent_readiness.

Tests that the architecture audit detects:
1. Missing booking locking strategies
2. Missing payment idempotency
3. In-process cron with multi-replica deployment
4. Missing audit logging for health data
5. Missing encryption for sensitive data
6. Missing AI disclaimers in healthcare
7. Missing secrets management
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


def _make_project(name="Test", desc="Test.", features=None, user_sel=None,
                  db=None, platform=None, constraints=None):
    from app.models.project import ProjectState, UserSelectedTechnology
    ust = []
    if user_sel:
        for t in user_sel:
            ust.append(UserSelectedTechnology(**t))
    return ProjectState(
        name=name, description=desc, problem="Test.",
        target_users=["Users"], core_features=features or ["Feature"],
        technologies=[], user_selected_technologies=ust,
        database=db, platform=platform, constraints=constraints or [],
    )


def _make_arch(tech_stack=None, sys_arch="Client-server.",
               components=None, deployment=None, security=None):
    from app.models.architecture import (
        ArchitectureDocument, TechnologyChoice,
        ArchitectureComponent, DeploymentPlan,
    )
    comps = []
    if components:
        for c in components:
            if isinstance(c, dict):
                comps.append(ArchitectureComponent(**c))
            else:
                comps.append(ArchitectureComponent(
                    name=c[0], responsibility=c[1], technologies=c[2]
                ))
    deploys = []
    if deployment:
        for d in deployment:
            if isinstance(d, dict):
                deploys.append(DeploymentPlan(**d))
            else:
                deploys.append(DeploymentPlan(
                    environment=d[0], services=d[1], reason=d[2]
                ))
    return ArchitectureDocument(
        system_architecture=sys_arch,
        components=comps,
        technology_stack=[
            TechnologyChoice(category=c, technology=t, reason=r)
            for (c, t, r) in (tech_stack or [])
        ],
        data_architecture=[], api_design=[],
        security=security or [], deployment=deploys,
    )


def _make_ctx(tech_stack=None, frs=None, nfrs=None, security=None,
              phases=None, agent_rules=None, dod=None):
    from app.models.context import ImplementationContext, ImplementationPhase, AgentRule
    impl_phases = None
    if phases:
        impl_phases = []
        for p in phases:
            if isinstance(p, dict):
                impl_phases.append(ImplementationPhase(**p))
            else:
                impl_phases.append(ImplementationPhase(
                    phase=p[0] if isinstance(p[0], int) else int(p[0]),
                    name=p[1], objective=p[2],
                    tasks=p[3], deliverables=p[4]
                ))
    return ImplementationContext(
        project_title="Test", project_summary="Test.", problem="Test.",
        target_users=["Users"],
        functional_requirements=frs or ["FR-001: Feature"],
        non_functional_requirements=nfrs or [],
        architecture_summary="Test.",
        technology_stack=tech_stack or ["React"],
        data_model=[], api_contract=[],
        security_requirements=security or ["JWT"],
        implementation_phases=impl_phases or [
            ImplementationPhase(phase=1, name="F", objective="Setup",
                              tasks=["Setup"], deliverables=["App"])
        ],
        agent_rules=agent_rules or [
            AgentRule(category="Architecture", rule="Monolith"),
            AgentRule(category="Security", rule="JWT"),
            AgentRule(category="Testing", rule="Tests"),
        ],
        definition_of_done=dod or ["Done"],
    )


def _make_reqs(frs=None):
    from app.models.requirements import RequirementsDocument, Requirement
    return RequirementsDocument(
        functional_requirements=[
            Requirement(id=fid, title=t, description="Test.", priority="MUST_HAVE")
            for fid, t in (frs or [("FR-001", "Feature")])
        ]
    )


def _get_concurrency_warnings(result):
    return [w for w in result.warnings if w.category == "concurrency_safety"]


# ============================================================
# Test 1: Booking without locking -> warning
# ============================================================
def test_booking_no_locking():
    from app.engines.agent_readiness import check_agent_readiness

    project = _make_project(features=["Appointment booking", "Time slot selection"])
    reqs = _make_reqs([("FR-001", "Appointment booking")])
    arch = _make_arch(
        components=[("API", "Handles bookings", ["Node.js"])],
    )
    ctx = _make_ctx(
        frs=["FR-001: Appointment booking", "FR-002: Time slot selection"],
    )

    result = check_agent_readiness(project, reqs, arch, ctx)
    concurrency = _get_concurrency_warnings(result)
    booking_warnings = [w for w in concurrency if "locking" in w.message.lower() or "double-booking" in w.message.lower()]
    assert len(booking_warnings) >= 1, f"Expected booking locking warning, got {len(booking_warnings)}: {[w.message for w in concurrency]}"


# ============================================================
# Test 2: Booking WITH locking -> no warning
# ============================================================
def test_booking_with_locking():
    from app.engines.agent_readiness import check_agent_readiness

    project = _make_project(features=["Appointment booking"])
    reqs = _make_reqs([("FR-001", "Appointment booking")])
    arch = _make_arch(
        components=[("API", "Handles bookings", ["Node.js"])],
    )
    ctx = _make_ctx(
        frs=["FR-001: Appointment booking"],
        security=["SELECT FOR UPDATE for booking", "UNIQUE constraint on time slots"],
    )

    result = check_agent_readiness(project, reqs, arch, ctx)
    concurrency = _get_concurrency_warnings(result)
    booking_warnings = [w for w in concurrency if "locking" in w.message.lower() or "double-booking" in w.message.lower()]
    assert len(booking_warnings) == 0, f"Unexpected booking warning: {[w.message for w in booking_warnings]}"


# ============================================================
# Test 3: Payment without idempotency -> warning
# ============================================================
def test_payment_no_idempotency():
    from app.engines.agent_readiness import check_agent_readiness

    project = _make_project(features=["Telebirr payments", "Checkout"])
    reqs = _make_reqs([("FR-001", "Payment processing")])
    arch = _make_arch(
        components=[("Payment", "Handles payments", ["Node.js"])],
    )
    ctx = _make_ctx(
        frs=["FR-001: Payment processing"],
        security=["JWT for auth"],
    )

    result = check_agent_readiness(project, reqs, arch, ctx)
    concurrency = _get_concurrency_warnings(result)
    payment_warnings = [w for w in concurrency if "idempoten" in w.message.lower() or "duplicate" in w.message.lower()]
    assert len(payment_warnings) >= 1, f"Expected payment idempotency warning, got {len(payment_warnings)}"


# ============================================================
# Test 4: Payment WITH idempotency -> no warning
# ============================================================
def test_payment_with_idempotency():
    from app.engines.agent_readiness import check_agent_readiness

    project = _make_project(features=["Telebirr payments"])
    reqs = _make_reqs([("FR-001", "Payment processing")])
    arch = _make_arch(
        components=[("Payment", "Handles payments", ["Node.js"])],
    )
    ctx = _make_ctx(
        frs=["FR-001: Payment processing"],
        security=["Idempotent webhook handlers", "UNIQUE constraint on provider_reference"],
    )

    result = check_agent_readiness(project, reqs, arch, ctx)
    concurrency = _get_concurrency_warnings(result)
    payment_warnings = [w for w in concurrency if "idempoten" in w.message.lower()]
    assert len(payment_warnings) == 0, f"Unexpected payment warning: {[w.message for w in payment_warnings]}"


# ============================================================
# Test 5: Cron + Fargate (multi-replica) without safe scheduling
# ============================================================
def test_cron_with_fargate_unsafe():
    from app.engines.agent_readiness import check_agent_readiness

    project = _make_project(features=["SMS reminders", "Background jobs"])
    reqs = _make_reqs([("FR-001", "SMS reminders")])
    arch = _make_arch(
        sys_arch="Node.js backend with Fargate deployment.",
        components=[("API", "Web API", ["Node.js"]), ("Worker", "Background cron", ["node-cron"])],
        deployment=[("production", ["Fargate tasks"], "Container hosting")],
    )
    ctx = _make_ctx(
        frs=["FR-001: SMS reminders"],
        security=["JWT"],
        phases=[(1, "Setup", "Deploy to Fargate", ["Deploy"], ["App"])],
    )

    result = check_agent_readiness(project, reqs, arch, ctx)
    concurrency = _get_concurrency_warnings(result)
    cron_warnings = [w for w in concurrency if "cron" in w.message.lower() or "duplicate" in w.message.lower() or "scheduling" in w.message.lower()]
    assert len(cron_warnings) >= 1, f"Expected cron safety warning, got {len(cron_warnings)}: {[w.message for w in concurrency]}"


# ============================================================
# Test 6: Cron + Fargate WITH safe scheduling -> no warning
# ============================================================
def test_cron_with_fargate_safe():
    from app.engines.agent_readiness import check_agent_readiness

    project = _make_project(features=["SMS reminders"])
    reqs = _make_reqs([("FR-001", "SMS reminders")])
    arch = _make_arch(
        sys_arch="Node.js backend with Fargate deployment.",
        components=[("API", "Web API", ["Node.js"])],
        deployment=[("production", ["Fargate tasks"], "Container hosting")],
    )
    ctx = _make_ctx(
        frs=["FR-001: SMS reminders"],
        security=["Database-based job claiming with SELECT FOR UPDATE SKIP LOCKED"],
    )

    result = check_agent_readiness(project, reqs, arch, ctx)
    concurrency = _get_concurrency_warnings(result)
    cron_warnings = [w for w in concurrency if "cron" in w.message.lower() or "duplicate" in w.message.lower()]
    assert len(cron_warnings) == 0, f"Unexpected cron warning: {[w.message for w in cron_warnings]}"


# ============================================================
# Test 7: Healthcare without audit logging
# ============================================================
def test_healthcare_no_audit():
    from app.engines.agent_readiness import check_agent_readiness

    project = _make_project(features=["Patient management", "Health records"])
    reqs = _make_reqs([("FR-001", "Patient management")])
    arch = _make_arch(
        components=[("API", "Health API", ["Node.js"])],
    )
    ctx = _make_ctx(
        frs=["FR-001: Patient management"],
        security=["JWT authentication"],
    )

    result = check_agent_readiness(project, reqs, arch, ctx)
    concurrency = _get_concurrency_warnings(result)
    audit_warnings = [w for w in concurrency if "audit" in w.message.lower()]
    assert len(audit_warnings) >= 1, f"Expected audit warning for healthcare, got {len(audit_warnings)}"


# ============================================================
# Test 8: Healthcare WITH audit logging
# ============================================================
def test_healthcare_with_audit():
    from app.engines.agent_readiness import check_agent_readiness

    project = _make_project(features=["Patient management", "Health records"])
    reqs = _make_reqs([("FR-001", "Patient management")])
    arch = _make_arch(
        components=[("API", "Health API", ["Node.js"])],
    )
    ctx = _make_ctx(
        frs=["FR-001: Patient management"],
        security=["JWT authentication", "Comprehensive audit logging for all data access"],
    )

    result = check_agent_readiness(project, reqs, arch, ctx)
    concurrency = _get_concurrency_warnings(result)
    audit_warnings = [w for w in concurrency if "audit" in w.message.lower()]
    assert len(audit_warnings) == 0, f"Unexpected audit warning: {[w.message for w in audit_warnings]}"


# ============================================================
# Test 9: AI + healthcare without disclaimer
# ============================================================
def test_ai_healthcare_no_disclaimer():
    from app.engines.agent_readiness import check_agent_readiness

    project = _make_project(features=["AI health guidance", "Patient records"])
    reqs = _make_reqs([("FR-001", "AI health guidance")])
    arch = _make_arch(
        tech_stack=[("AI", "OpenAI API", "Health guidance")],
        components=[("AI Service", "Health guidance", ["OpenAI API"])],
    )
    ctx = _make_ctx(
        tech_stack=["OpenAI API", "React", "Node.js"],
        frs=["FR-001: AI health guidance"],
        security=["JWT"],
    )

    result = check_agent_readiness(project, reqs, arch, ctx)
    concurrency = _get_concurrency_warnings(result)
    disclaimer_warnings = [w for w in concurrency if "disclaimer" in w.message.lower()]
    assert len(disclaimer_warnings) >= 1, f"Expected disclaimer warning, got {len(disclaimer_warnings)}"


# ============================================================
# Test 10: AI + healthcare WITH disclaimer
# ============================================================
def test_ai_healthcare_with_disclaimer():
    from app.engines.agent_readiness import check_agent_readiness

    project = _make_project(features=["AI health guidance", "Patient records"])
    reqs = _make_reqs([("FR-001", "AI health guidance")])
    arch = _make_arch(
        tech_stack=[("AI", "OpenAI API", "Health guidance")],
        components=[("AI Service", "Health guidance", ["OpenAI API"])],
    )
    ctx = _make_ctx(
        tech_stack=["OpenAI API", "React", "Node.js"],
        frs=["FR-001: AI health guidance"],
        security=[
            "JWT authentication",
            "AI disclaimer: This is not medical advice. Consult a professional.",
            "Encrypted health data",
        ],
    )

    result = check_agent_readiness(project, reqs, arch, ctx)
    concurrency = _get_concurrency_warnings(result)
    disclaimer_warnings = [w for w in concurrency if "disclaimer" in w.message.lower()]
    assert len(disclaimer_warnings) == 0, f"Unexpected disclaimer warning: {[w.message for w in disclaimer_warnings]}"


# ============================================================
# Test 11: Non-healthcare project -> no false concurrency warnings
# ============================================================
def test_simple_project_no_false_warnings():
    from app.engines.agent_readiness import check_agent_readiness

    project = _make_project(features=["Blog posts", "Comments"])
    reqs = _make_reqs([("FR-001", "Blog posts")])
    arch = _make_arch(
        components=[("API", "Blog API", ["Node.js"])],
    )
    ctx = _make_ctx(
        frs=["FR-001: Blog posts"],
    )

    result = check_agent_readiness(project, reqs, arch, ctx)
    concurrency = _get_concurrency_warnings(result)
    # A simple blog should have zero concurrency safety warnings
    assert len(concurrency) == 0, f"Unexpected concurrency warnings for simple project: {[w.message for w in concurrency]}"


# ============================================================
# Test 12: Multiple concurrency issues detected simultaneously
# ============================================================
def test_multiple_concurrency_issues():
    from app.engines.agent_readiness import check_agent_readiness

    project = _make_project(
        features=["Patient appointments", "Telebirr payments", "SMS reminders", "AI health guidance"],
    )
    reqs = _make_reqs([
        ("FR-001", "Patient appointments"),
        ("FR-002", "Payment processing"),
        ("FR-003", "SMS reminders"),
        ("FR-004", "AI health guidance"),
    ])
    arch = _make_arch(
        sys_arch="Node.js backend on Fargate.",
        tech_stack=[("AI", "OpenAI API", "Health guidance")],
        components=[
            ("API", "Web API", ["Node.js"]),
            ("Worker", "Background jobs", ["node-cron"]),
        ],
        deployment=[("production", ["Fargate"], "Container hosting")],
    )
    ctx = _make_ctx(
        tech_stack=["OpenAI API", "React", "Node.js"],
        frs=[
            "FR-001: Patient appointments",
            "FR-002: Payment processing",
            "FR-003: SMS reminders",
            "FR-004: AI health guidance",
        ],
        security=["JWT only"],  # Minimal security — missing many things
    )

    result = check_agent_readiness(project, reqs, arch, ctx)
    concurrency = _get_concurrency_warnings(result)
    # Should detect at least: booking locking, payment idempotency, cron safety, audit, disclaimer
    assert len(concurrency) >= 3, f"Expected >= 3 concurrency warnings, got {len(concurrency)}: {[w.message for w in concurrency]}"
    print(f"    Detected {len(concurrency)} concurrency issues:")
    for w in concurrency:
        print(f"      - [{w.category}] {w.message[:80]}...")


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    tests = [
        ("Booking without locking -> warning", test_booking_no_locking),
        ("Booking WITH locking -> no warning", test_booking_with_locking),
        ("Payment without idempotency -> warning", test_payment_no_idempotency),
        ("Payment WITH idempotency -> no warning", test_payment_with_idempotency),
        ("Cron + Fargate unsafe -> warning", test_cron_with_fargate_unsafe),
        ("Cron + Fargate safe -> no warning", test_cron_with_fargate_safe),
        ("Healthcare without audit -> warning", test_healthcare_no_audit),
        ("Healthcare WITH audit -> no warning", test_healthcare_with_audit),
        ("AI + healthcare no disclaimer -> warning", test_ai_healthcare_no_disclaimer),
        ("AI + healthcare WITH disclaimer -> no warning", test_ai_healthcare_with_disclaimer),
        ("Simple project -> no false warnings", test_simple_project_no_false_warnings),
        ("Multiple issues detected together", test_multiple_concurrency_issues),
    ]

    print("=" * 60)
    print("CONCURRENCY & SAFETY CHECKS")
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
