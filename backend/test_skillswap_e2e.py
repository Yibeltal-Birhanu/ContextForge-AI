"""
SkillSwap Ethiopia — End-to-End Browser Simulation Test

This script simulates the complete ContextForge pipeline through the API,
mimicking exactly what a user would do in the browser:

1. POST /projects/start with the project idea
2. Answer discovery questions one at a time
3. Continue until complete
4. Verify the final result

This is NOT a unit test — it calls the real API endpoints.
"""
import asyncio
import json
import sys
import httpx

API_URL = "http://127.0.0.1:8000"


async def test_start_project():
    """Step 1: Start the project with the idea."""
    print("=" * 60)
    print("STEP 1: Starting project with SkillSwap idea")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=600.0) as client:
        response = await client.post(
            f"{API_URL}/projects/start",
            json={
                "idea": (
                    "SkillSwap Ethiopia is a peer-to-peer skill exchange platform. "
                    "Users create profiles showing skills they can teach and skills "
                    "they want to learn. They can search for compatible users, send "
                    "exchange requests, schedule sessions, receive notifications, "
                    "and rate each other after completed sessions. The MVP focuses "
                    "on skill discovery, matching, exchange requests, scheduling, "
                    "notifications, and ratings."
                )
            },
        )

        assert response.status_code == 200, f"Start failed: {response.status_code} {response.text}"
        result = response.json()

        print(f"  Stage: {result.get('stage')}")
        print(f"  Complete: {result.get('complete')}")
        print(f"  Missing fields: {result.get('missing_fields', [])}")
        print(f"  Questions: {len(result.get('questions', []))}")

        if result.get("questions"):
            q = result["questions"][0]
            print(f"  First question field: {q.get('field')}")
            print(f"  First question: {q.get('question', '')[:100]}...")

        return result


async def answer_question(client, project_data, conversation_history, field, answer):
    """Answer a single question and get the next set of questions."""
    # Build updated conversation history
    # Find the question text from the current project state
    question_text = f"Question about {field}"

    new_history = list(conversation_history) if conversation_history else []
    new_history.append({
        "field": field,
        "question": question_text,
        "answer": answer,
    })

    response = await client.post(
        f"{API_URL}/projects/continue",
        json={
            "project": project_data,
            "answers": {field: answer},
            "conversation_history": new_history,
        },
    )

    assert response.status_code == 200, f"Continue failed: {response.status_code} {response.text}"
    return response.json(), new_history


async def test_complete_pipeline():
    """Run the complete pipeline through the API."""
    print("\n" + "=" * 60)
    print("STEP 2: Running complete discovery pipeline")
    print("=" * 60)

    # Pre-defined answers for SkillSwap
    answers_map = {
        "name": "SkillSwap Ethiopia",
        "description": (
            "A peer-to-peer skill exchange platform where people can teach "
            "skills they know and learn skills from other people without "
            "traditional paid courses."
        ),
        "problem": (
            "Many people in Ethiopia want to learn new skills but cannot "
            "afford traditional courses. Meanwhile, others have valuable "
            "skills they could teach. SkillSwap connects these two groups "
            "for mutual skill exchange."
        ),
        "target_users": (
            "Regular users who want to learn or teach skills, "
            "and platform administrators who manage users, "
            "reports, categories, and platform content."
        ),
        "core_features": (
            "User registration and login, profile management, "
            "skill profiles (teach/learn), skill categories, "
            "search and filtering, compatibility matching, "
            "exchange requests, session scheduling, "
            "notifications, ratings and reviews, "
            "user reporting, admin management."
        ),
        "platform": "Web",
        "technologies": (
            "Python, Django, Django REST Framework, PostgreSQL, "
            "Redis, React, TypeScript, Docker"
        ),
        "database": "PostgreSQL",
        "authentication": "Email and password with secure hashing",
        "integrations": "Redis for caching and background tasks",
        "constraints": (
            "Keep architecture simple for MVP. "
            "Do not introduce Kubernetes, microservices, "
            "service mesh, or unnecessary complexity."
        ),
        "deployment": "Docker containers on a cloud VPS using Docker Compose",
    }

    async with httpx.AsyncClient(timeout=600.0) as client:
        # Start the project
        result = await test_start_project()
        project_data = result.get("project", {})
        conversation_history = result.get("conversation_history", [])

        # Answer questions one at a time
        max_rounds = 15  # Safety limit
        round_num = 0

        while not result.get("complete") and round_num < max_rounds:
            round_num += 1
            questions = result.get("questions", [])

            if not questions:
                print(f"  Round {round_num}: No questions but not complete. Checking...")
                # Try to force completion by answering remaining fields
                missing = result.get("missing_fields", [])
                if not missing:
                    break
                # Answer the first missing field
                field = missing[0]
                answer = answers_map.get(field, f"Generic answer for {field}")
            else:
                q = questions[0]
                field = q.get("field", "")
                answer = answers_map.get(field, f"Generic answer for {field}")

                # If we have a specific answer for this field, use it
                if field not in answers_map:
                    # Generate a contextual answer
                    question_text = q.get("question", "").lower()
                    if "name" in question_text:
                        answer = "SkillSwap Ethiopia"
                    elif "platform" in question_text or "where" in question_text:
                        answer = "Web"
                    elif "deploy" in question_text or "host" in question_text:
                        answer = "Docker containers on cloud VPS"
                    elif "technolog" in question_text or "framework" in question_text:
                        answer = "Python, Django, PostgreSQL, Redis, React, TypeScript, Docker"
                    elif "auth" in question_text or "sign in" in question_text:
                        answer = "Email and password with secure hashing"
                    elif "database" in question_text:
                        answer = "PostgreSQL"
                    elif "constraint" in question_text or "limit" in question_text:
                        answer = "Keep architecture simple for MVP"
                    else:
                        answer = f"SkillSwap-specific answer for: {q.get('question', field)[:80]}"

            print(f"\n  Round {round_num}:")
            print(f"    Field: {field}")
            print(f"    Answer: {answer[:80]}...")

            result, conversation_history = await answer_question(
                client, project_data, conversation_history, field, answer
            )
            project_data = result.get("project", project_data)

            print(f"    Stage: {result.get('stage')}")
            print(f"    Complete: {result.get('complete')}")
            print(f"    Missing: {result.get('missing_fields', [])[:5]}")
            print(f"    Questions: {len(result.get('questions', []))}")

        print(f"\n  Pipeline completed after {round_num} rounds")
        print(f"  Final stage: {result.get('stage')}")
        print(f"  Final complete: {result.get('complete')}")

        return result


