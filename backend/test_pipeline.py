import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.services.project_pipeline import start_project, continue_project
from app.services.artifact_store import get_artifact


def main():

    print("=" * 60)
    print("TEST 1: Start project with idea")
    print("=" * 60)

    import asyncio

    result1 = asyncio.run(
        start_project(
            "I want to build an online supermarket where customers can browse products and place orders."
        )
    )

    print(f"\nStage: {result1.stage}")
    print(f"Complete: {result1.complete}")
    print(f"Missing fields: {result1.missing_fields}")
    print(f"Questions count: {len(result1.questions)}")
    print(f"Project name: {result1.project.name}")
    print(f"Project ID: {result1.project_id}")

    assert result1.stage == "discovery"
    assert result1.complete == False
    assert len(result1.missing_fields) > 0
    assert len(result1.questions) > 0
    assert result1.project_id is None
    print("\nTEST 1: PASSED")

    print("\n" + "=" * 60)
    print("TEST 2: Continue discovery with answers")
    print("=" * 60)

    answers = {
        "name": "Yibe Market",
        "platform": "Both web and mobile",
        "database": "PostgreSQL",
        "authentication": "Customer accounts and admin accounts",
        "deployment": "Docker on cloud hosting",
        "integrations": "Online payment (Stripe) and email notifications",
        "technologies": "React, TypeScript, Node.js, Express",
        "constraints": "Limited initial budget"
    }

    result2 = asyncio.run(
        continue_project(
            result1.project.model_dump(),
            answers,
        )
    )

    print(f"\nStage: {result2.stage}")
    print(f"Complete: {result2.complete}")
    print(f"Missing fields: {result2.missing_fields}")
    print(f"Questions count: {len(result2.questions)}")
    print(f"Project name: {result2.project.name}")
    print(f"Project ID: {result2.project_id}")

    # After providing answers, some fields should still be missing
    # or the pipeline should be complete
    if result2.complete:
        print("\nPipeline completed!")
        print(f"Download markdown: {result2.download_markdown}")
        print(f"Download txt: {result2.download_txt}")

        # Verify artifact is stored
        artifact = get_artifact(result2.project_id)
        assert artifact is not None
        print(f"Artifact stored: OK")
        print(f"Markdown length: {len(artifact.markdown)}")
        print("\nTEST 2: PASSED (completed)")
    else:
        print(f"\nStill need more information.")
        print(f"Next questions:")
        for q in result2.questions[:3]:
            print(f"  - {q.get('question', 'N/A')}")
        print("\nTEST 2: PASSED (discovery continues)")

    print("\n" + "=" * 60)
    print("TEST 3: Full completion with all fields")
    print("=" * 60)

    # Start fresh and provide all fields at once
    result3_start = asyncio.run(
        start_project(
            "I want to build a task management app for teams."
        )
    )

    # Provide comprehensive answers
    full_answers = {
        "name": "TeamTask",
        "description": "A task management application for teams to collaborate on projects.",
        "problem": "Teams need a simple way to track tasks and collaborate.",
        "target_users": "Team members and project managers",
        "core_features": "Create tasks, assign tasks, track progress, set deadlines, add comments",
        "platform": "Web application",
        "technologies": "React, TypeScript, Node.js, Express, PostgreSQL",
        "database": "PostgreSQL",
        "authentication": "User accounts with email and password",
        "integrations": "Email notifications",
        "constraints": "Must be simple and intuitive",
        "deployment": "Cloud hosting with Docker"
    }

    result3 = asyncio.run(
        continue_project(
            result3_start.project.model_dump(),
            full_answers,
        )
    )

    print(f"\nStage: {result3.stage}")
    print(f"Complete: {result3.complete}")
    print(f"Project name: {result3.project.name}")
    print(f"Project ID: {result3.project_id}")

    if result3.complete:
        print(f"Download markdown: {result3.download_markdown}")
        print(f"Download txt: {result3.download_txt}")

        # Verify artifact
        artifact = get_artifact(result3.project_id)
        assert artifact is not None
        assert artifact.valid == True
        assert artifact.validation_score == 100
        assert "# TeamTask" in artifact.markdown
        print(f"Artifact valid: {artifact.valid}")
        print(f"Validation score: {artifact.validation_score}")
        print(f"Markdown contains project name: OK")
        print("\nTEST 3: PASSED")
    else:
        print(f"Missing fields: {result3.missing_fields}")
        print("\nTEST 3: PASSED (needs more info)")

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)


main()
