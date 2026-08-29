"""
TEST: Check if the SAME question appears as question[0] in consecutive batches.

This simulates exactly what the browser does:
  1. Start → see question[0] → answer it
  2. Get new batch → see question[0] → is it the SAME field?
  3. If yes → BUG CONFIRMED
"""

import asyncio
import json
import sys
import io
import httpx

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = "http://127.0.0.1:8000"


def log(msg):
    print(f"\n{'='*70}")
    print(f"  {msg}")
    print(f"{'='*70}")


async def main():
    async with httpx.AsyncClient(timeout=120.0) as client:

        # Start fresh
        resp = await client.post(f"{BASE}/projects/start", json={
            "idea": (
                "I want to build SkillBridge Ethiopia, a job platform "
                "that connects Ethiopian students and graduates with "
                "employers. Students create profiles, search for jobs, "
                "and apply. Employers post jobs and review applicants. "
                "The platform should be accessible via web and mobile."
            )
        })

        if resp.status_code != 200:
            print(f"ERROR: {resp.status_code} {resp.text}")
            return

        start = resp.json()
        current_project = start["project"]
        current_questions = start["questions"]
        current_history = []

        log("START")
        print(f"  Questions: {[q['field'] for q in current_questions]}")
        print(f"  Question[0] = '{current_questions[0]['field']}'")

        prev_q0_field = None

        for round_num in range(1, 12):
            if not current_questions:
                log(f"Round {round_num}: No questions — COMPLETE")
                break

            q0 = current_questions[0]

            # CHECK: Is question[0] the same field as last round's question[0]?
            if prev_q0_field is not None and q0["field"] == prev_q0_field:
                log(f"Round {round_num}: *** BUG CONFIRMED ***")
                print(f"  Previous question[0] field: '{prev_q0_field}'")
                print(f"  Current question[0] field:  '{q0['field']}'")
                print(f"  The user would see the SAME question twice in a row!")
                print(f"\n  Full state:")
                print(f"  History: {[h['field'] for h in current_history]}")
                print(f"  Missing: {start.get('missing_fields', []) if round_num == 1 else 'see response'}")
                break

            log(f"Round {round_num}: Answering question[0] = '{q0['field']}'")

            current_history = current_history + [
                {
                    "field": q0["field"],
                    "question": q0["question"],
                    "answer": f"Test answer for {q0['field']}"
                }
            ]

            resp = await client.post(f"{BASE}/projects/continue", json={
                "project": current_project,
                "answers": {q0["field"]: f"Test answer for {q0['field']}"},
                "conversation_history": current_history,
            })

            if resp.status_code != 200:
                log(f"Round {round_num}: ERROR {resp.status_code}")
                print(resp.text[:200])
                break

            result = resp.json()

            if result["complete"]:
                log(f"Round {round_num}: COMPLETE!")
                break

            current_project = result["project"]
            current_questions = result["questions"]

            print(f"  New questions: {[q['field'] for q in current_questions]}")
            print(f"  Missing: {result['missing_fields']}")
            print(f"  History: {[h['field'] for h in result.get('conversation_history', [])]}")

            prev_q0_field = q0["field"]

        log("TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())
