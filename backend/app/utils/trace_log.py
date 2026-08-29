"""
TRACE LOG: Captures every continue_project() call to a file.
Inspect this file after reproducing the bug in the browser.
"""

import json
import datetime

_LOG_PATH = "trace_log.jsonl"


def trace_continue(
    step: str,
    project_data: dict,
    answers: dict,
    conversation_history: list,
    answer_list: list,
    force_applied: list,
    project_after_force: dict,
    missing_fields: list,
    answered_fields: list,
    remaining_missing: list,
    raw_questions: list,
    deduplicated: list,
):
    """Append one trace entry to trace_log.jsonl"""
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "step": step,
        "answers_received": answers,
        "answer_list": answer_list,
        "conversation_history_count": len(conversation_history),
        "conversation_history_fields": [h.get("field") for h in conversation_history],
        "force_applied": force_applied,
        "project_authentication": project_after_force.get("authentication"),
        "project_database": project_after_force.get("database"),
        "project_platform": project_after_force.get("platform"),
        "project_technologies": project_after_force.get("technologies"),
        "project_target_users": project_after_force.get("target_users"),
        "missing_fields": missing_fields,
        "answered_fields": answered_fields,
        "remaining_missing": remaining_missing,
        "raw_question_fields": [q.get("field") for q in raw_questions],
        "deduplicated_fields": [q.get("field") for q in deduplicated],
    }
    with open(_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")


def clear_log():
    """Clear the trace log."""
    with open(_LOG_PATH, "w", encoding="utf-8") as f:
        f.write("")
