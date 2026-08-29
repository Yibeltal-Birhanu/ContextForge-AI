"""
EduFlow LMS — End-to-End Pipeline Test

A completely new project with a DIFFERENT stack from HealthLink and SkillSwap:
- C# / ASP.NET Core / SQL Server / Entity Framework Core
- React / TypeScript
- Docker

This tests that ContextForge works for arbitrary projects.
"""
import asyncio
import json
import sys
import httpx

API_URL = "http://127.0.0.1:8000"


async def test_eduflow_pipeline():
    """Run the complete EduFlow pipeline through the API."""
    print("=" * 60)
    print("EDUFLOW LMS — END-TO-END PIPELINE TEST")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=600.0) as client:
        # Step 1: Start the project
        print("\n--- Step 1: Start Project ---")
        response = await client.post(
            f"{API_URL}/projects/start",
            json={
                "idea": (
                    "EduFlow is a learning management system for Ethiopian universities. "
                    "Students can enroll in courses, access course materials, submit assignments, "
                    "take quizzes, view grades, and receive notifications. "
                    "Instructors can create courses, upload materials, create quizzes, "
                    "grade assignments, and manage enrollments. "
                    "Administrators manage users, departments, and platform settings. "
                    "Use C#, ASP.NET Core, SQL Server, Entity Framework Core, React, TypeScript, and Docker."
                )
            },
        )
        assert response.status_code == 200, f"Start failed: {response.status_code}"
        result = response.json()
        project = result.get("project", {})
        history = result.get("conversation_history", [])

        print(f"  Initial name: {project.get('name')}")
        print(f"  Initial techs: {project.get('technologies')}")
        print(f"  Initial user_selected: {project.get('user_selected_technologies')}")

        # Step 2: Answer all discovery questions
        print("\n--- Step 2: Discovery ---")
        answers = {
            "name": "EduFlow LMS",
            "description": "Learning management system for Ethiopian universities.",
            "problem": "Ethiopian universities lack a unified digital platform for course management, assignments, and grading.",
            "target_users": "Students, Instructors, and Administrators",
            "core_features": "Course enrollment, course materials, assignment submission, quizzes, grades, notifications, instructor tools, admin management",
            "platform": "Web",
            "technologies": "C#, ASP.NET Core, SQL Server, Entity Framework Core, React, TypeScript, Docker",
            "database": "SQL Server",
            "authentication": "Email and password with JWT",
            "integrations": "Email notifications",
            "constraints": "Keep architecture simple for MVP. Must work on low-bandwidth connections.",
            "deployment": "Docker containers on cloud VPS",
        }

        max_rounds = 15
        round_num = 0

        while not result.get("complete") and round_num < max_rounds:
            round_num += 1
            questions = result.get("questions", [])
            missing = result.get("missing_fields", [])

            if not questions and not missing:
                break

            if questions:
                field = questions[0].get("field", "")
            elif missing:
                field = missing[0]
            else:
                break

            answer = answers.get(field, f"EduFlow answer for {field}")

            history.append({
                "field": field,
                "question": f"Question about {field}",
                "answer": answer,
            })

            response = await client.post(
                f"{API_URL}/projects/continue",
                json={
                    "project": project,
                    "answers": {field: answer},
                    "conversation_history": history,
                },
            )

            if response.status_code != 200:
                print(f"  ERROR at round {round_num}, field '{field}': {response.status_code}")
                print(f"  Response: {response.text[:300]}")
                break

            result = response.json()
            project = result.get("project", project)
            print(f"  Round {round_num}: {field} -> Complete: {result.get('complete')}")

        print(f"\n  Pipeline completed: {result.get('complete')}")
        print(f"  Final stage: {result.get('stage')}")

        # Step 3: Verify results
        print("\n--- Step 3: Verify Results ---")

        # Project name
        project_name = project.get("name", "")
        print(f"  Name: {project_name}")
        assert "eduflow" in project_name.lower() or "edu" in project_name.lower(), (
            f"Project name doesn't match EduFlow: {project_name}"
        )

        # Technology preservation
        user_techs = {t.get("name", "").lower() for t in project.get("user_selected_technologies", [])}
        project_techs = {t.lower() for t in project.get("technologies", [])}
        all_techs = user_techs | project_techs
        print(f"  User-selected techs: {user_techs}")
        print(f"  Project techs: {project_techs}")

        # Check required technologies
        required = {"c#", "asp.net core", "sql server", "entity framework core", "react", "typescript", "docker"}
        for rt in required:
            found = any(rt in t for t in all_techs)
            print(f"    {rt}: {'FOUND' if found else 'MISSING'}")

        # No HealthLink leakage
        healthlink = {"telebirr", "openai api", "amazon bedrock", "google maps", "africa's talking"}
        leaked = all_techs & healthlink
        print(f"  HealthLink leakage: {'NONE' if not leaked else leaked}")
        assert len(leaked) == 0, f"HealthLink technologies leaked: {leaked}"

        # No SkillSwap leakage
        skillswap = {"skill exchange", "skillswap"}
        project_text = json.dumps(project).lower()
        for term in skillswap:
            assert term not in project_text, f"SkillSwap term '{term}' found in EduFlow project"

        # No healthcare terms
        healthcare = ["patient", "doctor", "clinic", "appointment", "medical"]
        found_hc = [t for t in healthcare if t in project_text]
        print(f"  Healthcare terms: {'NONE' if found_hc else found_hc}")
        assert len(found_hc) == 0, f"Healthcare terms found: {found_hc}"

        # Quality scores
        quality = result.get("quality", {})
        if quality:
            print(f"\n  Quality overall: {quality.get('overall_score')}")
            print(f"  Validation: {quality.get('validation_score')}")
            print(f"  Readiness: {quality.get('readiness_score')}")
            print(f"  Ready for agent: {quality.get('ready_for_agent')}")

        # Download markdown
        download_md = result.get("download_markdown")
        if download_md:
            md_resp = await client.get(f"{API_URL}{download_md}")
            if md_resp.status_code == 200:
                md = md_resp.text
                print(f"\n  Markdown length: {len(md)} chars")
                print(f"  Contains 'EduFlow': {'EduFlow' in md}")
                print(f"  Contains 'C#': {'C#' in md or 'CSharp' in md}")
                print(f"  Contains 'ASP.NET': {'ASP.NET' in md}")
                print(f"  Contains 'SQL Server': {'SQL Server' in md}")
                print(f"  Contains 'React': {'React' in md}")
                print(f"  Contains 'Django': {'Django' in md}")
                print(f"  Contains 'FastAPI': {'FastAPI' in md}")
                print(f"  Contains 'Telebirr': {'Telebirr' in md}")
                print(f"  Contains 'patient': {'patient' in md.lower()}")

                # Verify NO leakage
                assert "django" not in md.lower(), "Django found in EduFlow context (SkillSwap leakage)"
                assert "fastapi" not in md.lower(), "FastAPI found in EduFlow context"
                assert "telebirr" not in md.lower(), "Telebirr found in EduFlow context (HealthLink leakage)"
                assert "patient" not in md.lower(), "patient found in EduFlow context (HealthLink leakage)"

                # Save for inspection
                with open("test_eduflow_context.md", "w", encoding="utf-8") as f:
                    f.write(md)
                print("  Saved to test_eduflow_context.md")
            else:
                print(f"  Markdown download failed: {md_resp.status_code}")

        print("\n" + "=" * 60)
        print("EDUFLOW E2E TEST: PASS")
        print("=" * 60)
        return True


async def main():
    try:
        return await test_eduflow_pipeline()
    except Exception as e:
        print(f"\n{'=' * 60}")
        print(f"EDUFLOW E2E TEST: FAIL")
        print(f"Error: {e}")
        print(f"{'=' * 60}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