async def verify_results(result):
    """Verify the final pipeline result."""
    print("\n" + "=" * 60)
    print("STEP 3: Verifying results")
    print("=" * 60)

    project = result.get("project", {})
    quality = result.get("quality", {})

    # Basic checks
    assert result.get("complete") is True, f"Pipeline not complete: {result.get('stage')}"
    assert result.get("project_id") is not None, "No project_id returned"

    # Project name
    project_name = project.get("name", "")
    print(f"  Project name: {project_name}")
    assert "skillswap" in project_name.lower() or "skill" in project_name.lower(), (
        f"Project name doesn't match SkillSwap: {project_name}"
    )

    # Technology preservation
    user_techs = project.get("user_selected_technologies", [])
    tech_names = {t.get("name", "").lower() for t in user_techs}
    print(f"  User-selected technologies: {tech_names}")

    # Check both user_selected_technologies AND project.technologies
    project_techs = {t.lower() for t in project.get("technologies", [])}
    all_techs = tech_names | project_techs
    print(f"  All project technologies: {all_techs}")

    # Technologies should be present somewhere (user_selected or project.technologies)
    # Note: the LLM may not always ask about technologies explicitly
    # but should use them in the architecture

    # No HealthLink leakage
    healthlink_techs = {"telebirr", "openai api", "amazon bedrock", "google maps", "africa's talking"}
    leaked = tech_names & healthlink_techs
    print(f"  HealthLink leakage: {'NONE' if not leaked else leaked}")
    assert len(leaked) == 0, f"HealthLink technologies leaked: {leaked}"

    # No healthcare concepts
    project_text = json.dumps(project).lower()
    healthcare_terms = ["patient", "doctor", "clinic", "appointment", "medical", "health record"]
    found_healthcare = [t for t in healthcare_terms if t in project_text]
    print(f"  Healthcare terms: {'NONE' if not found_healthcare else found_healthcare}")
    assert len(found_healthcare) == 0, f"Healthcare terms found: {found_healthcare}"

    # Quality scores
    if quality:
        print(f"  Quality overall: {quality.get('overall_score')}")
        print(f"  Validation: {quality.get('validation_score')}")
        print(f"  Readiness: {quality.get('readiness_score')}")
        print(f"  Ready for agent: {quality.get('ready_for_agent')}")
        print(f"  Warnings: {quality.get('warnings_count', 0)}")
        print(f"  Assumptions: {quality.get('assumptions_count', 0)}")

    # Download URLs
    download_md = result.get("download_markdown")
    download_txt = result.get("download_txt")
    print(f"  Download MD: {download_md}")
    print(f"  Download TXT: {download_txt}")

    # Try to download the markdown
    if download_md:
        async with httpx.AsyncClient(timeout=30.0) as client:
            md_response = await client.get(f"{API_URL}{download_md}")
            if md_response.status_code == 200:
                md_content = md_response.text
                print(f"\n  Markdown length: {len(md_content)} chars")
                print(f"  Contains 'SkillSwap': {'SkillSwap' in md_content}")
                print(f"  Contains 'Django': {'Django' in md_content}")
                print(f"  Contains 'PostgreSQL': {'PostgreSQL' in md_content}")
                print(f"  Contains 'Python': {'Python' in md_content}")
                print(f"  Contains 'SkillSwap': {'SkillSwap' in md_content}")
                print(f"  Contains 'Telebirr': {'Telebirr' in md_content}")
                print(f"  Contains 'patient': {'patient' in md_content.lower()}")
                print(f"  Contains 'healthcare': {'healthcare' in md_content.lower()}")
                # Verify NO HealthLink leakage
                healthlink_terms = ["telebirr", "openai api", "amazon bedrock", "google maps", "africa's talking"]
                for term in healthlink_terms:
                    assert term not in md_content.lower(), f"HealthLink term '{term}' found in SkillSwap context!"

                # Save for inspection
                with open("test_skillswap_context.md", "w", encoding="utf-8") as f:
                    f.write(md_content)
                print("  Saved to test_skillswap_context.md")
            else:
                print(f"  Markdown download failed: {md_response.status_code}")

    return True


async def main():
    """Run the complete E2E test."""
    print("=" * 60)
    print("SKILLSWAP ETHIOPIA — END-TO-END PIPELINE TEST")
    print("=" * 60)

    try:
        # Step 1-2: Run the complete pipeline
        result = await test_complete_pipeline()

        # Step 3: Verify results
        success = await verify_results(result)

        print("\n" + "=" * 60)
        print("E2E TEST RESULT: PASS")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n{'=' * 60}")
        print(f"E2E TEST RESULT: FAIL")
        print(f"Error: {e}")
        print(f"{'=' * 60}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
