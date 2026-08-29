"""Debug test to inspect SkillSwap pipeline output."""
import asyncio
import json
import httpx

API_URL = "http://127.0.0.1:8000"


async def main():
    async with httpx.AsyncClient(timeout=600.0) as client:
        # Start
        response = await client.post(
            f"{API_URL}/projects/start",
            json={
                "idea": (
                    "SkillSwap Ethiopia is a peer-to-peer skill exchange platform. "
                    "Users create profiles showing skills they can teach and skills "
                    "they want to learn. They can search for compatible users, send "
                    "exchange requests, schedule sessions, receive notifications, "
                    "and rate each other after completed sessions."
                )
            },
        )
        result = response.json()
        project = result.get("project", {})
        history = result.get("conversation_history", [])

        print("=== INITIAL PROJECT STATE ===")
        print(f"Name: {project.get('name')}")
        print(f"Technologies: {project.get('technologies')}")
        print(f"User-selected: {project.get('user_selected_technologies')}")
        print(f"Database: {project.get('database')}")
        print(f"Platform: {project.get('platform')}")

        # Answer all questions
        answers = {
            "platform": "Web",
            "problem": "Many people in Ethiopia want to learn new skills but cannot afford traditional courses. SkillSwap connects learners with teachers for mutual skill exchange.",
            "technologies": "Python, Django, Django REST Framework, PostgreSQL, Redis, React, TypeScript, Docker",
            "database": "PostgreSQL",
            "authentication": "Email and password with secure hashing",
            "integrations": "Redis for caching and background tasks",
            "deployment": "Docker containers on cloud VPS using Docker Compose",
            "constraints": "Keep architecture simple for MVP. Do not introduce Kubernetes or microservices.",
        }

        while not result.get("complete"):
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

            answer = answers.get(field, f"Answer for {field}")

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
                print(f"\n=== ERROR at field '{field}' ===")
                print(response.text[:500])
                break

            result = response.json()
            project = result.get("project", project)

            print(f"\nAnswered '{field}': {answer[:60]}...")
            print(f"  Complete: {result.get('complete')}")
            print(f"  Stage: {result.get('stage')}")
            print(f"  Techs: {project.get('technologies', [])[:5]}")
            print(f"  User-selected: {project.get('user_selected_technologies', [])[:5]}")

        # Final inspection
        print("\n=== FINAL PROJECT STATE ===")
        print(json.dumps(project, indent=2, default=str)[:3000])

        if result.get("quality"):
            print("\n=== QUALITY ===")
            print(json.dumps(result["quality"], indent=2, default=str)[:2000])

        # Download markdown
        if result.get("download_markdown"):
            md_resp = await client.get(f"{API_URL}{result['download_markdown']}")
            if md_resp.status_code == 200:
                md = md_resp.text
                print(f"\n=== MARKDOWN ({len(md)} chars) ===")
                print(md[:3000])
                with open("test_skillswap_context.md", "w") as f:
                    f.write(md)
                print("\nSaved to test_skillswap_context.md")


asyncio.run(main())
